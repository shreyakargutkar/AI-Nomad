#!/bin/bash

echo "Stopping all WanderBot services..."

for port in 5004 5005 5006 5007 5008 5009 5010 5011 5012 5013 3000; do
    pid=$(lsof -t -i:$port)
    if [ ! -z "$pid" ]; then
        echo "Killing service on port $port (PID: $pid)..."
        kill -9 $pid 2>/dev/null
    fi
done

echo "All services stopped."
