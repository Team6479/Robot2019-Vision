""""Vendoring script, python 3.5 needed"""
# Taken from pipenv
# see https://github.com/pypa/pipenv/blob/master/tasks/vendoring/__init__.py

import os
import shutil
import tarfile
import zipfile

from pathlib import Path
from tempfile import NamedTemporaryFile

import invoke
import requests


TASK_NAME = 'update'

# from time to time, remove the no longer needed ones
HARDCODED_LICENSE_URLS = {
}

FILE_WHITE_LIST = (
    'Makefile',
    'vendor.txt',
    'patched.txt',
    '__init__.py',
    'README.rst',
    'README.md',
)


def mkdir_p(newdir):
    """works the way a good mkdir should :)
        - already exists, silently complete
        - regular file in the way, raise an exception
        - parent directory(ies) does not exist, make them as well
        From: http://code.activestate.com/recipes/82465-a-friendly-mkdir/
    """
    if os.path.isdir(newdir):
        pass
    elif os.path.isfile(newdir):
        raise OSError(
            "a file with the same name as the desired dir, '{0}', already exists.".format(
                newdir
            )
        )

    else:
        head, tail = os.path.split(newdir)
        if head and not os.path.isdir(head):
            mkdir_p(head)
        if tail:
            os.mkdir(newdir)


def drop_dir(path):
    if path.exists() and path.is_dir():
        shutil.rmtree(str(path), ignore_errors=True)


def remove_all(paths):
    for path in paths:
        if path.is_dir():
            drop_dir(path)
        else:
            path.unlink()


def log(msg):
    print('[vendoring.%s] %s' % (TASK_NAME, msg))


def _get_git_root(ctx):
    return Path(ctx.run('git rev-parse --show-toplevel', hide=True).stdout.strip())


def _get_vendor_dir(ctx):
    return _get_git_root(ctx) / 'frc2019_vision' / 'vendor'


def _get_patched_dir(ctx):
    return _get_git_root(ctx) / 'frc2019_vision' / 'patched'


def clean_vendor(ctx, vendor_dir):
    # Old _vendor cleanup
    remove_all(vendor_dir.glob('*.pyc'))
    log('Cleaning %s' % vendor_dir)
    for item in vendor_dir.iterdir():
        if item.is_dir():
            shutil.rmtree(str(item))
        elif item.name not in FILE_WHITE_LIST:
            item.unlink()
        else:
            log('Skipping %s' % item)


def detect_vendored_libs(vendor_dir):
    retval = []
    for item in vendor_dir.iterdir():
        if item.is_dir():
            retval.append(item.name)
        elif "LICENSE" in item.name or "COPYING" in item.name:
            continue
        elif item.name.endswith(".pyi"):
            continue
        elif item.name not in FILE_WHITE_LIST:
            retval.append(item.name[:-3])
    return retval


def apply_patch(ctx, patch_file_path):
    log('Applying patch %s' % patch_file_path.name)
    ctx.run('git apply --ignore-whitespace --verbose %s' % patch_file_path)


def write_backport_imports(ctx, vendor_dir):
    backport_dir = vendor_dir / 'backports'
    if not backport_dir.exists():
        return
    backport_init = backport_dir / '__init__.py'
    backport_libs = detect_vendored_libs(backport_dir)
    init_py_lines = backport_init.read_text().splitlines()
    for lib in backport_libs:
        lib_line = 'from . import {0}'.format(lib)
        if lib_line not in init_py_lines:
            log('Adding backport %s to __init__.py exports' % lib)
            init_py_lines.append(lib_line)
    backport_init.write_text('\n'.join(init_py_lines) + '\n')


def _ensure_package_in_requirements(ctx, requirements_file, package):
    requirement = None
    log('using requirements file: %s' % requirements_file)
    req_file_lines = [l for l in requirements_file.read_text().splitlines()]
    if package:
        match = [r for r in req_file_lines if r.strip().lower().startswith(package)]
        matched_req = None
        if match:
            for m in match:
                specifiers = [m.index(s) for s in ['>', '<', '=', '~'] if s in m]
                if m.lower() == package or (specifiers and m[:min(specifiers)].lower() == package):
                    matched_req = "{0}".format(m)
                    requirement = matched_req
                    log("Matched req: %r" % matched_req)
        if not matched_req:
            req_file_lines.append("{0}".format(package))
            log("Writing requirements file: %s" % requirements_file)
            requirements_file.write_text('\n'.join(req_file_lines))
            requirement = "{0}".format(package)
    return requirement


def install(ctx, vendor_dir, package=None):
    requirements_file = vendor_dir / "{0}.txt".format(vendor_dir.name)
    requirement = "-r {0}".format(requirements_file.as_posix())
    log('Using requirements file: %s' % requirement)
    if package:
        requirement = _ensure_package_in_requirements(ctx, requirements_file, package)
    # We use --no-deps because we want to ensure that all of our dependencies
    # are added to vendor.txt, this includes all dependencies recursively up
    # the chain.
    ctx.run(
        'pip install -t {0} --no-compile --no-deps --upgrade {1}'.format(
            vendor_dir.as_posix(),
            requirement,
        )
    )


