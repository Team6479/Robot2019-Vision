#! /bin/bash

$SSH_ARGS="-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"
rsync -av -e "sshpass -p nvidia ssh $SSH_ARGS" --exclude='.git' \
                                     --exclude='.vscode' \
                                     --exclude '*.egg-info' \
                                     --exclude 'pip-wheel-metadata' \
                                     --exclude 'tests' \
                                     ../ nvidia@192.168.1.7:/home/nvidia/Robot2019-Vision


# Add this to end of script: pip3.6 install --no-deps --no-build-isolation --user /home/nvidia/Robot2019-Vision/

sshpass -p nvidia ssh $SSH_ARGS nvidia@192.168.1.7 << EOF
    echo 'Bootstrapping Jetson'
    pip3.6 install --user /home/nvidia/Robot2019-Vision/
EOF
