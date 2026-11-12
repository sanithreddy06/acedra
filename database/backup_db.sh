#!/bin/bash
# ==============================================================================
# ACEDRA - database backup
#
#   PostgreSQL:  DATABASE_URL=postgresql://user:pass@host:5432/acedra ./database/backup_db.sh [backup_dir]
#   SQLite:      ./database/backup_db.sh [backup_dir]            (copies ./acedra.db, or $SQLITE_PATH)
#
# Writes a gzip-compressed plain SQL dump (PostgreSQL) or database copy (SQLite), verifies the archive,
# records its SHA-256 next to it, and removes ACEDRA backups in that directory older than
# BACKUP_RETENTION_DAYS (default 14). The dump has no ownership or privilege statements, so it restores
# under any database user.
# ==============================================================================
set -euo pipefail

BACKUP_DIR="${1:-./database/backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p "$BACKUP_DIR"
umask 077   # backups contain personal data: readable by the owner only

if [ -n "${DATABASE_URL:-}" ] && [[ "$DATABASE_URL" == postgresql* ]]; then
    BACKUP_FILE="$BACKUP_DIR/acedra_pg_$TIMESTAMP.sql.gz"
    CLEAN_URL="${DATABASE_URL/postgresql+psycopg:\/\//postgresql:\/\/}"   # accept the SQLAlchemy form too
    echo "[PostgreSQL] Dumping to $BACKUP_FILE"
    if ! pg_dump --no-owner --no-privileges "$CLEAN_URL" | gzip -9 > "$BACKUP_FILE.partial"; then
        rm -f "$BACKUP_FILE.partial"
        echo "Error: pg_dump failed; no backup was written." >&2
        exit 1
    fi
else
    SQLITE_PATH="${SQLITE_PATH:-./acedra.db}"
    if [ ! -f "$SQLITE_PATH" ]; then
        echo "Error: no DATABASE_URL for PostgreSQL and no SQLite database at $SQLITE_PATH." >&2
        exit 1
    fi
    BACKUP_FILE="$BACKUP_DIR/acedra_sqlite_$TIMESTAMP.db.gz"
    echo "[SQLite] Copying $SQLITE_PATH to $BACKUP_FILE"
    gzip -c "$SQLITE_PATH" > "$BACKUP_FILE.partial"
fi

gzip -t "$BACKUP_FILE.partial"          # never keep an archive that cannot be read back
mv "$BACKUP_FILE.partial" "$BACKUP_FILE"
( cd "$BACKUP_DIR" && sha256sum "$(basename "$BACKUP_FILE")" > "$(basename "$BACKUP_FILE").sha256" )
echo "Backup written: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"

find "$BACKUP_DIR" -type f -name "acedra_*" -mtime +"$RETENTION_DAYS" -delete || true
