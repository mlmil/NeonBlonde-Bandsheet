#!/usr/bin/env python3
"""
Generate Neon Blonde Band Sheet from Google Calendar.
Fetches events from neonblondevc@gmail.com and outputs as JSON.
"""

import json
import sys
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import requests

# Configuration
CALENDAR_ID = "neonblondevc@gmail.com"
PT_TZ = ZoneInfo("America/Los_Angeles")

# Get token from environment (set by GitHub Actions)
TOKEN_JSON = os.environ.get("NEON_TOKEN_JSON")
CLIENT_SECRETS_JSON = os.environ.get("NEON_CLIENT_SECRETS_JSON")

if not TOKEN_JSON or not CLIENT_SECRETS_JSON:
    print("Error: NEON_TOKEN_JSON and NEON_CLIENT_SECRETS_JSON environment variables required")
    sys.exit(1)

try:
    token_data = json.loads(TOKEN_JSON)
    client_secrets = json.loads(CLIENT_SECRETS_JSON)
except json.JSONDecodeError as e:
    print(f"Error parsing JSON: {e}")
    sys.exit(1)


def refresh_access_token(token_data, client_secrets):
    """Refresh OAuth token using refresh_token."""
    client_id = client_secrets["installed"]["client_id"]
    client_secret = client_secrets["installed"]["client_secret"]
    refresh_token = token_data.get("refresh_token")

    if not refresh_token:
        print("Error: No refresh_token found")
        sys.exit(1)

    url = "https://oauth2.googleapis.com/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        new_token = response.json()
        token_data["access_token"] = new_token["access_token"]
        token_data["expires_in"] = new_token.get("expires_in", 3599)
        return token_data
    except requests.RequestException as e:
        print(f"Error refreshing token: {e}")
        sys.exit(1)


def get_calendar_events(access_token):
    """Fetch all future events from Neon Blonde calendar."""
    headers = {"Authorization": f"Bearer {access_token}"}

    # Get events from today onwards for the next 6 months
    today = datetime.now(PT_TZ).date()
    time_min = datetime.combine(today, datetime.min.time(), tzinfo=PT_TZ).isoformat()
    time_max = (datetime.now(PT_TZ) + timedelta(days=180)).isoformat()

    url = "https://www.googleapis.com/calendar/v3/calendars/neonblondevc@gmail.com/events"
    params = {
        "timeMin": time_min,
        "timeMax": time_max,
        "singleEvents": True,
        "orderBy": "startTime",
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get("items", [])
    except requests.RequestException as e:
        print(f"Error fetching calendar events: {e}")
        sys.exit(1)


def parse_events(events):
    """Separate gigs and member outs from calendar events."""
    gigs = []
    member_outs = {}

    member_out_keywords = {"out", "unavailable", "absent", "blocked", "vacation", "off"}

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
    # Refresh token if needed
    updated_token = refresh_access_token(token_data, client_secrets)
    access_token = updated_token["access_token"]

    # Fetch and parse calendar events
    events = get_calendar_events(access_token)
    gigs, member_outs = parse_events(events)

    # Generate Band Sheet
    bandsheet = generate_bandsheet(gigs, member_outs)

    # Write JSON data file
    with open("bandsheet-data.json", "w") as f:
        json.dump(bandsheet, f, indent=2)

    print("✓ Band Sheet generated successfully")
    print(f"  - {len(bandsheet['booked_gigs'])} gigs")
    print(f"  - {len(bandsheet['members_out'])} member outs")
    print(f"  - {len(bandsheet['free_weekends'])} free weekends")


if __name__ == "__main__":
    main()