def post_install_cleanup(ctx, vendor_dir):
    remove_all(vendor_dir.glob('*.dist-info'))
    remove_all(vendor_dir.glob('*.egg-info'))

    # Cleanup setuptools unneeded parts
    drop_dir(vendor_dir / 'bin')
    drop_dir(vendor_dir / 'tests')
    remove_all(vendor_dir.glob('toml.py'))


def vendor(ctx, vendor_dir, package=None):
    log('Reinstalling vendored libraries')
    is_patched = vendor_dir.name == 'patched'
    install(ctx, vendor_dir, package=package)
    log('Running post-install cleanup...')
    post_install_cleanup(ctx, vendor_dir)
    # Detect the vendored packages/modules
    vendored_libs = detect_vendored_libs(_get_vendor_dir(ctx))
    log("Detected vendored libraries: %s" % ", ".join(vendored_libs))

    # Apply pre-patches
    log("Applying pre-patches...")
    patch_dir = Path(__file__).parent / 'patches' / vendor_dir.name
    if is_patched:
        for patch in patch_dir.glob('*.patch'):
            if not patch.name.startswith('_post'):
                apply_patch(ctx, patch)

    log("Removing scandir library files...")
    remove_all(vendor_dir.glob('*.so'))
    drop_dir(vendor_dir / 'setuptools')
    drop_dir(vendor_dir / 'pkg_resources' / '_vendor')
    drop_dir(vendor_dir / 'pkg_resources' / 'extern')
    drop_dir(vendor_dir / 'bin')

    write_backport_imports(ctx, vendor_dir)
    if not package:
        log('Applying post-patches...')
        patches = patch_dir.glob('*.patch' if not is_patched else '_post*.patch')
        for patch in patches:
            log(patch)
            apply_patch(ctx, patch)


@invoke.task
def packages_missing_licenses(ctx, vendor_dir=None, requirements_file='vendor.txt', package=None):
    if not vendor_dir:
        vendor_dir = _get_vendor_dir(ctx)
    requirements = vendor_dir.joinpath(requirements_file).read_text().splitlines()
    new_requirements = []
    LICENSES = ["LICENSE-MIT", "LICENSE", "LICENSE.txt", "LICENSE.APACHE", "LICENSE.BSD"]
    for i, req in enumerate(requirements):
        pkg = req.strip().split("=")[0]
        possible_pkgs = [pkg, pkg.replace('-', '_')]
        match_found = False
        for pkgpath in possible_pkgs:
            pkgpath = vendor_dir.joinpath(pkgpath)
            if pkgpath.exists() and pkgpath.is_dir():
                for licensepath in LICENSES:
                    licensepath = pkgpath.joinpath(licensepath)
                    if licensepath.exists():
                        match_found = True
                        # log("%s: Trying path %s... FOUND" % (pkg, licensepath))
                        break
            elif (pkgpath.exists() or pkgpath.parent.joinpath("{0}.py".format(pkgpath.stem)).exists()):
                for licensepath in LICENSES:
                    licensepath = pkgpath.parent.joinpath("{0}.{1}".format(pkgpath.stem, licensepath))
                    if licensepath.exists():
                        match_found = True
                        # log("%s: Trying path %s... FOUND" % (pkg, licensepath))
                        break
            if match_found:
                break
        if match_found:
            continue
        else:
            # log("%s: No license found in %s" % (pkg, pkgpath))
            new_requirements.append(req)
    return new_requirements


@invoke.task
def download_licenses(ctx, vendor_dir=None, requirements_file='vendor.txt', package=None, only=False, patched=False):
    log('Downloading licenses')
    if not vendor_dir:
        if patched:
            vendor_dir = _get_patched_dir(ctx)
            requirements_file = 'patched.txt'
        else:
            vendor_dir = _get_vendor_dir(ctx)
    requirements_file = vendor_dir / requirements_file
    requirements = packages_missing_licenses(ctx, vendor_dir, requirements_file, package=package)

    with NamedTemporaryFile(prefix="frc2019_vision", suffix="vendor-reqs", delete=False, mode="w") as fh:
        fh.write("\n".join(requirements))
        new_requirements_file = fh.name
    new_requirements_file = Path(new_requirements_file)
    log(requirements)
    requirement = "-r {0}".format(new_requirements_file.as_posix())
    if package:
        if not only:
            # for packages we want to add to the requirements file
            requirement = _ensure_package_in_requirements(ctx, requirements_file, package)
        else:
            # for packages we want to get the license for by themselves
            requirement = package
    tmp_dir = vendor_dir / '__tmp__'
    # TODO: Fix this whenever it gets sorted out (see https://github.com/pypa/pip/issues/5739)
    ctx.run('pip install flit')  # needed for the next step
    ctx.run(
        'pip download --no-binary :all: --only-binary requests_download --no-build-isolation --no-deps -d {0} {1}'.format(
            tmp_dir.as_posix(),
            requirement,
        )
    )
    for sdist in tmp_dir.iterdir():
        extract_license(vendor_dir, sdist)
    new_requirements_file.unlink()
    drop_dir(tmp_dir)


