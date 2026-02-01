#  Utility Scripts

These scripts are located in `scripts/` and are designed to help you manage the bot's data and database.

## 1.  `update_rag.py` - Knowledge Update
This script scans the `docs/` folder, processes all documents (PDF, MD, TXT, DOCX), and rebuilds the bot's "digital brain" (BM25 index).

**When to use:**
- After adding or updating files in `docs/`.
- If the bot isn't answering correctly based on latest information.

**Usage:**
```bash
docker compose exec app python scripts/update_rag.py
```

---

## 2.  `reset_db.py` - Database Reset
This is a **destructive** script. It completely deletes all tables (Users, Conversations, Messages, Tickets) and recreates them from scratch.

**When to use:**
- If you want to clear all chat history and start over.
- During troubleshooting if the database schema gets corrupted.

**Usage:**
```bash
docker compose exec app python scripts/reset_db.py
```

---

> [!WARNING]  
> Using `reset_db.py` will permanently delete all customer data and chat history. Use with caution.
