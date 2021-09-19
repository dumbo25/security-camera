#!/bin/bash
# sript to add motioneye to a Raspberry Pi running Raspberry Pi OS
#
# run as
#   sudo bash motioneye.sh

# Install ffmpeg and other motion dependencies:
sudo apt install ffmpeg libmariadb3 libpq5 libmicrohttpd12 -y

# Install motion:
# note: Raspbian Buster comes with motion version 4.1; it is recommended version 4.2 is installed
wget https://github.com/Motion-Project/motion/releases/download/release-4.2.2/pi_buster_motion_4.2.2-1_armhf.deb
# sudo apt install motion
dpkg -i pi_buster_motion_4.2.2-1_armhf.deb

# Install the dependencies from the repositories:
sudo apt install python-pip python-dev libssl-dev libcurl4-openssl-dev libjpeg-dev libz-dev -y

# Install motioneye, which will automatically pull Python dependencies (tornado, jinja2, pillow and pycurl):
sudo pip install motioneye

# Prepare the configuration directory:
mkdir -p /etc/motioneye
cp /usr/local/share/motioneye/extra/motioneye.conf.sample /etc/motioneye/motioneye.conf

# Prepare the media directory:
mkdir -p /var/lib/motioneye

# Add an init script, configure it to run at startup and start the motionEye server:
cp /usr/local/share/motioneye/extra/motioneye.systemd-unit-local /etc/systemd/system/motioneye.service
systemctl daemon-reload
systemctl enable motioneye
systemctl start motioneye



