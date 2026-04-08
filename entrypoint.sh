#!/bin/bash
set -e

mkdir -p /data

# Generate icons only if missing (Pillow optional)
python generate_icons.py || echo "Icon generation skipped (icons may already exist)"

python -c "
from app import app, db, init_db
with app.app_context():
    init_db()
"

exec gunicorn --bind 0.0.0.0:6000 --workers 2 --timeout 120 app:app
