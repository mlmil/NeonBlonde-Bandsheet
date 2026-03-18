#!/usr/bin/env python3
"""
Generate Neon Blonde Band Sheet from Google Calendar.
Uses Google Calendar API with service account authentication.
"""

import json
import sys
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Configuration
CALENDAR_ID = "neonblondevc@gmail.com"
PT_TZ = ZoneInfo("America/Los_Angeles")
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def get_calendar_events():
    """Fetch all future events using Google Calendar API."""
    print("[INFO] Fetching calendar events using Google Calendar API...")

    # Load service account credentials from environment variable
    creds_json = os.environ.get("SERVICE_ACCOUNT_JSON")
    if not creds_json:
        print("ERROR: SERVICE_ACCOUNT_JSON environment variable not set")
        sys.exit(1)

    try:
        creds_dict = json.loads(creds_json)
        credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)

        service = build("calendar", "v3", credentials=credentials)

        today = datetime.now(PT_TZ).date()
        time_min = datetime.combine(today, datetime.min.time(), tzinfo=PT_TZ).isoformat()
        time_max = (datetime.now(PT_TZ) + timedelta(days=180)).isoformat()

        print(f"[DEBUG] Querying calendar {CALENDAR_ID} from {time_min} to {time_max}")

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
        print(f"ERROR: Failed to parse SERVICE_ACCOUNT_JSON: {e}")
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
            # Parse member availability event
            member_name = event.get("summary", "Unknown").split()[0]  # First word

            start = event.get("start", {})
            end = event.get("end", {})

            if "date" in start:
                # All-day event
                start_date = datetime.strptime(start["date"], "%Y-%m-%d").date()
                end_date = datetime.strptime(end["date"], "%Y-%m-%d").date()
            else:
                # Timed event
                start_dt = datetime.fromisoformat(start.get("dateTime", ""))
                end_dt = datetime.fromisoformat(end.get("dateTime", ""))
                start_date = start_dt.date()
                end_date = end_dt.date()

            if member_name not in member_outs:
                member_outs[member_name] = []
            member_outs[member_name].append((start_date, end_date))
        else:
            # Parse gig event
            start = event.get("start", {})
            location = event.get("location", "TBD")

            if "date" in start:
                # All-day event
                start_date = datetime.strptime(start["date"], "%Y-%m-%d").date()
                start_time = None
            else:
                # Timed event
                start_dt = datetime.fromisoformat(start.get("dateTime", ""))
                start_date = start_dt.date()
                start_time = start_dt.time()

            gigs.append({
                "date": start_date,
                "time": start_time,
                "venue": location,
                "title": event.get("summary", "Gig"),
            })

    return sorted(gigs, key=lambda x: (x["date"], x["time"] or "")), member_outs


def format_time_12h(time_obj):
    """Convert time object to 12-hour format with PM suffix."""
    if not time_obj:
        return None
    return time_obj.strftime("%-I:%M%p").replace("AM", "AM").replace("PM", "PM").lower().replace("am", "AM").replace("pm", "PM")


def generate_bandsheet(gigs, member_outs):
    """Generate Band Sheet sections."""
    today = datetime.now(PT_TZ).date()

    # THIS WEEK - next 7 days with events
    this_week_entries = []
    week_end = today + timedelta(days=7)

    for gig in gigs:
        if today <= gig["date"] < week_end:
            time_str = f"@ {format_time_12h(gig['time'])}" if gig["time"] else ""
            venue = gig["venue"].replace(", ", ", ").strip()
            entry = f"{gig['date'].strftime('%A').upper()} {time_str} {venue}".strip()
            this_week_entries.append(entry)

    for member_name, date_ranges in member_outs.items():
        for start_date, end_date in date_ranges:
            if today <= start_date < week_end:
                entry = f"{member_name.upper()} OUT {start_date.strftime('%A').upper()}"
                this_week_entries.append(entry)

    # BOOKED GIGS - all gigs with full details
    booked_gigs = []
    for gig in gigs:
        day_abbr = gig["date"].strftime("%a").upper()
        date_str = gig["date"].strftime("%-m-%-d-%Y")
        time_str = f"@ {format_time_12h(gig['time'])}" if gig["time"] else ""
        venue = gig["venue"].strip()
        entry = f"{day_abbr} {date_str} {time_str} — {venue}".replace("  ", " ")
        booked_gigs.append(entry)

    # MEMBERS OUT - all member unavailability
    members_out = []
    for member_name, date_ranges in sorted(member_outs.items()):
        for start_date, end_date in sorted(date_ranges):
            day_abbr_start = start_date.strftime("%a").upper()
            date_str_start = start_date.strftime("%-m-%-d-%Y")

            # Check if single day or range
            if (end_date - start_date).days <= 1:
                # Single day
                entry = f"- {member_name}: {day_abbr_start} {date_str_start}"
            else:
                # Range - subtract 1 from end to account for exclusive end date
                actual_end = end_date - timedelta(days=1)
                day_abbr_end = actual_end.strftime("%a").upper()
                date_str_end = actual_end.strftime("%-m-%-d-%Y")
                entry = f"- {member_name}: {day_abbr_start} {date_str_start} to {day_abbr_end} {date_str_end}"
            members_out.append(entry)

    # FULLY FREE WEEKENDS
    free_weekends = []
    check_date = today
    end_of_july = today.replace(month=7, day=31)
    for _ in range((end_of_july - today).days + 1):  # Check through end of July
        if check_date.weekday() == 5:  # Saturday
            sat_date = check_date
            sun_date = check_date + timedelta(days=1)

            # Check if both days are free of gigs
            sat_gigs = [g for g in gigs if g["date"] == sat_date]
            sun_gigs = [g for g in gigs if g["date"] == sun_date]

            # Check if any members are out
            sat_member_out = any(
                start <= sat_date < end for _, dates in member_outs.items() for start, end in dates
            )
            sun_member_out = any(
                start <= sun_date < end for _, dates in member_outs.items() for start, end in dates
            )

            if not sat_gigs and not sun_gigs and not sat_member_out and not sun_member_out:
                entry = f"- SAT-SUN {sat_date.strftime('%B %-d')}-{sun_date.strftime('%-d')}"
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
    """Main execution."""
    print("=" * 60)
    print("NEON BLONDE BAND SHEET GENERATOR")
    print("=" * 60)

    # Fetch calendar events
    print("\n[STEP 1] Fetching calendar events...")
    events = get_calendar_events()

    print("\n[STEP 2] Parsing events...")
    gigs, member_outs = parse_events(events)
    print(f"[DEBUG] Parsed {len(gigs)} gigs and {len(member_outs)} member outs")

    # Generate Band Sheet
    print("\n[STEP 3] Generating Band Sheet...")
    bandsheet = generate_bandsheet(gigs, member_outs)

    # Write JSON data file
    print("\n[STEP 4] Writing JSON file...")
    try:
        with open("bandsheet-data.json", "w") as f:
            json.dump(bandsheet, f, indent=2)
        print("[OK] bandsheet-data.json written successfully")
    except Exception as e:
        print(f"ERROR writing file: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✓ BAND SHEET GENERATED SUCCESSFULLY")
    print("=" * 60)
    print(f"  - {len(bandsheet['booked_gigs'])} gigs")
    print(f"  - {len(bandsheet['members_out'])} member outs")
    print(f"  - {len(bandsheet['free_weekends'])} free weekends")
    print(f"  - Updated: {bandsheet['updated']}")


if __name__ == "__main__":
    main()
