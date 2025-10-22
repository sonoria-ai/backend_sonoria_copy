#!/bin/bash

echo "Testing create assistant API..."
echo ""

curl -X POST http://localhost:8000/assistant/create-assistant/ \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": 1,
    "name": "Sonoria",
    "voice_type": "alloy",
    "greeting_message": "hi how are you"
  }'

echo ""
echo ""
echo "Checking assistant status..."
curl -s 'http://localhost:8000/assistant/status/?org_id=1'
echo ""
