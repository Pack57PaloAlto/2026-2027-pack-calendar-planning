#!/usr/bin/env python3
"""
Build script: Convert all YAML calendar files into a single events.json
for the FullCalendar interactive calendar view.

Usage:
    python3 scripts/build-calendar-json.py

Output:
    docs/events.json — array of FullCalendar event objects
"""

import json
import os
import sys
from datetime import date, datetime, timedelta

import yaml

# Project root
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF_DIR = os.path.join(ROOT, "reference-calendars")
PACK_DIR = os.path.join(ROOT, "pack-calendar")
OUT_DIR = os.path.join(ROOT, "docs")

# FullCalendar event colors per calendar source
# Pack = blue shades, Council = purple, Schools = green shades,
# Religious = red shades, Federal = red
COLORS = {
    # Pack events — blues
    "pack_meeting":     {"color": "#1a73e8", "textColor": "#fff"},   # blue
    "pack_committee":   {"color": "#4285f4", "textColor": "#fff"},   # lighter blue
    "pack_special":     {"color": "#1565c0", "textColor": "#fff"},   # dark blue
    "pack_camping":     {"color": "#0d47a1", "textColor": "#fff"},   # deeper blue
    "pack_conflict":    {"color": "#e8710a", "textColor": "#fff"},   # orange
    "den_meeting":      {"color": "#fbc02d", "textColor": "#000"},   # yellow
    # BSA Council — purples
    "council":          {"color": "#7b1fa2", "textColor": "#fff"},   # purple
    "training":         {"color": "#9c27b0", "textColor": "#fff"},   # lighter purple
    # School calendars — greens
    "pausd":            {"color": "#2e7d32", "textColor": "#fff"},   # green
    "hausner":          {"color": "#388e3c", "textColor": "#fff"},   # medium green
    "jcc":              {"color": "#43a047", "textColor": "#fff"},   # lighter green
    "emerson":          {"color": "#4caf50", "textColor": "#fff"},   # green
    "nueva":            {"color": "#66bb6a", "textColor": "#fff"},   # light green
    "keys":             {"color": "#1b5e20", "textColor": "#fff"},   # dark green
    "st_raymond":       {"color": "#81c784", "textColor": "#000"},   # pale green
    # Religious holidays — reds
    "jewish":           {"color": "#c62828", "textColor": "#fff"},   # dark red
    "islamic":          {"color": "#d32f2f", "textColor": "#fff"},   # red
    "christian":        {"color": "#e53935", "textColor": "#fff"},   # medium red
    "hindu":            {"color": "#ef5350", "textColor": "#fff"},   # light red
    # Federal holidays — red
    "us_federal":       {"color": "#b71c1c", "textColor": "#fff"},   # deepest red
}


def to_date_str(d):
    """Convert a date/datetime/string to 'YYYY-MM-DD'."""
    if isinstance(d, (date, datetime)):
        return d.strftime("%Y-%m-%d")
    return str(d)[:10]


def make_event(title, start, end=None, calendar="pack_meeting", description="", all_day=True):
    """Create a FullCalendar event dict."""
    colors = COLORS.get(calendar, {"color": "#999", "textColor": "#fff"})
    evt = {
        "title": title,
        "start": to_date_str(start),
        "allDay": all_day,
        "calendar": calendar,
        **colors,
    }
    if end:
        # FullCalendar exclusive end date — add 1 day for multi-day
        end_d = to_date_str(end)
        if end_d != evt["start"]:
            # Add 1 day because FullCalendar end is exclusive
            end_dt = datetime.strptime(end_d, "%Y-%m-%d") + timedelta(days=1)
            evt["end"] = end_dt.strftime("%Y-%m-%d")
    if description:
        evt["description"] = description
    return evt


