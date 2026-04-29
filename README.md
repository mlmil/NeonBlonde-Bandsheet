# Neon Blonde Band Sheet

**Real-time gig schedule for Neon Blonde, the 6-piece 80s cover band.**

The bandsheet is a live, auto-updating interface that pulls gig data from the band's master schedule and presents it with a dark-mode 80s aesthetic. Built with React and deployed via GitHub Pages.

## What It Does

- Fetches upcoming gigs from the band's Google Calendar
- Displays the next gig with venue, date, time, and notes
- Maintains a historical log of completed gigs
- Updates automatically every day at 2 PM UTC (via GitHub Actions)
- Styled with neon colors (cyan, pink, yellow) and the custom Overseer font

## Stack

- **Frontend:** React 18.3.1 (CDN-delivered, single-file HTML)
- **Data Source:** Google Calendar API
- **Data Format:** JSON (bandsheet-data.json)
- **Hosting:** GitHub Pages (/docs directory)
- **Automation:** GitHub Actions (daily updates, OAuth credential management)
- **Typography:** Custom Overseer font (4 weights)

## How It Works

1. **Daily Update Cycle** — GitHub Actions runs `generate_bandsheet.py` at 2 PM UTC
2. **Calendar Fetch** — Pulls events from the master gig schedule
3. **JSON Generation** — Creates bandsheet-data.json with formatted gig data
4. **GitHub Pages Sync** — Copies data to /docs for live deployment
5. **Live Site** — React app loads data and renders the interface

## Files

```
NeonBlonde-Bandsheet/
├── docs/
│   ├── index.html              # Redesigned React-based interface
│   ├── tweaks-panel.jsx        # Customization UI component
│   ├── bandsheet-data.json     # Current gig data
│   └── fonts/                  # Custom Overseer typeface
├── .github/workflows/
│   └── bandsheet.yml           # CI/CD pipeline
├── generate_bandsheet.py       # Calendar → JSON generator
├── _config.yml                 # GitHub Pages configuration
└── credentials.json            # OAuth credentials (gitignored)
```

## Live Site

**https://mlmil.github.io/NeonBlonde-Bandsheet/**

## Setup

OAuth credentials are stored as Base64-encoded secrets in GitHub Actions. The workflow:
1. Decodes the token from `NEON_BLONDE_OAUTH_TOKEN_B64`
2. Authenticates to Google Calendar
3. Fetches events from the master schedule
4. Generates JSON and deploys

Credentials are protected via `.gitignore`; they never commit to the repo.

## Customization

The tweaks panel (tweaks-panel.jsx) allows runtime adjustments:
- Color schemes
- Font sizing
- Layout preferences
- Display filters

## Notes

- All dates/times are in the band's local timezone
- Completed gigs remain in the log for historical reference
- The workflow runs daily; manual updates via GitHub Actions "Run workflow" button
- GitHub Pages rebuilds automatically after each push

---

*Neon Blonde musical direction by Mike Miller • Bandsheet automation by Claude*
