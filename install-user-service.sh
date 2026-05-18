#!/usr/bin/env bash

set -euo pipefail

REPO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
UNIT_DIR="$HOME/.config/systemd/user"
UNIT_FILE="$UNIT_DIR/streamerbot-chat-server.service"

mkdir -p "$UNIT_DIR"

cat > "$UNIT_FILE" <<EOF
[Unit]
Description=StreamerBot Chat Local HTTP Server
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
WorkingDirectory=$REPO_DIR
ExecStart=/usr/bin/env python3 $REPO_DIR/chat-server.py --host 127.0.0.1 --port 8765 --directory $REPO_DIR
Restart=on-failure
RestartSec=2
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now streamerbot-chat-server.service

echo "Installed and started: streamerbot-chat-server.service"
echo "Open: http://127.0.0.1:8765/chat.html"
echo "Check status: systemctl --user status streamerbot-chat-server.service"