def parse_pack_proposal():
    """Parse the pack calendar proposal YAML."""
    events = []
    path = os.path.join(PACK_DIR, "pack57-2026-27-proposal.yaml")
    with open(path) as f:
        data = yaml.safe_load(f)

    months = ["september", "october", "november", "december",
              "january", "february", "march", "april", "may"]

    for month in months:
        if month not in data:
            continue
        for item in data[month]:
            d = item.get("date")
            if not d:
                continue
            t = item.get("type", "")
            title = item.get("event", "")
            notes = item.get("notes", "")
            time_str = item.get("time", "")

            if t == "pack_meeting":
                cal = "pack_meeting"
            elif t == "pack_committee":
                cal = "pack_committee"
            elif t == "camping":
                cal = "pack_camping"
            elif t == "special_event":
                cal = "pack_special"
            elif t == "service_project":
                cal = "pack_special"
            elif t in ("council_event", "district_event"):
                cal = "council"
            elif t in ("conflict", "cultural_note"):
                cal = "pack_conflict"
            else:
                cal = "pack_special"

            desc = ""
            if time_str:
                desc += f"{time_str}. "
            if isinstance(notes, str) and notes.strip():
                desc += notes.strip()[:200]

            events.append(make_event(title, d, description=desc, calendar=cal))

    # Training dates
    if "training" in data:
        for item in data["training"]:
            d = item.get("date")
            if d:
                events.append(make_event(
                    item.get("event", "Training"),
                    d,
                    description=item.get("notes", ""),
                    calendar="training"
                ))

    return events


def parse_pausd():
    """Parse PAUSD calendar."""
    events = []
    path = os.path.join(REF_DIR, "pausd-2026-27.yaml")
    with open(path) as f:
        data = yaml.safe_load(f)

    for item in data.get("holidays_and_breaks", []):
        if "date" in item:
            events.append(make_event(
                f"PAUSD: {item['description']}",
                item["date"],
                calendar="pausd"
            ))
        elif "start" in item and "end" in item:
            events.append(make_event(
                f"PAUSD: {item['description']}",
                item["start"],
                end=item["end"],
                calendar="pausd"
            ))
        elif "dates" in item:
            dates = item["dates"]
            if len(dates) > 1:
                events.append(make_event(
                    f"PAUSD: {item['description']}",
                    dates[0],
                    end=dates[-1],
                    calendar="pausd"
                ))
            else:
                events.append(make_event(
                    f"PAUSD: {item['description']}",
                    dates[0],
                    calendar="pausd"
                ))

    for item in data.get("staff_days", []):
        if "date" in item:
            events.append(make_event(
                f"PAUSD: {item['description']}",
                item["date"],
                calendar="pausd"
            ))

    return events


def parse_hausner():
    """Parse Hausner calendar."""
    events = []
    path = os.path.join(REF_DIR, "hausner-2026-27.yaml")
    if not os.path.exists(path):
        return events
    with open(path) as f:
        data = yaml.safe_load(f)

    # Look for holidays_and_breaks, no_school, closures, etc.
    for key in ["holidays_and_breaks", "no_school_days", "closures", "breaks"]:
        if key not in data:
            continue
        items = data[key]
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    d = item.get("date") or item.get("start")
                    end = item.get("end")
                    desc = item.get("description", item.get("event", "No school"))
                    if d:
                        events.append(make_event(f"Hausner: {desc}", d, end=end, calendar="hausner"))
                elif isinstance(item, str):
                    # Plain date string
                    events.append(make_event("Hausner: No school", item, calendar="hausner"))

    return events


def parse_jcc():
    """Parse JCC closures."""
    events = []
    path = os.path.join(REF_DIR, "jcc-paloalto-2026.yaml")
    with open(path) as f:
        data = yaml.safe_load(f)

    for item in data.get("complete_closures", []):
        if "date" in item:
            events.append(make_event(
                f"JCC Closed: {item['description']}",
                item["date"],
                calendar="jcc"
            ))
    for item in data.get("admin_closures", []):
        if "date" in item:
            events.append(make_event(
                f"JCC Admin Closed: {item['description']}",
                item["date"],
                calendar="jcc"
            ))
        elif "dates" in item:
            for d in item["dates"]:
                events.append(make_event(
                    f"JCC Admin Closed: {item['description']}",
                    d,
                    calendar="jcc"
                ))

    return events


