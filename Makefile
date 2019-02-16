format:
	black frc2019_vision
	isort -y

update_vendored_packages:
	inv vendoring.update

# Used for deploying the code to the Jetson
deploy:
	rsync -av -e 'sshpass -p nvidia ssh' --exclude='.git' --exclude '*.egg-info' --exclude 'pip-wheel-metadata' . nvidia@192.168.1.7:/home/nvidia/Robot2019-Vision
	sshpass -p nvidia ssh nvidia@192.168.1.7 'pip3.6 install --no-deps --no-build-isolation --user /home/nvidia/Robot2019-Vision/'

