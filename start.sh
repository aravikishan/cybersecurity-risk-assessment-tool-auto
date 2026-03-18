#!/bin/bash
set -e
echo "Starting Cybersecurity Risk Assessment Tool..."
uvicorn app:app --host 0.0.0.0 --port 9055 --workers 1