def parse_school_generic(filename, calendar_key, label):
    """Generic parser for school calendars with flexible structure."""
    events = []
    path = os.path.join(REF_DIR, filename)
    if not os.path.exists(path):
        return events
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"  Warning: Could not parse {filename}: {e}")
        return events

    if not data:
        return events

    # Try multiple possible key names for holidays/breaks
    for key in ["holidays_and_breaks", "estimated_holidays_and_breaks",
                "no_school_days", "closures", "breaks",
                "catholic_holy_days_no_school", "known_events"]:
        section = data.get(key)
        if not section:
            continue
        # If it's a dict with a nested list or note, skip non-list
        if isinstance(section, dict):
            continue
        if not isinstance(section, list):
            continue
        for item in section:
            if not isinstance(item, dict):
                continue
            d = item.get("date") or item.get("start")
            end = item.get("end")
            desc = item.get("description", item.get("event", "No school"))
            # Skip entries with approximate dates (start with ~)
            if d and str(d).startswith("~"):
                continue
            if end and str(end).startswith("~"):
                end = None
            if d:
                events.append(make_event(
                    f"{label}: {desc}", d, end=end, calendar=calendar_key
                ))
            # Handle "dates" array format (like St. Raymond)
            if "dates" in item:
                dates = item["dates"]
                if isinstance(dates, list) and len(dates) > 0:
                    # Check for approximate dates
                    clean_dates = [dd for dd in dates if not str(dd).startswith("~")]
                    if len(clean_dates) > 1:
                        events.append(make_event(
                            f"{label}: {desc}",
                            clean_dates[0], end=clean_dates[-1],
                            calendar=calendar_key
                        ))
                    elif len(clean_dates) == 1:
                        events.append(make_event(
                            f"{label}: {desc}",
                            clean_dates[0], calendar=calendar_key
                        ))

    # Also parse early_release_days if present
    for d in data.get("early_release_days", []):
        if d and not str(d).startswith("~"):
            events.append(make_event(
                f"{label}: Early Release", d, calendar=calendar_key
            ))

    return events


def parse_religious_calendar(filename, calendar_key, label):
    """Generic parser for religious holiday YAML files."""
    events = []
    path = os.path.join(REF_DIR, filename)
    if not os.path.exists(path):
        return events
    with open(path) as f:
        data = yaml.safe_load(f)

    # Try pack_season first (most relevant), then year_2026/year_2027
    for section_key in ["pack_season", "year_2026", "year_2027"]:
        section = data.get(section_key, [])
        if not isinstance(section, list):
            continue
        for item in section:
            if not isinstance(item, dict):
                continue
            d = item.get("date")
            if not d:
                continue
            holiday = item.get("holiday", item.get("event", "Holiday"))
            duration = item.get("duration", "")
            significance = item.get("significance", "")

            desc = significance[:150] if significance else ""
            if duration:
                desc = f"{duration}. {desc}"

            events.append(make_event(
                f"{label}: {holiday}",
                d,
                description=desc,
                calendar=calendar_key
            ))

    return events


def parse_us_federal():
    """Parse US federal holidays."""
    events = []
    path = os.path.join(REF_DIR, "us-federal-holidays-2026-27.yaml")
    if not os.path.exists(path):
        return events
    with open(path) as f:
        data = yaml.safe_load(f)

    for year_key in ["year_2026", "year_2027"]:
        section = data.get(year_key, [])
        if not isinstance(section, list):
            continue
        for item in section:
            if not isinstance(item, dict):
                continue
            d = item.get("date")
            holiday = item.get("holiday", "Federal Holiday")
            if d:
                events.append(make_event(
                    f"🇺🇸 {holiday}",
                    d,
                    calendar="us_federal"
                ))

    return events


def parse_council():
    """Parse Pacific Skyline Council events."""
    events = []
    path = os.path.join(REF_DIR, "pacific-skyline-council-2026-27.yaml")
    if not os.path.exists(path):
        return events
    with open(path) as f:
        data = yaml.safe_load(f)

    for item in data.get("events", []):
        if not isinstance(item, dict):
            continue
        d = item.get("date")
        if not d:
            continue
        evt_name = item.get("event", "Council Event")
        loc = item.get("location", "")
        notes = item.get("notes", "")
        t = item.get("type", "")

        desc = ""
        if loc:
            desc += f"📍 {loc}. "
        if notes:
            desc += str(notes)[:150]

        # Skip holidays (already in US Federal)
        if t == "holiday":
            continue

        events.append(make_event(
            f"PacSky: {evt_name}",
            d,
            description=desc,
            calendar="council"
        ))

    return events


def deduplicate(events):
    """Remove near-duplicate events (same date + similar title)."""
    seen = set()
    unique = []
    for e in events:
        key = (e["start"], e["title"][:30])
        if key not in seen:
            seen.add(key)
            unique.append(e)
    return unique


