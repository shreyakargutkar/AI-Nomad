#!/bin/bash
# Full reset when pages show blank or 500 errors
cd "$(dirname "$0")"
./stop_services.sh 2>/dev/null
rm -rf frontend/.next
./start_services.sh
