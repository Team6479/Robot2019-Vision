import codecs
import os

from setuptools import find_packages, setup

# Taken from pipenv
# See https://github.com/pypa/pipenv/blob/master/setup.py
here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = "\n" + f.read()

about = {}
with open(os.path.join(here, "frc2019_vision", "__version__.py")) as f:
    exec(f.read(), about)

setup(
    name='frc2019_vision',
    version=about["__version__"],
    description='An opinionated tool to generate base projects for a multitude of languages.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/Team6479/Robot2019-Vision',
    author='Team6479',
    packages=find_packages(exclude=["tasks", "tasks.*"]),
    entry_points={
        'console_scripts': [
            'vision-2019 = frc2019_vision.__main__:main',
        ]
    },
    package_data={
        "": ["LICENSE"]
    },
    include_package_data=True,
    license='MIT',
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
)
