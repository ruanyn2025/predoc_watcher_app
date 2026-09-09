# Predoc Watcher

**English** · [中文](README.zh-CN.md)

A desktop app over three pre-doc / RA job boards: search them, star what interests you,
set reminders, and track your applications.

It fetches the boards itself and keeps a local database. No API key, no mailbox, no account.

| Source | Page |
|---|---|
| predoc.org | <https://www.predoc.org/opportunities> |
| NBER (internal) | <https://www.nber.org/career-resources/research-assistant-positions-nber> |
| NBER (external) | <https://www.nber.org/career-resources/research-assistant-positions-not-nber> |

> If you would rather just get one email a day and skip the interface, see
> [predoc-watcher-email](https://github.com/ruanyn2025/predoc-watcher-email).
> The two are independent; you can use either on its own.

## Install

Requires Python 3.9 or later ([download](https://www.python.org/downloads/); on Windows, tick
"Add Python to PATH" during setup).

```bash
git clone https://github.com/ruanyn2025/predoc_watcher_app.git
cd predoc_watcher_app
pip install -r requirements.txt
```

The window and tray were built and tested on Windows. On Mac and Linux you can run the
web-only version, described under "Web version only" below.

## Start it

Double-click `启动.bat`, or run `python desktop.py`.

The first start fetches all three boards and builds the local database, which takes a few seconds.

**Closing the window does not quit.** The X button hides it to the system tray and the app keeps
checking for new postings. Left-click the tray icon to bring the window back; right-click and
choose Exit to quit for real. Launching it again while it is running just brings the window back
rather than starting a second copy.

### Add it to the Start menu

```powershell
.\install_shortcut.ps1
```

```powershell
.\install_shortcut.ps1 -Desktop     # also put a shortcut on the desktop
.\install_shortcut.ps1 -Startup     # also start on login, minimised to the tray
.\install_shortcut.ps1 -Uninstall   # remove them all
```

### Choosing a Python interpreter

By default the launcher uses `pythonw` from PATH, which is usually all you need. You only have to
set this if your Python lives in a conda environment or a virtualenv and is not on PATH. Three
ways, in order of precedence:

| Method | What to do |
|---|---|
| Environment variable | Set `PREDOC_PYTHON` to the full path of the interpreter |
| `python_path.txt` | Create this file in the project folder with the full path on one line |
| PATH | Do nothing |

With a virtualenv:

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

Then put the interpreter path in `python_path.txt`. Use `pythonw.exe` to avoid a console window
flashing on startup:

```
C:\full\path\.venv\Scripts\pythonw.exe
```

Activating the virtualenv and then double-clicking the launcher does not work: double-clicking
starts a new process that does not inherit the environment you activated in a terminal, so the
path has to be written down.

### What it does in the background

It fetches once at startup, again when you hide it to the tray, and every 6 hours after that.
A tray notification appears when new postings turn up.

### Web version only

If you do not want the window and tray, run `app.py` and open <http://127.0.0.1:8765/> in a
browser:

```bash
python app.py
```

That path does not need pywebview or pystray installed.

## The five pages

**New** — postings that appeared since you last hit "Mark all read", grouped by the date they were
found. Reminders due in the next 7 days sit at the top, turning red inside 3 days.

**All Jobs** — everything, including delisted postings. The search box matches fields,
researchers, institutions and titles at once; several space-separated words must all match, so
`labor harvard` finds postings matching both the field and the institution. You can also filter by
source and by whether a posting is still open.

**Starred** — press the star to save a posting; the list is sorted by reminder date. The **Edit**
button on each card changes the reminder date and the note. Pressing a lit star unstars.

**Applications** — pressing "Applied" on a starred posting moves it here. For each one you can:

- Set the **stage**: Applied / Test / Interview / Closed. The page groups by stage and folds
  Closed ones to the bottom.
- Record **several named dates**, such as "code test due 9/18" or "first interview 9/25 10:00".
- Add **notes** and **links**. Links can be given your own label and open in your browser.
- See the date you applied and how long ago that was.

Dates, notes and links are available on the Starred page too, for postings you have not applied to
yet. Moving an application back to Starred keeps everything you wrote.

**Calendar** — a month view of every reminder and application date. Dates within 7 days are shown
solid, later ones tinted. Hovering a mark shows the institution and researchers; clicking it jumps
back to the card on Starred or Applications.

## The reminder date when you star something

Starring opens a panel asking you to confirm a reminder date. This is because the deadline field on
the job boards is unreliable: over half the postings do not have one at all, and those that do are
often rolling, missing the year, or already past.

The panel shows the original deadline text and prefills a date: the parsed date if one could be
read and it is in the future, otherwise 7 days out. Adjust it with the shortcut buttons or by
editing the date directly. Enter confirms, Esc cancels.

## Appearance and language

Two buttons at the top right: the half-filled circle switches theme, the globe switches language.

Themes are System, Light and Dark. Languages are 简体中文, 繁體中文, English, Français and Español.
Both choices are stored locally and kept for next time.

The two kinds of calendar mark can be recoloured: click the small swatch in the legend at the
bottom to pick from seven presets, use the eyedropper, or type a hex value.

## Commands

| Command | What it does |
|---|---|
| `python desktop.py` | Normal start |
| `python desktop.py --minimized` | Start hidden in the tray |
| `python desktop.py --interval 6` | Hours between background checks, 6 by default |
| `python desktop.py --no-fetch` | Do not fetch at startup |
| `python desktop.py --port 8000` | Use a different port |
| `python app.py` | Web version only |

## Troubleshooting

**The page will not open.** Port 8765 may be taken; use another one:
`python app.py --port 8000`.

**It says a source failed.** An occasional failure is usually a network problem; that source's
postings are kept as they were and are not wrongly marked as delisted. If it happens repeatedly,
the site has probably changed and the parsing code needs updating.

**CERTIFICATE_VERIFY_FAILED.** predoc.org's server omits an intermediate certificate.
`extra_ca/gdig2.pem` is that certificate; the app merges it in at runtime, with verification left
fully on. If the file is missing or damaged, clone the repository again.

**Starting over.** Deleting `jobs.db` rebuilds the database on the next start, but your stars,
reminders and applications go with it.

## Files

```
desktop.py            desktop shell: window and system tray
app.py                web server
fetch.py              fetches and parses the three boards
db.py                 database schema and queries
ingest.py             writes fetch results into the database
deadlines.py          deadline parsing
i18n.py               interface text, five languages
calcolors.py          derives the calendar colours
make_icon.py          generates the icon
install_shortcut.ps1  installs the Start menu shortcut
templates/            page templates
static/               styles and front-end scripts
extra_ca/gdig2.pem    the intermediate certificate predoc.org omits
app.ico               application icon
jobs.db               your data: postings, stars, reminders, applications
python_path.txt       your interpreter path (optional)
启动.bat              double-click to start
```

`jobs.db` and `python_path.txt` are in `.gitignore` and will not be committed.

## Limits

- The boards do not publish a posting date, so "Found" on each card is the date this app first saw
  the posting.
- History accrues from the day you first run it; earlier postings cannot be recovered.
- Everything found on the first run is recorded as pre-existing and does not count as new.
- The window and tray have only been tested on Windows.

## License

MIT, see [LICENSE](LICENSE).
