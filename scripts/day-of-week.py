#!/usr/bin/env python3
"""
Compute day-of-week for a list of dates.

Usage:
  python3 day-of-week.py 2026-09-03 2026-10-15 2027-01-21
  # or pipe dates:
  echo "2026-09-03" | python3 day-of-week.py
"""

import sys
from datetime import datetime

def day_for(datestr):
    dt = datetime.strptime(datestr.strip(), '%Y-%m-%d')
    return f"{datestr.strip()}  {dt.strftime('%A')[:3]}  ({dt.strftime('%A')})"

if len(sys.argv) > 1:
    dates = sys.argv[1:]
else:
    dates = sys.stdin.read().strip().split('\n')

for d in dates:
    if d.strip():
        print(day_for(d))
