#!/usr/bin/env python3
"""
Generate Neon Blonde Band Sheet from public Google Calendar ICS feed.
No auth required — calendar is public.
Creates a receipt document in Google Drive showing what was generated.
"""

import json
import sys
import requests
from icalendar import Calendar
from datetime import datetime, timedelta, date, time
from zoneinfo import ZoneInfo
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
from google.auth import default
from google.api_core.exceptions import GoogleAPIError
from googleapiclient.discovery import build

# Load config
with open("config.json") as f:
    CONFIG = json.load(f)

CALENDAR_ID = CONFIG.get("calendar_id", "neonblondevc@gmail.com")
ICS_URL = f"https://calendar.google.com/calendar/ical/{CALENDAR_ID.replace('@', '%40')}/public/basic.ics"
PT_TZ = ZoneInfo("America/Los_Angeles")
DRIVE_FOLDER_ID = CONFIG.get("drive_folder_id")
CREDENTIALS_FILE = CONFIG.get("credentials_file", "credentials.json")

MEMBER_OUT_KEYWORDS = {"out", "unavailable", "absent", "blocked", "vacation", "off"}


def fetch_events():
    print(f"[INFO] Fetching ICS feed from Google Calendar...")
    resp = requests.get(ICS_URL, timeout=30)
    resp.raise_for_status()
    cal = Calendar.from_ical(resp.content)

    today = datetime.now(PT_TZ).date()
    year_end = date(today.year, 12, 31)
    events = []

    for component in cal.walk():
        if component.name != "VEVENT":
            continue

        summary = str(component.get("SUMMARY", "")).strip()
        location = str(component.get("LOCATION", "")).strip()

        dtstart = component.get("DTSTART").dt
        dtend = component.get("DTEND").dt

        # Normalize to date + optional time
        if isinstance(dtstart, datetime):
            dtstart = dtstart.astimezone(PT_TZ)
            start_date = dtstart.date()
            start_time = dtstart.time()
        else:
            start_date = dtstart
            start_time = None

        if isinstance(dtend, datetime):
            dtend = dtend.astimezone(PT_TZ)
            end_date = dtend.date()
        else:
            end_date = dtend

        if start_date < today or start_date > year_end:
            continue

        events.append({
            "summary": summary,
            "location": location,
            "start_date": start_date,
            "start_time": start_time,
            "end_date": end_date,
        })

    print(f"[OK] {len(events)} events loaded")
    return events


def parse_events(events):
    gigs = []
    member_outs = {}

    for e in events:
        title = e["summary"].lower()
        is_out = any(kw in title for kw in MEMBER_OUT_KEYWORDS)

        if is_out:
            name = e["summary"].split()[0].capitalize()
            if name not in member_outs:
                member_outs[name] = []
            member_outs[name].append((e["start_date"], e["end_date"]))
        else:
            venue = e["summary"]
            city = e["location"]
            # If location already contains the venue name, use it as-is
            if city and venue.lower() in city.lower():
                display = city
            else:
                display = f"{venue}, {city}" if city else venue
            gigs.append({
                "date": e["start_date"],
                "time": e["start_time"],
                "venue": display,
                "title": e["summary"],
            })

    gigs.sort(key=lambda x: (x["date"], x["time"] or time.min))
    return gigs, member_outs


def format_time(t):
    if not t:
        return None
    hour, minute = t.hour, t.minute
    period = "PM" if hour >= 12 else "AM"
    h = hour % 12 or 12
    return f"@{h}:{minute:02d}{period}" if minute else f"@{h}{period}"


def is_blocked(d, member_outs):
    return any(
        start <= d < end
        for dates in member_outs.values()
        for start, end in dates
    )