def extract_license(vendor_dir, sdist):
    if sdist.stem.endswith('.tar'):
        ext = sdist.suffix[1:]
        with tarfile.open(sdist, mode='r:{}'.format(ext)) as tar:
            found = find_and_extract_license(vendor_dir, tar, tar.getmembers())
    elif sdist.suffix == '.zip':
        with zipfile.ZipFile(sdist) as zip:
            found = find_and_extract_license(vendor_dir, zip, zip.infolist())
    else:
        raise NotImplementedError('new sdist type!')

    if not found:
        log('License not found in {}, will download'.format(sdist.name))
        license_fallback(vendor_dir, sdist.name)


def find_and_extract_license(vendor_dir, tar, members):
    found = False
    for member in members:
        try:
            name = member.name
        except AttributeError:  # zipfile
            name = member.filename
        if 'LICENSE' in name or 'COPYING' in name:
            if '/test' in name:
                # some testing licenses in hml5lib and distlib
                log('Ignoring {}'.format(name))
                continue
            found = True
            extract_license_member(vendor_dir, tar, member, name)
    return found


def license_fallback(vendor_dir, sdist_name):
    """Hardcoded license URLs. Check when updating if those are still needed"""
    libname = libname_from_dir(sdist_name)
    if libname not in HARDCODED_LICENSE_URLS:
        raise ValueError('No hardcoded URL for {} license'.format(libname))

    url = HARDCODED_LICENSE_URLS[libname]
    _, _, name = url.rpartition('/')
    dest = license_destination(vendor_dir, libname, name)
    r = requests.get(url, allow_redirects=True)
    log('Downloading {}'.format(url))
    r.raise_for_status()
    dest.write_bytes(r.content)


def libname_from_dir(dirname):
    """Reconstruct the library name without it's version"""
    parts = []
    for part in dirname.split('-'):
        if part[0].isdigit():
            break
        parts.append(part)
    return '-'.join(parts)


def license_destination(vendor_dir, libname, filename):
    """Given the (reconstructed) library name, find appropriate destination"""
    normal = vendor_dir / libname
    if normal.is_dir():
        return normal / filename
    lowercase = vendor_dir / libname.lower().replace('-', '_')
    if lowercase.is_dir():
        return lowercase / filename
    # fallback to libname.LICENSE (used for nondirs)
    return vendor_dir / '{}.{}'.format(libname, filename)


def extract_license_member(vendor_dir, tar, member, name):
    mpath = Path(name)  # relative path inside the sdist
    dirname = list(mpath.parents)[-2].name  # -1 is .
    libname = libname_from_dir(dirname)
    dest = license_destination(vendor_dir, libname, mpath.name)
    log('Extracting {} into {}'.format(name, dest))
    try:
        fileobj = tar.extractfile(member)
        dest.write_bytes(fileobj.read())
    except AttributeError:  # zipfile
        dest.write_bytes(tar.read(member))


@invoke.task()
def generate_patch(ctx, package_path, patch_description, base='HEAD'):
    pkg = Path(package_path)
    if len(pkg.parts) != 2 or pkg.parts[0] not in ('vendor', 'patched'):
        raise ValueError('example usage: generate-patch patched/piptools some-description')
    if patch_description:
        patch_fn = '{0}-{1}.patch'.format(pkg.parts[1], patch_description)
    else:
        patch_fn = '{0}.patch'.format(pkg.parts[1])
    command = 'git diff {base} -p {root} > {out}'.format(
        base=base,
        root=Path('frc2019_vision').joinpath(pkg),
        out=Path(__file__).parent.joinpath('patches', pkg.parts[0], patch_fn),
    )
    with ctx.cd(str(_get_git_root(ctx))):
        log(command)
        ctx.run(command)


@invoke.task(name=TASK_NAME)
def main(ctx, package=None):
    vendor_dir = _get_vendor_dir(ctx)
    #patched_dir = _get_patched_dir(ctx)
    log('Using vendor dir: %s' % vendor_dir)
    if package:
        vendor(ctx, vendor_dir, package=package)
        download_licenses(ctx, vendor_dir, package=package)
        log("Vendored %s" % package)
        return
    clean_vendor(ctx, vendor_dir)
    #clean_vendor(ctx, patched_dir)
    vendor(ctx, vendor_dir)
    #vendor(ctx, patched_dir)
    # download_licenses(ctx, vendor_dir)
    #download_licenses(ctx, patched_dir, 'patched.txt')
    log('Revendoring complete')
