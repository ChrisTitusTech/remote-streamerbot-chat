# remote-streamerbot-chat

A lightweight live chat overlay that connects to a remote [Streamer.bot](https://streamer.bot/) instance over WebSocket and displays Twitch/YouTube chat messages in a clean dark-themed browser window.

---

## How It Works

```
Streamer.bot (Windows PC at 10.0.0.95)
        │
        │  WebSocket  ws://10.0.0.95:8080
        │
Linux machine
  └── ./chat  (bash script)
          └── localhost HTTP server
            └── brave-origin-nightly  (Chromium-based)
              └── chat.html  (UI + streamerbot-client.js)
```

1. The `chat` script starts a local HTTP server on `127.0.0.1` and launches an isolated Brave Nightly window pointed at `chat.html`.
2. `chat.html` loads the bundled `streamerbot-client.js` library and opens a WebSocket connection to Streamer.bot.
3. Incoming `Twitch.ChatMessage` and `YouTube.ChatMessage` events are parsed and rendered in real time.

Using localhost avoids `file://` browser security restrictions and works reliably in browsers and embedded previews.

---

## Requirements

| Dependency | Purpose |
|---|---|
| `brave-origin-nightly` | Chromium-based browser used to display the overlay |
| `bash` | Runs the launcher script |
| `python3` | Serves the overlay over localhost |

`curl` is not required.

---

## File Structure

```
remote-streamerbot-chat/
├── chat                   # Bash launcher script
├── chat.html              # Chat overlay UI
├── streamerbot-client.js  # Bundled @streamerbot/client library (local copy)
├── install.sh             # Installs the desktop entry for your app launcher
└── README.md              # This file
```

---

## Setup

### 1. Streamer.bot (Windows machine)

1. Open Streamer.bot.
2. Go to **Servers/Clients → WebSocket Server**.
3. Enable the WebSocket server.
4. Set the **bind address** to your LAN IP (e.g. `10.0.0.95`) — **not** `127.0.0.1`, otherwise remote connections will be refused.
5. Set the port to `8080` (or update `chat.html` to match your chosen port).
6. Make sure your Windows firewall allows inbound connections on that port.

### 2. Linux machine

Clone the repo:

```bash
git clone https://github.com/YOUR_USERNAME/remote-streamerbot-chat.git
cd remote-streamerbot-chat
```

Make the script executable:

```bash
chmod +x chat
```

Edit `chat.html` and update the host/port to match your Streamer.bot machine:

```js
const client = new StreamerbotClient({
    host: "10.0.0.95",  // ← your Streamer.bot machine's LAN IP
    port: 8080,
    password: "",         // ← fill in if you set a password in Streamer.bot
    autoReconnect: true,
    ...
});
```

---

## Usage

```bash
./chat
```

Or from anywhere:

```bash
~/github/remote-streamerbot-chat/chat
```

The overlay opens as a standalone app window (no browser chrome/address bar) with:

- A **dark header** showing "Live Chat" and a connection status badge
  - 🟠 Orange = Connecting…
  - 🟢 Green = Connected
  - 🔴 Red = Disconnected
- Each chat message shows:
  - 🟣 Twitch or 🔴 YouTube platform icon
  - User badges (broadcaster, subscriber, etc.)
  - Username in the user's chat colour
  - Message text
  - Timestamp

The window blocks the terminal until it is closed, then exits cleanly.

---

## How the Script Works

```bash
#!/usr/bin/env bash

CHAT_DIR="$HOME/github/remote-streamerbot-chat"
CHAT_FILE="$CHAT_DIR/chat.html"
PROFILE_DIR="$HOME/.config/streamerbot-chat-profile"
SERVER_HOST="127.0.0.1"
SERVER_PORT="${STREAMERBOT_CHAT_PORT:-8765}"
BROWSER_CMD="${STREAMERBOT_CHAT_BROWSER:-brave-origin-nightly}"
```

- **`CHAT_DIR`** — absolute path to the project directory so the local HTTP server can expose `chat.html` and `streamerbot-client.js`.
- **`CHAT_FILE`** — absolute path to the HTML entry file, hardcoded to `$HOME`.
- **`PROFILE_DIR`** — a persistent isolated Chromium profile stored in `~/.config`. Keeping it persistent avoids a slow first-run initialisation on every launch.
- **`SERVER_PORT`** — the local port used for the temporary HTTP server. Override with `STREAMERBOT_CHAT_PORT` if needed.
- **`BROWSER_CMD`** — browser executable used to open the overlay. Override with `STREAMERBOT_CHAT_BROWSER` if you want a different Chromium-based browser.

```bash
rm -f "$PROFILE_DIR/SingletonLock" "$PROFILE_DIR/SingletonCookie" "$PROFILE_DIR/SingletonSocket"
```

Chromium writes a `SingletonLock` file to prevent two instances sharing a profile. If the browser crashes or is killed, the lock is never cleaned up, causing subsequent launches to hand the URL off to a non-existent process (resulting in a grey window). Only the lock files are removed — the rest of the profile is preserved.

```bash
python3 -m http.server "$SERVER_PORT" \
  --bind "$SERVER_HOST" \
  --directory "$CHAT_DIR" \
  >/dev/null 2>&1 &

"$BROWSER_CMD" \
  --user-data-dir="$PROFILE_DIR" \
  --disable-gpu \
  --ozone-platform=x11 \
  --no-first-run \
  --no-default-browser-check \
  --disable-extensions \
  --class="StreamerBotChat" \
  "http://${SERVER_HOST}:${SERVER_PORT}/chat.html"
```

| Flag | Reason |
|---|---|
| `--user-data-dir` | Forces a new isolated browser process; prevents URL handoff to an existing browser session |
| `--disable-gpu` | Works around a `vaInitialize failed` GPU error that causes grey windows on some systems |
| `--ozone-platform=x11` | Explicitly selects X11 rendering on X11 sessions |
| `--no-first-run` | Skips the new-profile welcome screen |
| `--no-default-browser-check` | Suppresses the browser default-check prompt |
| `--disable-extensions` | Prevents extensions (e.g. uBlock) from initialising, speeding up startup |
| `--class=StreamerBotChat` | Sets the X11 window class, useful for window manager rules |

The script runs the local server in the background, waits for it to become reachable, then runs the browser in the foreground. When the browser exits, the background server is cleaned up automatically.

---

## Updating the Streamer.bot Client Library

`streamerbot-client.js` is a local copy of the
[`@streamerbot/client`](https://www.npmjs.com/package/@streamerbot/client) npm package.
It is bundled locally so the overlay works without internet access.

To update it to the latest version:

```bash
curl -sL "https://cdn.jsdelivr.net/npm/@streamerbot/client/dist/streamerbot-client.js" \
  -o ~/github/remote-streamerbot-chat/streamerbot-client.js
```

---

## Changing the Streamer.bot Host or Port

Edit `chat.html` and update the `StreamerbotClient` constructor:

```js
const client = new StreamerbotClient({
    host: "10.0.0.95",  // LAN IP of the machine running Streamer.bot
    port: 8080,          // WebSocket server port set in Streamer.bot
    password: "",        // Leave empty if no password is set
    autoReconnect: true,
    ...
});
```

---

## Installing as a Desktop Application

Run the included install script to register the overlay as an application in your launcher (rofi, dmenu, GNOME, KDE, etc.):

```bash
./install.sh
```

This will:
- Make the `chat` script executable
- Write a `.desktop` entry to `~/.local/share/applications/streamerbot-chat.desktop` using the correct absolute path automatically
- Refresh the desktop database so the entry appears in your launcher immediately

You can then launch **StreamerBot Chat** from your application launcher like any other app, no terminal needed.

---

## Troubleshooting

**Grey/blank window on launch**
The `SingletonLock` cleanup in the script handles this automatically. If it still happens, delete the entire profile and let it rebuild:
```bash
rm -rf ~/.config/streamerbot-chat-profile
```

**Unsafe `file://` origin errors**
Open the overlay through `./chat`, not by opening `chat.html` directly in a browser or VS Code file preview. The launcher now serves the page over `http://127.0.0.1`, which avoids `file://` origin restrictions.

**Status stays "Connecting…" forever**
- Confirm Streamer.bot is running on the Windows machine.
- Confirm the WebSocket server in Streamer.bot is enabled and bound to the LAN IP (not `127.0.0.1`).
- Test connectivity from the Linux machine:
  ```bash
  nc -zv 10.0.0.95 8080
  ```
- Check that the Windows firewall allows inbound TCP on port 8080.

**Messages appear but are blank**
The payload structure from Streamer.bot changed. Open `chat.html`, add `onData: (raw) => console.log(raw)` to the `StreamerbotClient` constructor, relaunch, and inspect the browser console (right-click → Inspect) to see the raw payload shape. Then update `handleChatMessage` accordingly.

**"Opening in existing browser session" and nothing loads**
An existing browser window is running without `--user-data-dir`. The `SingletonLock` cleanup and `--user-data-dir` flag together prevent this. If it recurs, kill all Brave Nightly processes:
```bash
pkill brave-origin-nightly
```
Then relaunch with `./chat`.