def main():
    all_events = []

    print("Parsing pack proposal...")
    all_events.extend(parse_pack_proposal())

    print("Parsing PAUSD calendar...")
    all_events.extend(parse_pausd())

    print("Parsing Hausner calendar...")
    all_events.extend(parse_hausner())

    print("Parsing JCC closures...")
    all_events.extend(parse_jcc())

    print("Parsing Emerson Montessori calendar...")
    all_events.extend(parse_school_generic(
        "emerson-montessori-2025-26.yaml", "emerson", "Emerson"))

    print("Parsing Nueva School calendar...")
    all_events.extend(parse_school_generic(
        "nueva-2026-27.yaml", "nueva", "Nueva"))

    print("Parsing Keys School calendar...")
    all_events.extend(parse_school_generic(
        "keys-2026-27.yaml", "keys", "Keys"))

    print("Parsing St. Raymond calendar...")
    all_events.extend(parse_school_generic(
        "st-raymond-2026-27.yaml", "st_raymond", "St. Raymond"))

    print("Parsing Jewish holidays...")
    all_events.extend(parse_religious_calendar(
        "jewish-holidays-2026-27.yaml", "jewish", "✡️ Jewish"))

    print("Parsing Islamic holidays...")
    all_events.extend(parse_religious_calendar(
        "islamic-holidays-2026-27.yaml", "islamic", "☪️ Islamic"))

    print("Parsing Christian holidays...")
    all_events.extend(parse_religious_calendar(
        "christian-holidays-2026-27.yaml", "christian", "✝️ Christian"))

    print("Parsing Hindu holidays...")
    all_events.extend(parse_religious_calendar(
        "hindu-holidays-2026-27.yaml", "hindu", "🕉️ Hindu"))

    print("Parsing US federal holidays...")
    all_events.extend(parse_us_federal())

    print("Parsing PacSky council events...")
    all_events.extend(parse_council())

    # Deduplicate
    all_events = deduplicate(all_events)

    # Sort by start date
    all_events.sort(key=lambda e: e["start"])

    # Write output
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, "events.json")
    with open(out_path, "w") as f:
        json.dump(all_events, f, indent=2, default=str)

    print(f"\nWrote {len(all_events)} events to {out_path}")

    # Also write calendar metadata for the UI
    calendars = {
        "pack_meeting":   {"label": "Pack Meetings", "color": COLORS["pack_meeting"]["color"], "checked": True},
        "pack_committee": {"label": "Committee Meetings", "color": COLORS["pack_committee"]["color"], "checked": True},
        "pack_special":   {"label": "Special Events (Derby, Service)", "color": COLORS["pack_special"]["color"], "checked": True},
        "pack_camping":   {"label": "Camping Trips", "color": COLORS["pack_camping"]["color"], "checked": True},
        "pack_conflict":  {"label": "Conflicts / No-Meeting Days", "color": COLORS["pack_conflict"]["color"], "checked": False},
        "council":        {"label": "PacSky Council / District", "color": COLORS["council"]["color"], "checked": True},
        "training":       {"label": "Leader Training (PacSky)", "color": COLORS["training"]["color"], "checked": True},
        "pausd":          {"label": "PAUSD No-School Days", "color": COLORS["pausd"]["color"], "checked": True},
        "hausner":        {"label": "Hausner (Jewish Day School)", "color": COLORS["hausner"]["color"], "checked": False},
        "jcc":            {"label": "JCC Closures", "color": COLORS["jcc"]["color"], "checked": False},
        "emerson":        {"label": "Emerson Montessori", "color": COLORS["emerson"]["color"], "checked": False},
        "nueva":          {"label": "Nueva School", "color": COLORS["nueva"]["color"], "checked": False},
        "keys":           {"label": "Keys School", "color": COLORS["keys"]["color"], "checked": False},
        "st_raymond":     {"label": "St. Raymond (Catholic)", "color": COLORS["st_raymond"]["color"], "checked": False},
        "jewish":         {"label": "Jewish Holidays", "color": COLORS["jewish"]["color"], "checked": True},
        "islamic":        {"label": "Islamic Holidays", "color": COLORS["islamic"]["color"], "checked": True},
        "christian":      {"label": "Christian Holidays", "color": COLORS["christian"]["color"], "checked": True},
        "hindu":          {"label": "Hindu / Indian Holidays", "color": COLORS["hindu"]["color"], "checked": True},
        "us_federal":     {"label": "US Federal Holidays", "color": COLORS["us_federal"]["color"], "checked": True},
    }

    meta_path = os.path.join(OUT_DIR, "calendars.json")
    with open(meta_path, "w") as f:
        json.dump(calendars, f, indent=2)

    print(f"Wrote calendar metadata to {meta_path}")


if __name__ == "__main__":
    main()
