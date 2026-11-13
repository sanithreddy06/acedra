#!/bin/bash
# ==============================================================================
# ACEDRA - start the local demo (macOS: double-click this file; Linux: ./start.command)
#
# First run: creates backend/.venv, installs the Python and Node packages, and loads the sample universities
# if there is no database yet. Every run: starts the API on http://localhost:8000 and the web app on
# http://localhost:5173, then opens the browser. Press Ctrl+C in this window to stop both.
# ==============================================================================
set -u
cd "$(dirname "$0")"
ROOT="$(pwd)"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
API_PORT=8000
WEB_PORT=5173

say()  { printf '\n\033[1m%s\033[0m\n' "$*"; }
fail() { printf '\n\033[31mCannot start: %s\033[0m\n' "$*"; echo; read -r -p "Press Return to close this window. " _ 2>/dev/null; exit 1; }

# ---------------------------------------------------------------- prerequisites
PY=""
for candidate in python3.12 python3.13 python3.11 python3.10 python3; do
    if command -v "$candidate" >/dev/null 2>&1 && \
       "$candidate" -c 'import sys; sys.exit(0 if (3, 10) <= sys.version_info[:2] <= (3, 13) else 1)' 2>/dev/null; then
        PY="$candidate"; break
    fi
done
[ -n "$PY" ] || fail "Python 3.10 to 3.13 is required. Install it with:  brew install python@3.12   (or from python.org)"

command -v node >/dev/null 2>&1 || fail "Node.js 20.19 or newer is required. Install it with:  brew install node   (or from nodejs.org)"
node -e 'const [a,b]=process.versions.node.split(".").map(Number); process.exit((a===20&&b>=19)||(a===22&&b>=12)||a>22?0:1)' \
    || fail "Node.js $(node --version) is too old. Version 20.19+ or 22.12+ is required:  brew upgrade node"

port_in_use() { (echo >"/dev/tcp/127.0.0.1/$1") >/dev/null 2>&1; }
for port in $API_PORT $WEB_PORT; do
    port_in_use "$port" && fail "Port $port is already in use. ACEDRA may already be running (open http://localhost:$WEB_PORT), or close the program using that port."
done

# ---------------------------------------------------------------- backend setup
say "1/4  Python environment ($($PY --version))"
if [ ! -x backend/.venv/bin/python ]; then
    "$PY" -m venv backend/.venv || fail "could not create backend/.venv"
fi
VENV="$ROOT/backend/.venv/bin"
STAMP="backend/.venv/.requirements.sha"
WANT="$(shasum -a 256 backend/requirements.txt 2>/dev/null || sha256sum backend/requirements.txt)"
if [ ! -f "$STAMP" ] || [ "$(cat "$STAMP")" != "$WANT" ]; then
    echo "Installing Python packages (first run takes a minute or two)..."
    "$VENV/python" -m pip install --quiet --upgrade pip
    "$VENV/python" -m pip install --quiet -r backend/requirements.txt || fail "pip could not install backend/requirements.txt (check the internet connection)"
    echo "$WANT" > "$STAMP"
fi
[ -f backend/.env ] || cp backend/.env.example backend/.env

say "2/4  Database"
if [ ! -f acedra.db ]; then
    echo "No database yet: loading the sample universities (REVA University and two others)..."
    "$VENV/python" database/seeds/seed_all.py > /dev/null || fail "could not create the sample database"
fi
echo "Using $ROOT/acedra.db"

# ---------------------------------------------------------------- frontend setup
say "3/4  Web app packages"
LOCK_STAMP="frontend/node_modules/.package-lock.sha"
LOCK_WANT="$(shasum -a 256 frontend/package-lock.json 2>/dev/null || sha256sum frontend/package-lock.json)"
if [ ! -f "$LOCK_STAMP" ] || [ "$(cat "$LOCK_STAMP")" != "$LOCK_WANT" ]; then
    echo "Installing Node packages (first run takes a minute)..."
    (cd frontend && npm ci --no-fund --no-audit --loglevel=error) || fail "npm could not install the web app packages (check the internet connection)"
    echo "$LOCK_WANT" > "$LOCK_STAMP"
fi

# ---------------------------------------------------------------- run
say "4/4  Starting ACEDRA"
mkdir -p .run
API_PID=""; WEB_PID=""
stop() {
    echo; echo "Stopping ACEDRA..."
    [ -n "$WEB_PID" ] && kill "$WEB_PID" 2>/dev/null
    [ -n "$API_PID" ] && kill "$API_PID" 2>/dev/null
    wait 2>/dev/null
    exit 0
}
trap stop INT TERM HUP

(cd backend && exec "$VENV/python" -m uvicorn app.main:app --host 127.0.0.1 --port "$API_PORT") > .run/api.log 2>&1 &
API_PID=$!
for _ in $(seq 1 60); do
    kill -0 "$API_PID" 2>/dev/null || { tail -n 15 .run/api.log; fail "the API stopped while starting (details above; full log in .run/api.log)"; }
    curl -fs "http://127.0.0.1:$API_PORT/ready" >/dev/null 2>&1 && break
    sleep 1
done
curl -fs "http://127.0.0.1:$API_PORT/ready" >/dev/null 2>&1 || { tail -n 15 .run/api.log; kill "$API_PID" 2>/dev/null; fail "the API did not become ready (full log in .run/api.log)"; }
echo "API ready      http://localhost:$API_PORT"

(cd frontend && exec npx vite --host 127.0.0.1 --port "$WEB_PORT" --strictPort) > .run/web.log 2>&1 &
WEB_PID=$!
for _ in $(seq 1 60); do
    kill -0 "$WEB_PID" 2>/dev/null || { tail -n 15 .run/web.log; kill "$API_PID" 2>/dev/null; fail "the web app stopped while starting (full log in .run/web.log)"; }
    curl -fs "http://127.0.0.1:$WEB_PORT/" >/dev/null 2>&1 && break
    sleep 1
done
echo "Web app ready  http://localhost:$WEB_PORT"

cat <<INFO

  ACEDRA is running. Sign in at http://localhost:$WEB_PORT/login

    Administrator      anitha.rao@reva.in        AdminPass123!
    Faculty            kavya.menon@reva.in       FacultyPass123!
    Mentor             suresh.hegde@reva.in      MentorPass123!
    Placement officer  rahul.deshpande@reva.in   PlacementPass123!
    Student            aarav.sharma@reva.in      StudentPass123!
    Platform team      superadmin@acedra.example PlatformPass123!

  Keep this window open. Press Ctrl+C here to stop.

INFO
command -v open >/dev/null 2>&1 && open "http://localhost:$WEB_PORT/login"

# Stay up until either process exits or the window is interrupted.
while kill -0 "$API_PID" 2>/dev/null && kill -0 "$WEB_PID" 2>/dev/null; do sleep 2; done
echo "A server process stopped unexpectedly. Last lines of the logs:"
tail -n 8 .run/api.log .run/web.log
stop
