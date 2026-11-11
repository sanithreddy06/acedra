#!/bin/bash
# ==============================================================================
# ACEDRA — Database Restoration Script
# Usage: ./database/restore_db.sh <backup_file_path>      (run from the project root; SQLITE_PATH overrides the target)
# ==============================================================================

set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <backup_file_path>"
    echo "Example: $0 ./database/backups/acedra_sqlite_20261109_020000.db.gz"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file '$BACKUP_FILE' not found."
    exit 1
fi

echo "=========================================================="
echo "ACEDRA — RESTORING DATABASE"
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
    # SQLite restoration — the application's database lives at the project root (DATABASE_URL=sqlite:///./acedra.db).
    DEST="${SQLITE_PATH:-./acedra.db}"
    gzip -t "$BACKUP_FILE"  # refuse corrupt archives before touching anything
    if [ -f "$DEST" ]; then
        SAFETY="$DEST.before-restore-$(date +%Y%m%d_%H%M%S)"
        cp "$DEST" "$SAFETY"
        echo "[SQLite] Existing database kept as $SAFETY"
    fi
    echo "[SQLite] Restoring archive to $DEST..."
    gunzip -c "$BACKUP_FILE" > "$DEST.restoring"
    mv "$DEST.restoring" "$DEST"
    echo "✓ [SQLite] Database file restored successfully to $DEST. Stop the API before restoring and start it afterwards."
fi
