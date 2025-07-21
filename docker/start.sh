#!/bin/bash

export DISPLAY=:0

# 仮想ディスプレイを起動
echo "Starting Xvfb..."
Xvfb :0 -screen 0 1280x800x24 &
sleep 2

# D-Busを起動
echo "Starting D-Bus..."
dbus-launch --exit-with-session &
sleep 1

# Openboxウィンドウマネージャを起動
echo "Starting Openbox..."
openbox-session &
sleep 2

# Chromiumをキオスクモードで起動
echo "Starting Chromium in kiosk mode..."
chromium --no-sandbox --disable-dev-shm-usage --disable-gpu --kiosk --no-first-run --disable-infobars --disable-features=TranslateUI https://example.com &
sleep 3

# VNCサーバーを起動
echo "Starting VNC server..."
x11vnc -display :0 -usepw -forever -shared -noxdamage
