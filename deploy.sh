#!/bin/bash
set -e

# Deploy to VPS
echo "Deploying to VPS..."

rsync -avz --delete \
  --exclude '.git/' \
  --exclude '.gitignore' \
  --exclude '.venv/' \
  --exclude '.venv/' \
  --exclude '.agent/' \
  --exclude '.gemini/' \
  --exclude '.vscode/' \
  --exclude '.idea/' \
  --exclude '.pytest_cache/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '*.pyo' \
  --exclude 'data/' \
  --exclude 'logs/' \
  --exclude 'backups/' \
  --exclude '*.db' \
  --exclude '*.sqlite' \
  --exclude '*.log' \
  --exclude '.DS_Store' \
  --exclude 'tmp/' \
  --exclude 'output_server.txt' \
  --exclude 'conversations.txt' \
  --exclude 'mejoras.txt' \
  --exclude '*_logs.txt' \
  --exclude 'README.old.md' \
  ./ azure:~/bot_whatsapp/

echo "Done, deploying container"
ssh azure "cd ~/bot_whatsapp && docker compose down && sleep 5 && docker compose build --no-cache && sleep 5 && docker compose up -d && sleep 5 && docker compose ps -a"
sleep 5
echo "Done. Showing logs..."
ssh azure "cd ~/bot_whatsapp && docker compose logs --tail=20 && sleep 5 && docker compose ps -a"
