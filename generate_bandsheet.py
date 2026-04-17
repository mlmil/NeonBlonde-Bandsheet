#!/usr/bin/env python3
"""
Generate Neon Blonde Band Sheet from Google Calendar.
Uses OAuth2 credentials (NEON_TOKEN_JSON env var).
"""

import json
import sys
import os
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Configuration
CALENDAR_ID = "neonblondevc@gmail.com"
PT_TZ = ZoneInfo("America/Los_Angeles")
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def get_calendar_events():
    """Fetch all future events using Google Calendar API (OAuth2)."""
    print("[INFO] Fetching calendar events using OAuth2...")

    token_json = os.environ.get("NEON_TOKEN_JSON")
    if not token_json:
        print("ERROR: NEON_TOKEN_JSON environment variable not set")
        sys.exit(1)

    try:
        token_data = json.loads(token_json)
        creds = Credentials(
            token=token_data.get("access_token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=token_data.get("client_id"),
            client_secret=token_data.get("client_secret"),
            scopes=SCOPES,
        )

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            print("[INFO] OAuth token refreshed")

        service = build("calendar", "v3", credentials=creds)

        today = datetime.now(PT_TZ).date()
        time_min = datetime.combine(today, datetime.min.time(), tzinfo=PT_TZ).isoformat()
        # Fetch through end of year
        year_end = date(today.year, 12, 31)
        time_max = datetime.combine(year_end, datetime.max.time(), tzinfo=PT_TZ).isoformat()

        print(f"[DEBUG] Querying {CALENDAR_ID} from {today} to {year_end}")

        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        items = events_result.get("items", [])
        print(f"[OK] Retrieved {len(items)} events")
        return items

    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse NEON_TOKEN_JSON: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def parse_events(events):
    """Separate gigs and member outs from calendar events."""
    gigs = []
    member_outs = {}

    member_out_keywords = {"out", "unavailable", "absent", "blocked", "vacation", "off", "birthday"}

    for event in events:
        title = event.get("summary", "").lower()
        is_member_out = any(keyword in title for keyword in member_out_keywords)

        if is_member_out:
            member_name = event.get("summary", "Unknown").split()[0].capitalize()

            start = event.get("start", {})
            end = event.get("end", {})

            if "date" in start:
                start_date = datetime.strptime(start["date"], "%Y-%m-%d").date()
                end_date = datetime.strptime(end["date"], "%Y-%m-%d").date()
            else:
                start_dt = datetime.fromisoformat(start.get("dateTime", ""))
                end_dt = datetime.fromisoformat(end.get("dateTime", ""))
                start_date = start_dt.astimezone(PT_TZ).date()
                end_date = end_dt.astimezone(PT_TZ).date()

            if member_name not in member_outs:
                member_outs[member_name] = []
            member_outs[member_name].append((start_date, end_date))
        else:
            start = event.get("start", {})
            location = event.get("location", "TBD")

            if "date" in start:
                start_date = datetime.strptime(start["date"], "%Y-%m-%d").date()
                start_time = None
            else:
                start_dt = datetime.fromisoformat(start.get("dateTime", "")).astimezone(PT_TZ)
                start_date = start_dt.date()
                start_time = start_dt.time()

            gigs.append({
                "date": start_date,
                "time": start_time,
                "venue": location,
                "title": event.get("summary", "Gig"),
            })

    return sorted(gigs, key=lambda x: (x["date"], x["time"] or datetime.min.time())), member_outs


def format_time(time_obj):
    """Convert time to band sheet format: @8PM or @9:30PM."""
    if not time_obj:
        return None
    hour = time_obj.hour
    minute = time_obj.minute
    period = "PM" if hour >= 12 else "AM"
    hour12 = hour % 12 or 12
    if minute:
        return f"@{hour12}:{minute:02d}{period}"
    return f"@{hour12}{period}"


def generate_bandsheet(gigs, member_outs):
    """Generate Band Sheet sections."""
    today = datetime.now(PT_TZ).date()
    week_end = today + timedelta(days=7)

    # THIS WEEK — collect all days with events, sort chronologically
    this_week_raw = []

    for gig in gigs:
        if today <= gig["date"] < week_end:
            t = format_time(gig["time"])
            time_str = f" {t}" if t else ""
            venue = gig["venue"].strip()
            entry = f"{gig['date'].strftime('%A').upper()}{time_str} {venue}"
            sort_time = gig["time"] or datetime.min.time()
            this_week_raw.append((gig["date"], sort_time, entry))

    for member_name, date_ranges in member_outs.items():
        for start_date, end_date in date_ranges:
            if today <= start_date < week_end:
                entry = f"{member_name.upper()} OUT {start_date.strftime('%A').upper()}"
                this_week_raw.append((start_date, datetime.min.time(), entry))

    this_week_raw.sort(key=lambda x: (x[0], x[1]))
    this_week_entries = [e[2] for e in this_week_raw]

    # BOOKED GIGS
    booked_gigs = []
    for gig in gigs:
        day_abbr = gig["date"].strftime("%a").upper()
        date_str = gig["date"].strftime("%-m-%-d-%Y")
        t = format_time(gig["time"])
        time_str = f" {t}" if t else ""
        venue = gig["venue"].strip()
        entry = f"{day_abbr} {date_str}{time_str} — {venue}"
        booked_gigs.append(entry)

    # MEMBERS OUT
    members_out = []
    for member_name in sorted(member_outs.keys()):
        for start_date, end_date in sorted(member_outs[member_name]):
            day_start = start_date.strftime("%a").upper()
            date_start = start_date.strftime("%-m-%-d-%Y")

            if (end_date - start_date).days <= 1:
                entry = f"- {member_name}: {day_start} {date_start}"
            else:
                actual_end = end_date - timedelta(days=1)
                day_end = actual_end.strftime("%a").upper()
                date_end = actual_end.strftime("%-m-%-d-%Y")
                entry = f"- {member_name}: {day_start} {date_start} to {day_end} {date_end}"
            members_out.append(entry)

    # FULLY FREE WEEKENDS (FRI-SAT) — through end of year
    free_weekends = []
    year_end = date(today.year, 12, 31)
    check_date = today
    while check_date <= year_end:
        if check_date.weekday() == 4:  # Friday
            fri_date = check_date
            sat_date = check_date + timedelta(days=1)

            fri_gigs = [g for g in gigs if g["date"] == fri_date]
            sat_gigs = [g for g in gigs if g["date"] == sat_date]

            fri_blocked = any(
                start <= fri_date < end
                for dates in member_outs.values()
                for start, end in dates
            )
            sat_blocked = any(
                start <= sat_date < end
                for dates in member_outs.values()
                for start, end in dates
            )

            if not fri_gigs and not sat_gigs and not fri_blocked and not sat_blocked:
                entry = f"- FRI-SAT {fri_date.strftime('%B %-d')}-{sat_date.strftime('%-d')}"
                free_weekends.append(entry)

        check_date += timedelta(days=1)

    return {
        "updated": datetime.now(PT_TZ).strftime("%B %d, %Y @ %-I:%M %p PT"),
        "this_week": this_week_entries,
        "booked_gigs": booked_gigs,
        "members_out": members_out,
        "free_weekends": free_weekends,
    }


def main():
    print("=" * 60)
    print("NEON BLONDE BAND SHEET GENERATOR")
    print("=" * 60)

    print("\n[STEP 1] Fetching calendar events...")
    events = get_calendar_events()

    print("\n[STEP 2] Parsing events...")
    gigs, member_outs = parse_events(events)
    print(f"[DEBUG] {len(gigs)} gigs, {len(member_outs)} members with outs")

    print("\n[STEP 3] Generating Band Sheet...")
    bandsheet = generate_bandsheet(gigs, member_outs)

    print("\n[STEP 4] Writing JSON file...")
    try:
        with open("bandsheet-data.json", "w") as f:
            json.dump(bandsheet, f, indent=2)
        print("[OK] bandsheet-data.json written")
    except Exception as e:
        print(f"ERROR writing file: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("BAND SHEET GENERATED")
    print("=" * 60)
    print(f"  {len(bandsheet['booked_gigs'])} gigs")
    print(f"  {len(bandsheet['members_out'])} member outs")
    print(f"  {len(bandsheet['free_weekends'])} free weekends")
    print(f"  Updated: {bandsheet['updated']}")


if __name__ == "__main__":
    main()
