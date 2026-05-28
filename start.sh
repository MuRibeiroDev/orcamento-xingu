#!/usr/bin/env bash
# Sobe backend (porta 8000) e frontend (porta 5173) juntos para desenvolvimento.
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="/opt/homebrew/bin:$PATH"

echo "==> Backend (http://localhost:8000)"
cd "$DIR/backend"
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
[ -f .env ] || cp .env.example .env
uvicorn app.main:app --reload --port 8000 &
BACK_PID=$!

echo "==> Frontend (http://localhost:5173)"
cd "$DIR/frontend"
[ -d node_modules ] || npm install
[ -f .env ] || cp .env.example .env
npm run dev

kill $BACK_PID 2>/dev/null || true
