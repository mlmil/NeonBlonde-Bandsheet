# Neon Blonde Band Sheet

![Neon Blonde](neon-portrait-1.jpeg)

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

The bandsheet uses OAuth 2.0 to authenticate with Google Calendar API. The automation flow is entirely handled by GitHub Actions—no manual credential management required.

**Credentials workflow:**
- `generate_bandsheet.py` reads Base64-encoded OAuth credentials from `credentials.json`
- GitHub Actions keeps credentials secure via encrypted secrets
- The Python script pulls gig events and generates fresh JSON daily
- No credentials are stored or exposed in the deployed site

**To run locally:**
```bash
python3 generate_bandsheet.py
```

This regenerates `docs/bandsheet-data.json` and updates the live site on next GitHub Pages sync.

## Customization

The **Tweaks Panel** in the React app allows runtime adjustments:
- Font weight and sizing
- Neon color intensity and scheme
- Layout spacing and typography
- Display modes (compact, expanded, dark/light)

Tweaks are applied client-side and don't persist across page reloads (by design—the band can quickly experiment without committing changes).

## Notes

- The custom Overseer font is served from `docs/fonts/` and supports 4 weights (regular, italic, bold, bold italic)
- GitHub Actions runs on UTC schedule; times may differ from band's local timezone
- The React app is delivered as a single 17KB HTML file for fast loading and simple deployment
- `bandsheet-data.json` is the single source of truth for gig data on the live site

