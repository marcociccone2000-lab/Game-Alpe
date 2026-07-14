# 🏔️ Alpe Games

A fun community voting platform: upload funny moments, photos, challenges or stories,
let everyone vote with ⭐ 1–5, and the top-ranked event wins the 🍺.

Built entirely with **Python + Streamlit + SQLite + Pandas + Plotly** — no JavaScript,
no Node.js, nothing else to install besides Python.

---

## 1. What you need

- **Python 3.9 or newer** installed on your computer.
  - Windows/Mac: download from https://www.python.org/downloads/ and during install,
    tick the box **"Add Python to PATH"**.
  - To check you already have it, open a terminal and type: `python --version`

That's the only requirement. Everything else (Streamlit, Pandas, Plotly...) is
installed automatically in step 3 below.

---

## 2. Files in this folder

```
alpe_games/
├── app.py                 → the application (run this)
├── database.py            → database logic (do not run directly)
├── requirements.txt        → list of Python packages needed
├── .streamlit/config.toml  → colors/theme
├── uploads/                → uploaded photos are stored here automatically
└── README.md               → this file
```

When you run the app for the first time, it will automatically create a file
called `alpe_games.db` in this same folder — that is your database. No setup needed.

---

## 3. How to install (only once)

1. Unzip this folder anywhere on your computer, e.g. on your Desktop.
2. Open a terminal / command prompt **inside this folder**:
   - Windows: open the folder in File Explorer, click the address bar, type `cmd`, press Enter.
   - Mac: right-click the folder → "New Terminal at Folder" (or use Finder + Terminal `cd` command).
3. Install the required packages by running:

   ```
   pip install -r requirements.txt
   ```

   (On some systems you may need `pip3` instead of `pip`.)

---

## 4. How to run the app

From the same terminal, inside this folder, run:

```
streamlit run app.py
```

A browser tab will open automatically at `http://localhost:8501` with the app running.
If it doesn't open automatically, copy that address into your browser.

To stop the app, go back to the terminal window and press `Ctrl + C`.

---

## 5. Using Alpe Games

- **🏠 Home** — dashboard with totals, the current Beer Winner 🍺, and the Top 3 podium.
- **➕ Add Event** — upload a new funny moment (title, description, photo, author, date).
- **🖼️ Gallery** — browse all events as cards; click "View & Vote" to open one and rate it.
- **🏆 Leaderboard** — live ranking, top 3 highlighted with 🥇🥈🥉.
- **📊 Statistics** — totals, top 10, and Plotly charts (votes per event, ratings
  distribution, ranking performance).
- **🛠️ Admin** — edit/delete events, reset votes, reset the whole leaderboard, and
  export results to CSV. Default password: `alpe2026` (change it — see below).

### Voting rule

Each browser session can vote **once per event**. The vote is tied to a random
session ID generated when you open the app, so refreshing the page keeps you
recognized, but a brand-new browser/incognito session can vote again — there is
no login system, by design, to keep the app simple.

---

## 6. Changing the Admin password

Open `app.py` in any text editor, find this line near the top:

```python
ADMIN_PASSWORD = "alpe2026"
```

Change `"alpe2026"` to whatever password you want, save the file, and restart the app.

---

## 7. Backing up or resetting your data

- All events and votes live in `alpe_games.db` (a single SQLite file).
- All uploaded photos live in the `uploads/` folder.
- To fully reset the app, close it, delete `alpe_games.db` and empty the `uploads/`
  folder — a fresh database will be created next time you run the app. You can also
  do this from inside the app: **🛠️ Admin → Reset Votes → "Reset EVERYTHING"**.
- To back up, just copy `alpe_games.db` and the `uploads/` folder somewhere safe.

---

## 8. Running it for a group (same Wi-Fi network)

By default the app only runs on your own computer (`localhost`). If you want
friends on the same Wi-Fi to use it from their phones/laptops:

```
streamlit run app.py --server.address 0.0.0.0
```

Then share your computer's local IP address (e.g. `http://192.168.1.23:8501`)
with them. Everyone must stay on the same network.

Enjoy the games — and may the funniest moment win the 🍺!
