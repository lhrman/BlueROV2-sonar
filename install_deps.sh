#!/bin/bash
set -e  # stani ako bilo što failsa

echo "=== Instalacija dependencies ==="

sudo apt update

sudo apt install -y \
    ros-humble-robot-localization \
    ros-humble-slam-toolbox \
    ros-humble-rmw-cyclonedds-cpp

sudo apt install -y python3-pip

python3 -m pip install pymavlink pygame

echo "=== Gotovo! ==="