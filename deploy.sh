#!/bin/bash
set -e

REMOTE_HOST="azure"
REMOTE_TMP="~/tmp/bot_whatsapp"
REMOTE_DIR="~/bot_whatsapp"

# Deploy to VPS (Temp folder)
echo "Deploying to VPS (Temp: $REMOTE_TMP)..."

# Ensure temp dir exists and is clean
ssh $REMOTE_HOST "rm -rf $REMOTE_TMP && mkdir -p $REMOTE_TMP"

rsync -avz \
  --exclude '.git/' \
  --exclude '.gitignore' \
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
  ./ $REMOTE_HOST:$REMOTE_TMP/

echo "Files transferred. Building and deploying..."

ssh $REMOTE_HOST "
    set -e
    
    # 1. Build image in temp
    cd $REMOTE_TMP
    echo 'Building image...'
    docker compose build --no-cache

    # 2. Prepare production directory
    echo 'Preparing production directory...'
    mkdir -p $REMOTE_DIR
    
    # Copy essential files
    cp .env docker-compose.yml $REMOTE_DIR/
    
    # Update config and docs (using rsync to preserve permissions and only update changed)
    # Using local rsync on server if available, or just cp -r
    # cp -r is safer if rsync not installed on minimal server, but rsync is usually there.
    # We used rsync to upload, so it's there.
    mkdir -p $REMOTE_DIR/config $REMOTE_DIR/docs
    rsync -av --delete config/ $REMOTE_DIR/config/
    rsync -av --delete docs/ $REMOTE_DIR/docs/
    
    # Ensure data/logs dirs exist
    mkdir -p $REMOTE_DIR/data $REMOTE_DIR/logs

    # 3. Deploy in production
    cd $REMOTE_DIR
    echo 'Restarting services...'
    docker compose down
    sleep 3
    docker compose up -d

    # 4. Cleanup
    echo 'Cleaning up temp files...'
    rm -rf $REMOTE_TMP

    # 5. Show status
    echo 'Deployment complete!'
    docker compose ps -a
    sleep 5
    docker compose logs --tail=20
"
