#!/bin/bash
# Verification Script for Conversation Lifecycle Implementation
# Run this after starting Docker

set -e

echo "🚀 Phase 3 Verification Script"
echo "================================"

# Step 1: Verify Docker is running
echo ""
echo "Step 1: Checking Docker..."
if ! docker ps &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi
echo "✅ Docker is running"

# Step 2: Start containers
echo ""
echo "Step 2: Starting containers..."
docker-compose up -d
sleep 5
echo "✅ Containers started"

# Step 3: Reset database
echo ""
echo "Step 3: Resetting database schema..."
python scripts/reset_db.py
if [ $? -eq 0 ]; then
    echo "✅ Database reset successful"
else
    echo "❌ Database reset failed"
    exit 1
fi

# Step 4: Run tests
echo ""
echo "Step 4: Running integration tests..."
pytest tests/test_conversation_lifecycle.py -v --tb=short

# Step 5: Show summary
echo ""
echo "================================"
echo "📊 Verification Summary"
echo "================================"
echo ""
echo "Verified Components:"
echo "  ✅ Database models (User, Conversation, Message)"
echo "  ✅ Session manager conversation lifecycle"
echo "  ✅ User service identity management"
echo "  ✅ Message processor integration"
echo "  ✅ Conversation closure logic"
echo ""
echo "Next Steps:"
echo "  1. Review walkthrough.md for manual testing procedures"
echo "  2. Test with real WhatsApp messages"
echo "  3. Monitor logs for any errors"
echo ""
echo "Database Inspection Commands:"
echo "  docker-compose exec postgres psql -U chatbot -d chatbot_db"
echo "  SELECT * FROM users;"
echo "  SELECT * FROM conversations;"
echo "  SELECT * FROM messages;"
