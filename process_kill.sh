#!/bin/bash

# Specify the port you want to free up
PORT=8000  # Replace with your specific port

# Find and kill all processes using the specified port
lsof -i tcp:$PORT | grep LISTEN | awk '{print $2}' | xargs kill -9

echo "All processes running on port $PORT have been killed."
