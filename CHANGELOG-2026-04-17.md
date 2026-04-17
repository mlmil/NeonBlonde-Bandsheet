# Neon Blonde Band Sheet — Changelog
**Date:** April 17, 2026

---

## Session Summary

Full overhaul of the band sheet generator and supporting workflow.

---

## Changes Made

### Auth — Ripped Out, Replaced with ICS Feed
- Removed all Google OAuth / service account / go-google-mcp authentication
- Switched to public Google Calendar ICS feed (`/public/basic.ics`)
- No secrets, no tokens, no credentials required
- Calendar must remain set to public (already was)

### `generate_bandsheet.py` — Full Rewrite
- Replaced `google-api-python-client` with `requests` + `icalendar`
- Fetches events from `neonblondevc@gmail.com` public ICS feed
- Event parsing:
  - **Event title** = venue name
  - **Event location** = city
  - Combined display: `Venue, City` (deduplicates if location already contains venue name)
  - **Event times** = exact gig times, converted to Pacific Time
- Time format: `@8PM`, `@9:30PM` (no `:00` on the hour)
- Member outs detected by keywords: `out`, `unavailable`, `absent`, `blocked`, `vacation`, `off`
- Date range fix: single-day all-day events display correctly (exclusive end date handled)

### THIS WEEK Section
- Gigs and member outs merged and sorted chronologically together
- Was previously adding them separately (out of order)

### Weekend Days Open Section
- Was: SAT-SUN pairs through July only
- Now: Individual open Fridays, Saturdays, and Sundays through December 31
- Grouped by month in the HTML display with pink month headers

### `index.html`
- Added `addWeekendsByMonth()` function — groups open days under month headers
- Added `.month-header` CSS style (pink, subtle border)
- Renamed section from "Fully Free Weekends" → "Weekend Days Open"

### `requirements.txt`
- Removed: `google-auth`, `google-auth-oauthlib`, `google-auth-httplib2`, `google-api-python-client`
- Added: `requests==2.31.0`, `icalendar==5.0.12`

### `.github/workflows/bandsheet.yml`
- Removed all secret env vars (`SERVICE_ACCOUNT_JSON`, `NEON_TOKEN_JSON`, `NEON_CLIENT_SECRETS_JSON`)
- Workflow now runs with zero secrets

### `SETUP.md`
- Updated local project path from `/Volumes/VADER/Cowork Projects/neon-bandsheet` → `/Users/studio_hub/neon-bandsheet`

### Project Location
- Moved from `/Volumes/VADER/Cowork Projects/neon-bandsheet` → `/Users/studio_hub/neon-bandsheet`
- All files updated to reflect new path

---

## Repo
`https://github.com/mlmil/NeonBlonde-Bandsheet`

## Live URL
`https://mlmil.github.io/NeonBlonde-Bandsheet/`

## Schedule
Auto-updates daily at 6 AM PT via GitHub Actions cron.
