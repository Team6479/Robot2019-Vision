#! /bin/bash

rsync -av -e 'sshpass -p nvidia ssh' --exclude='.git' \
                                     --exclude='.vscode' \
                                     --exclude '*.egg-info' \
                                     --exclude 'pip-wheel-metadata' \
                                     --exclude 'tests' \
                                     ../ nvidia@192.168.1.7:/home/nvidia/Robot2019-Vision


# Add this to end of script: pip3.6 install --no-deps --no-build-isolation --user /home/nvidia/Robot2019-Vision/

sshpass -p nvidia ssh nvidia@192.168.1.7 << EOF
    echo 'Bootstrapping Jetson'
    pip3.6 install --no-deps --no-build-isolation --user /home/nvidia/Robot2019-Vision/
EOF
