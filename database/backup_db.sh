#!/bin/bash
# ==============================================================================
# Smart Campus Intelligence — Automated Database Backup Script
# Supports PostgreSQL with pgvector as well as SQLite fallback
# Usage: ./database/backup_db.sh [backup_dir]
# ==============================================================================

set -euo pipefail

BACKUP_DIR="${1:-./database/backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p "$BACKUP_DIR"

echo "=========================================================="
echo "SMART CAMPUS INTELLIGENCE — DATABASE BACKUP ROUTINE"
echo "Timestamp: $TIMESTAMP"
echo "=========================================================="

if [ -n "${DATABASE_URL:-}" ] && [[ "$DATABASE_URL" == *"postgresql"* ]]; then
    BACKUP_FILE="$BACKUP_DIR/smart_campus_pg_$TIMESTAMP.sql.gz"
    echo "[PostgreSQL] Initiating compressed dump to $BACKUP_FILE..."
    
    # Strip dialect prefix if using SQLAlchemy psycopg format
    CLEAN_URL=$(echo "$DATABASE_URL" | sed 's/postgresql+psycopg:\/\//postgresql:\/\//')
    pg_dump "$CLEAN_URL" | gzip -9 > "$BACKUP_FILE"
    
    FILESIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✓ [PostgreSQL] Backup completed successfully. Size: $FILESIZE"
else
    # SQLite Backup
    SQLITE_PATH="./backend/smart_campus.db"
    if [ ! -f "$SQLITE_PATH" ]; then
        SQLITE_PATH="./smart_campus.db"
    fi

    if [ -f "$SQLITE_PATH" ]; then
        BACKUP_FILE="$BACKUP_DIR/smart_campus_sqlite_$TIMESTAMP.db.gz"
        echo "[SQLite] Backing up $SQLITE_PATH to $BACKUP_FILE..."
        gzip -c "$SQLITE_PATH" > "$BACKUP_FILE"
        FILESIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        echo "✓ [SQLite] Backup completed successfully. Size: $FILESIZE"
    else
        echo "Error: No valid database found to back up."
        exit 1
    fi
fi

# Retention Policy: keep only last 14 backups
echo "Applying 14-day retention cleanup on $BACKUP_DIR..."
find "$BACKUP_DIR" -type f -name "smart_campus_*" -mtime +14 -delete || true
echo "✓ Backup routine finished."
