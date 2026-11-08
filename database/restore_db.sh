#!/bin/bash
# ==============================================================================
# Smart Campus Intelligence — Database Restoration Script
# Usage: ./database/restore_db.sh <backup_file_path>
# ==============================================================================

set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <backup_file_path>"
    echo "Example: $0 ./database/backups/smart_campus_sqlite_20261109_020000.db.gz"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file '$BACKUP_FILE' not found."
    exit 1
fi

echo "=========================================================="
echo "SMART CAMPUS INTELLIGENCE — RESTORING DATABASE"
echo "Target archive: $BACKUP_FILE"
echo "=========================================================="

if [[ "$BACKUP_FILE" == *"pg_"* ]] || [[ "$BACKUP_FILE" == *".sql.gz"* ]]; then
    if [ -z "${DATABASE_URL:-}" ]; then
        echo "Error: DATABASE_URL must be exported to restore PostgreSQL archive."
        exit 1
    fi
    CLEAN_URL=$(echo "$DATABASE_URL" | sed 's/postgresql+psycopg:\/\//postgresql:\/\//')
    echo "[PostgreSQL] Decompressing and restoring to target database..."
    gunzip -c "$BACKUP_FILE" | psql "$CLEAN_URL"
    echo "✓ [PostgreSQL] Restoration complete."
else
    # SQLite Restoration
    DEST="./backend/smart_campus.db"
    echo "[SQLite] Restoring archive to $DEST..."
    gunzip -c "$BACKUP_FILE" > "$DEST"
    echo "✓ [SQLite] Database file restored successfully to $DEST."
fi
