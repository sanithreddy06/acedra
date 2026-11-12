#!/bin/bash
# ==============================================================================
# Build a clean ACEDRA release directory and archive from the committed state of the repository.
#
#   ./scripts/make_release.sh [version]        (default: the VERSION in backend/app/core/config.py)
#
# Output (in ./release, which is git-ignored):
#   release/acedra-<version>/            the release tree
#   release/acedra-<version>/MANIFEST.txt   every file with its SHA-256
#   release/acedra-<version>.tar.gz      the same tree as one archive, plus its .sha256
#
# Only files tracked by Git are included, so nothing ignored can leak in: no .git, databases, backups,
# recovery archives, caches, node_modules, .env files, TLS material or .DS_Store. The v0.1 documentation
# archive is left out as well. The script refuses to run with uncommitted changes and re-checks the result.
# ==============================================================================
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

VERSION="${1:-$(sed -n 's/^ *VERSION: str = "\(.*\)"$/\1/p' backend/app/core/config.py)}"
[ -n "$VERSION" ] || { echo "Error: could not determine the version." >&2; exit 1; }
if [ -n "$(git status --porcelain)" ]; then
    echo "Error: uncommitted changes. Commit or stash them; a release is built from a commit." >&2
    exit 1
fi

NAME="acedra-$VERSION"
OUT="release/$NAME"
mkdir -p release
if [ -e "$OUT" ] || [ -e "release/$NAME.tar.gz" ]; then
    echo "Error: release/$NAME already exists. Move it away or choose another version." >&2
    exit 1
fi
mkdir "$OUT"
git archive --format=tar HEAD -- . ':(exclude)documentation/archive_v0.1' | tar -x -C "$OUT"

# Belt and braces: fail if anything that must never ship is present.
FORBIDDEN=$(cd "$OUT" && find . \( -name '.git' -o -name '*.db' -o -name '*.sqlite3' -o -name '*.gz' -o -name '*.tgz' \
    -o -name '.DS_Store' -o -name '__pycache__' -o -name '*.pyc' -o -name 'node_modules' -o -name '.ruff_cache' \
    -o -name '.pytest_cache' -o -name '_recovery' -o -name 'backups' -o -name '*.pem' -o -name '*.log' -o -name '*.tmp' \
    -o -name '.env' -o -name '.env.production' -o -name 'dist' \) -print)
if [ -n "$FORBIDDEN" ]; then
    echo "Error: files that must not be released were found:" >&2; echo "$FORBIDDEN" >&2
    exit 1
fi

{
    echo "ACEDRA $VERSION"
    echo "Commit: $(git rev-parse HEAD)"
    echo "Built:  $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo
    ( cd "$OUT" && find . -type f ! -name MANIFEST.txt | LC_ALL=C sort | sed 's|^\./||' | xargs -d '\n' sha256sum )
} > "$OUT/MANIFEST.txt"

tar -czf "release/$NAME.tar.gz" -C release "$NAME"
( cd release && sha256sum "$NAME.tar.gz" > "$NAME.tar.gz.sha256" )

echo "Release directory: $OUT ($(find "$OUT" -type f | wc -l) files, $(du -sh "$OUT" | cut -f1))"
echo "Release archive:   release/$NAME.tar.gz ($(du -h "release/$NAME.tar.gz" | cut -f1))"
