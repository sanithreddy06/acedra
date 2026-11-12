#!/bin/bash
# ==============================================================================
# ACEDRA - database restore
#
#   PostgreSQL:  DATABASE_URL=postgresql://user:pass@host:5432/target ./database/restore_db.sh <file.sql.gz>
#   SQLite:      ./database/restore_db.sh <file.db.gz>          (restores to ./acedra.db, or $SQLITE_PATH)
#
# PostgreSQL restores run in ONE transaction and stop at the first error, so a failed restore leaves the
# target exactly as it was. The target database must be EMPTY (create a new one for the restore); pass
# --force only if you really mean to load a dump over existing tables. Stop the API before restoring a
# database it is using, and start it afterwards.
# ==============================================================================
set -euo pipefail

FORCE=false
if [ "${1:-}" = "--force" ]; then FORCE=true; shift; fi
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 [--force] <backup_file>" >&2
    exit 1
fi
BACKUP_FILE="$1"
[ -f "$BACKUP_FILE" ] || { echo "Error: backup file '$BACKUP_FILE' not found." >&2; exit 1; }

gzip -t "$BACKUP_FILE"   # refuse a corrupt archive before touching anything
if [ -f "$BACKUP_FILE.sha256" ]; then
    ( cd "$(dirname "$BACKUP_FILE")" && sha256sum -c "$(basename "$BACKUP_FILE").sha256" >/dev/null ) \
        || { echo "Error: checksum mismatch for $BACKUP_FILE." >&2; exit 1; }
    echo "Checksum verified."
fi

if [[ "$BACKUP_FILE" == *.sql.gz ]]; then
    [ -n "${DATABASE_URL:-}" ] || { echo "Error: export DATABASE_URL for the target database." >&2; exit 1; }
    CLEAN_URL="${DATABASE_URL/postgresql+psycopg:\/\//postgresql:\/\/}"
    TABLES=$(psql "$CLEAN_URL" -Atc "select count(*) from information_schema.tables where table_schema = 'public'")
    if [ "$TABLES" != "0" ] && [ "$FORCE" != true ]; then
        echo "Error: the target database already has $TABLES table(s). Restore into a new, empty database" >&2
        echo "       (createdb acedra_restored), or pass --force." >&2
        exit 1
    fi
    echo "[PostgreSQL] Restoring $BACKUP_FILE"
    gunzip -c "$BACKUP_FILE" | psql "$CLEAN_URL" --quiet --set ON_ERROR_STOP=1 --single-transaction >/dev/null
    echo "Restore complete: $(psql "$CLEAN_URL" -Atc "select count(*) from information_schema.tables where table_schema = 'public'") tables."
else
    DEST="${SQLITE_PATH:-./acedra.db}"
    if [ -f "$DEST" ]; then
        SAFETY="$DEST.before-restore-$(date +%Y%m%d_%H%M%S)"
        cp "$DEST" "$SAFETY"
        echo "[SQLite] Existing database kept as $SAFETY"
    fi
    gunzip -c "$BACKUP_FILE" > "$DEST.restoring"
    mv "$DEST.restoring" "$DEST"
    echo "Restore complete: $DEST"
fi