def generate_bandsheet(gigs, member_outs):
    today = datetime.now(PT_TZ).date()
    week_end = today + timedelta(days=7)
    year_end = date(today.year, 12, 31)

    # THIS WEEK
    this_week_raw = []
    for gig in gigs:
        if today <= gig["date"] < week_end:
            t = format_time(gig["time"])
            entry = f"{gig['date'].strftime('%A').upper()}{' ' + t if t else ''} {gig['venue']}"
            this_week_raw.append((gig["date"], gig["time"] or time.min, entry))

    for name, ranges in member_outs.items():
        for start, end in ranges:
            if today <= start < week_end:
                entry = f"{name.upper()} OUT {start.strftime('%A').upper()}"
                this_week_raw.append((start, time.min, entry))

    this_week_raw.sort(key=lambda x: (x[0], x[1]))
    this_week = [e[2] for e in this_week_raw]

    # BOOKED GIGS
    booked_gigs = []
    for gig in gigs:
        day = gig["date"].strftime("%a").upper()
        d = gig["date"].strftime("%-m-%-d-%Y")
        t = format_time(gig["time"])
        entry = f"{day} {d}{' ' + t if t else ''} — {gig['venue']}"
        booked_gigs.append(entry)

    # MEMBERS OUT
    members_out = []
    for name in sorted(member_outs):
        for start, end in sorted(member_outs[name]):
            ds = start.strftime("%a").upper()
            d1 = start.strftime("%-m-%-d-%Y")
            if (end - start).days <= 1:
                members_out.append(f"- {name}: {ds} {d1}")
            else:
                actual_end = end - timedelta(days=1)
                de = actual_end.strftime("%a").upper()
                d2 = actual_end.strftime("%-m-%-d-%Y")
                members_out.append(f"- {name}: {ds} {d1} to {de} {d2}")

    # WEEKEND DAYS OPEN
    weekend_days_open = []
    check = today
    gig_dates = {g["date"] for g in gigs}
    while check <= year_end:
        if check.weekday() in (4, 5, 6):  # Fri, Sat, Sun
            if check not in gig_dates and not is_blocked(check, member_outs):
                weekend_days_open.append(f"- {check.strftime('%a').upper()} {check.strftime('%B %-d')}")
        check += timedelta(days=1)

    return {
        "updated": datetime.now(PT_TZ).strftime("%B %d, %Y @ %-I:%M %p PT"),
        "this_week": this_week,
        "booked_gigs": booked_gigs,
        "members_out": members_out,
        "free_weekends": weekend_days_open,
    }


def create_drive_receipt(gigs):
    """Create a receipt document in each venue folder showing when it was published."""
    if not DRIVE_FOLDER_ID:
        print("[SKIP] No DRIVE_FOLDER_ID in config — skipping receipt creation")
        return

    try:
        # Try to load credentials from file
        try:
            creds = service_account.Credentials.from_service_account_file(
                CREDENTIALS_FILE,
                scopes=["https://www.googleapis.com/auth/drive"]
            )
            print("[INFO] Using service account credentials")
        except:
            # Fallback to default credentials (useful in GitHub Actions)
            creds, _ = default(scopes=["https://www.googleapis.com/auth/drive"])
            print("[INFO] Using default credentials")

        drive_service = build("drive", "v3", credentials=creds)
        timestamp = datetime.now(PT_TZ).strftime("%Y-%m-%d %H:%M:%S PT")

        # For each gig, find the matching venue folder and create a receipt
        for gig in gigs:
            venue = gig['venue']
            gig_date = gig['date']

            # Build folder name matching Google Apps Script format
            folder_name = f"{gig['title']} - {gig_date.strftime('%m/%d/%Y')}"

            try:
                # Search for the folder
                query = f"name = '{folder_name}' and '{DRIVE_FOLDER_ID}' in parents and trashed = false"
                results = drive_service.files().list(
                    q=query,
                    spaces='drive',
                    fields='files(id, name)',
                    pageSize=1
                ).execute()

                folders = results.get('files', [])
                if not folders:
                    print(f"[SKIP] Folder not found: {folder_name}")
                    continue

                folder_id = folders[0]['id']

                # Create receipt text for this gig
                receipt_text = f"""NEON BLONDE - BANDSHEET PUBLICATION RECEIPT

Event: {gig['title']}
Venue: {venue}
Date: {gig_date.strftime('%A, %B %d, %Y')}
Time: {gig['time'].strftime('%I:%M %p PT') if gig['time'] else 'Time TBD'}

Published to Bandsheet: {timestamp}
"""

                # Create the file in this venue's folder
                file_metadata = {
                    'name': f"Bandsheet Receipt {datetime.now(PT_TZ).strftime('%Y-%m-%d %H:%M')}",
                    'mimeType': 'text/plain',
                    'parents': [folder_id]
                }

                from io import BytesIO
                file_result = drive_service.files().create(
                    body=file_metadata,
                    media_body=BytesIO(receipt_text.encode('utf-8')),
                    fields='id, webViewLink'
                ).execute()

                print(f"[OK] Receipt created for {folder_name}")

            except Exception as e:
                print(f"[WARN] Failed to create receipt for {folder_name}: {e}")

    except Exception as e:
        print(f"[ERROR] Failed to authenticate with Drive: {e}")


def main():
    print("=" * 60)
    print("NEON BLONDE BAND SHEET GENERATOR")
    print("=" * 60)

    events = fetch_events()
    gigs, member_outs = parse_events(events)
    print(f"[DEBUG] {len(gigs)} gigs, {len(member_outs)} members with outs")

    bandsheet = generate_bandsheet(gigs, member_outs)

    with open("bandsheet-data.json", "w") as f:
        json.dump(bandsheet, f, indent=2)
    print("[OK] bandsheet-data.json written")

    print(f"\n  {len(bandsheet['booked_gigs'])} gigs")
    print(f"  {len(bandsheet['members_out'])} member outs")
    print(f"  {len(bandsheet['free_weekends'])} open weekend days")
    print(f"  Updated: {bandsheet['updated']}")

    # Create receipts in venue folders
    create_drive_receipt(gigs)


if __name__ == "__main__":
    main()
