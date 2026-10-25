#!/bin/bash

# Navigate to workspace
CWD="/Users/smitakargutkar/Desktop/ainomad"
cd "$CWD"

# Check if .env exists in root
if [ -f .env ]; then
    echo "Found .env in root. Ensuring single source of truth is used."
else
    echo "WARNING: .env not found in root!"
fi

# Function to kill existing processes on these ports to avoid address-already-in-use errors
cleanup_ports() {
    echo "Checking and cleaning up ports..."
    for port in 5004 5005 5006 5007 5008 5009 5010 5011 5012 5013 3000; do
        pid=$(lsof -t -i:$port)
        if [ ! -z "$pid" ]; then
            echo "Port $port is in use by PID $pid. Killing..."
            kill -9 $pid 2>/dev/null
        fi
    done
}

cleanup_ports

# Prevent broken dev server from stale/corrupt Turbopack cache
if [ -d "frontend/.next" ]; then
    echo "Clearing frontend .next cache (avoids blank/broken pages)..."
    rm -rf frontend/.next
fi

echo "Starting backend services..."

# Start Chatbot on 5006
.venv/bin/python backend/services/chatbot/app.py > backend/chatbot.log 2>&1 &
echo "✓ Chatbot Service started (Port 5006)"

# Start Festivals on 5004
.venv/bin/python backend/services/festivals/app.py > backend/festivals.log 2>&1 &
echo "✓ Festivals Service started (Port 5004)"

# Start Itinerary on 5005
.venv/bin/python backend/services/itinerary/app.py > backend/itinerary.log 2>&1 &
echo "✓ Itinerary Service started (Port 5005)"

# Start Readiness on 5007
.venv/bin/python backend/services/readiness/app.py > backend/readiness.log 2>&1 &
echo "✓ Readiness Service started (Port 5007)"

# Start Journal on 5008
.venv/bin/python backend/services/journal/app.py > backend/journal.log 2>&1 &
echo "✓ Journal Service started (Port 5008)"

# Start Budget Intelligence on 5009
.venv/bin/python backend/services/budget_intelligence/app.py > backend/budget_intelligence.log 2>&1 &
echo "✓ Budget Intelligence Service started (Port 5009)"

# Start Emergency Companion on 5010
.venv/bin/python backend/services/emergency/app.py > backend/emergency.log 2>&1 &
echo "✓ Emergency Companion Service started (Port 5010)"

# Start Contextual Recommendations on 5011
.venv/bin/python backend/services/recommendations/app.py > backend/recommendations.log 2>&1 &
echo "✓ Contextual Recommendations Service started (Port 5011)"

# Start Budget Predictor on 5012
.venv/bin/python backend/services/budget_predictor/app.py > backend/budget_predictor.log 2>&1 &
echo "✓ Budget Predictor Service started (Port 5012)"

# Start Smart Day Planner on 5013
.venv/bin/python backend/services/smart_day_planner/app.py > backend/smart_day_planner.log 2>&1 &
echo "✓ Smart Day Planner Service started (Port 5013)"

echo "Waiting for smart day planner API (up to 15s)..."
for i in $(seq 1 15); do
    if python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:5013/health', timeout=2)" 2>/dev/null; then
        echo "✓ Smart Day Planner API ready (Port 5013)"
        break
    fi
    sleep 1
    if [ "$i" -eq 15 ]; then
        echo "⚠ Smart Day Planner API slow to start — check backend/smart_day_planner.log"
    fi
done

echo "Waiting for budget predictor API (up to 15s)..."
for i in $(seq 1 15); do
    if python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:5012/health', timeout=2)" 2>/dev/null; then
        echo "✓ Budget Predictor API ready (Port 5012)"
        break
    fi
    sleep 1
    if [ "$i" -eq 15 ]; then
        echo "⚠ Budget Predictor API slow to start — check backend/budget_predictor.log"
    fi
done

echo "Waiting for recommendations API (up to 15s)..."
for i in $(seq 1 15); do
    if python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:5011/health', timeout=2)" 2>/dev/null; then
        echo "✓ Recommendations API ready (Port 5011)"
        break
    fi
    sleep 1
    if [ "$i" -eq 15 ]; then
        echo "⚠ Recommendations API slow to start — check backend/recommendations.log"
    fi
done

echo "Starting frontend dev server..."
nohup npm run dev --prefix frontend > frontend.log 2>&1 &

echo "Waiting for frontend (up to 30s)..."
for i in $(seq 1 30); do
    if python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:3000', timeout=2)" 2>/dev/null; then
        echo "✓ Frontend ready at http://localhost:3000"
        break
    fi
    sleep 1
    if [ "$i" -eq 30 ]; then
        echo "⚠ Frontend slow to start — check frontend.log"
    fi
done

echo ""
echo "All services running. Open http://localhost:3000"
echo "Logs: frontend.log, backend/*.log | Stop: ./stop_services.sh"
