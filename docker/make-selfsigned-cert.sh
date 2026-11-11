#!/bin/sh
# Creates a self-signed certificate in docker/certs for a local smoke test of the production stack.
# Browsers will warn about it. Use a certificate from your CA or Let's Encrypt for a real deployment.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)/certs"
HOST="${1:-localhost}"
mkdir -p "$DIR"
openssl req -x509 -nodes -newkey rsa:2048 -days 30 \
  -keyout "$DIR/privkey.pem" -out "$DIR/fullchain.pem" \
  -subj "/CN=$HOST" -addext "subjectAltName=DNS:$HOST"
echo "Wrote $DIR/fullchain.pem and $DIR/privkey.pem for $HOST (valid 30 days)."
