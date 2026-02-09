<div align="center">
  <img src="logos/banner.png" alt="coral" width="100%">
</div>

# coral

monitor social accounts, track changes, get a timeline.

one app. instagram, pinterest, spotify. more later.

## what it does

you create identities (people), link their social accounts, and coral watches them. it checks on a schedule, diffs the data, and logs what changed — new followers, bio updates, new pins, unfollows. everything shows up on a timeline.

built-in username search powered by maigret scans hundreds of sites for matching profiles.

## install

```bash
curl -fsSL https://raw.githubusercontent.com/Sha-Dox/coral/main/install.sh | bash
```

or manually:

```bash
git clone https://github.com/Sha-Dox/coral.git
cd coral
pip install -r recoral/requirements.txt
cp .env.example .env
python3 recoral/app.py
```

open http://localhost:3456

## setup

### instagram

requires a logged-in instaloader session.

```bash
instaloader --login YOUR_USERNAME
```

then either set it globally in settings, or per-account when adding an instagram monitor.

### spotify

grab your `sp_dc` cookie from open.spotify.com (browser devtools → application → cookies). paste it in settings or per-account.

### pinterest

works out of the box. no auth needed.

## project structure

```
recoral/
├── app.py                flask app + blueprint registration
├── config.py             env-based config
├── database.py           sqlite operations
├── scheduler.py          apscheduler wrapper
├── maigret_search.py     username osint search
├── monitors/
│   ├── instagram.py      instaloader-based profile diffing
│   ├── pinterest.py      board/pin count tracking
│   └── spotify.py        sp_dc auth + spclient api
├── routes/
│   ├── pages.py          serves the spa
│   ├── identities.py     identity crud
│   ├── accounts.py       account crud
│   ├── events.py         activity timeline
│   ├── monitoring.py     check triggers + maigret
│   └── settings.py       app configuration
├── static/               css, js, images
└── templates/
    └── index.html         single-page app
```

## configuration

all via `.env` or the settings page in the ui.

| variable | default | description |
|---|---|---|
| `CORAL_PORT` | `3456` | server port |
| `CORAL_HOST` | `0.0.0.0` | bind address |
| `CORAL_CHECK_INTERVAL` | `300` | seconds between checks |
| `SP_DC_COOKIE` | | global spotify cookie |
| `INSTAGRAM_SESSION_FILE` | | global ig session username |

## api

```
GET  /api/identities              list identities
POST /api/identities              create identity
GET  /api/events                  activity timeline
POST /api/identities/:id/accounts link an account
POST /api/check-all               trigger all checks
POST /api/check/:account_id       check one account
POST /api/maigret/search          username search
GET  /api/settings                read settings
PUT  /api/settings                update settings
GET  /api/stats                   dashboard stats
```

## license

mit
