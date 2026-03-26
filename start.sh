#!/bin/bash
cd "$(dirname "$0")"

# Stop ModemManager so it doesn't grab the serial port
sudo systemctl stop ModemManager

# Start the WebSocket server in the background
python3 server.py &
SERVER_PID=$!

# Wait for server to be ready
sleep 1

# Open the visualizer in the browser
xdg-open visualizer.html

# Wait for server process — Ctrl+C to stop
trap "kill $SERVER_PID 2>/dev/null; sudo systemctl start ModemManager" EXIT
wait $SERVER_PID
