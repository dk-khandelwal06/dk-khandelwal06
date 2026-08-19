import os
import json
import urllib.request
from datetime import date, timedelta
from xml.sax.saxutils import escape

USERNAME = "dk-khandelwal06"

TOKEN = os.environ.get("GH_TOKEN")

if not TOKEN:
    raise RuntimeError("GH_TOKEN is missing")

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

payload = json.dumps({
    "query": QUERY,
    "variables": {
        "login": USERNAME
    }
}).encode("utf-8")

request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": USERNAME
    },
    method="POST"
)

with urllib.request.urlopen(request) as response:
    result = json.loads(response.read().decode("utf-8"))

if "errors" in result:
    raise RuntimeError(result["errors"])

calendar = result["data"]["user"]["contributionsCollection"]["contributionCalendar"]

total_contributions = calendar["totalContributions"]

days = []

for week in calendar["weeks"]:
    for d in week["contributionDays"]:
        days.append({
            "date": date.fromisoformat(d["date"]),
            "count": d["contributionCount"]
        })

days.sort(key=lambda x: x["date"])


# -----------------------------
# Calculate longest streak
# -----------------------------

longest_streak = 0
current_streak_count = 0

for i, day in enumerate(days):
    if day["count"] > 0:
        if i > 0 and days[i - 1]["count"] > 0:
            current_streak_count += 1
        else:
            current_streak_count = 1

        longest_streak = max(longest_streak, current_streak_count)
    else:
        current_streak_count = 0


# -----------------------------
# Calculate current streak
# -----------------------------

today = date.today()

day_map = {d["date"]: d["count"] for d in days}

current_streak = 0

check_day = today

# If today has no contribution yet,
# allow the streak to continue from yesterday.
if day_map.get(check_day, 0) == 0:
    check_day = today - timedelta(days=1)

while day_map.get(check_day, 0) > 0:
    current_streak += 1
    check_day -= timedelta(days=1)


# -----------------------------
# Current streak date range
# -----------------------------

if current_streak > 0:
    streak_end = today if day_map.get(today, 0) > 0 else today - timedelta(days=1)
    streak_start = streak_end - timedelta(days=current_streak - 1)

    current_range = (
        f"{streak_start.strftime('%b %d')} - "
        f"{streak_end.strftime('%b %d')}"
    )
else:
    current_range = "No active streak"


# -----------------------------
# Longest streak date range
# -----------------------------

longest_start = None
longest_end = None

running_start = None
running_length = 0

for d in days:
    if d["count"] > 0:
        if running_start is None:
            running_start = d["date"]
            running_length = 1
        else:
            running_length += 1

        if running_length == longest_streak:
            longest_start = running_start
            longest_end = d["date"]
    else:
        running_start = None
        running_length = 0

if longest_start and longest_end:
    longest_range = (
        f"{longest_start.strftime('%b %d, %Y')} - "
        f"{longest_end.strftime('%b %d, %Y')}"
    )
else:
    longest_range = "N/A"


# -----------------------------
# SVG
# -----------------------------

WIDTH = 900
HEIGHT = 220

pink = "#ff3f91"
yellow = "#ffd93d"
purple = "#8b35e8"
background = "#11101a"
card = "#151321"
text = "#ffffff"
muted = "#a9a4b5"

svg = f"""<svg xmlns="http://www.w3.org/2000/svg"
width="{WIDTH}" height="{HEIGHT}"
viewBox="0 0 {WIDTH} {HEIGHT}">

<rect width="100%" height="100%" fill="{background}"/>

<rect x="25" y="20" width="850" height="180"
rx="3" fill="{card}"/>

<!-- Vertical separators -->

<line x1="300" y1="40" x2="300" y2="160"
stroke="#aaa" stroke-width="1"/>

<line x1="600" y1="40" x2="600" y2="160"
stroke="#aaa" stroke-width="1"/>


<!-- TOTAL CONTRIBUTIONS -->

<text x="150" y="85"
text-anchor="middle"
font-family="Arial, Helvetica, sans-serif"
font-size="28"
font-weight="bold"
fill="{pink}">
{total_contributions}
</text>

<text x="150" y="115"
text-anchor="middle"
font-family="Arial, Helvetica, sans-serif"
font-size="13"
fill="{pink}">
Total Contributions
</text>

<text x="150" y="140"
text-anchor="middle"
font-family="Arial, Helvetica, sans-serif"
font-size="11"
fill="{yellow}">
Last 12 Months
</text>


<!-- CURRENT STREAK -->

<circle cx="450" cy="78" r="34"
fill="none"
stroke="{pink}"
stroke-width="5"/>

<text x="450" y="88"
text-anchor="middle"
font-family="Arial, Helvetica, sans-serif"
font-size="24"
font-weight="bold"
fill="{yellow}">
{current_streak}
</text>

<text x="450" y="118"
text-anchor="middle"
font-family="Arial, Helvetica, sans-serif"
font-size="13"
font-weight="bold"
fill="{yellow}">
Current Streak
</text>

<text x="450" y="142"
text-anchor="middle"
font-family="Arial, Helvetica, sans-serif"
font-size="11"
fill="#8ee8ff">
{escape(current_range)}
</text>


<!-- LONGEST STREAK -->

<text x="750" y="85"
text-anchor="middle"
font-family="Arial, Helvetica, sans-serif"
font-size="28"
font-weight="bold"
fill="{pink}">
{longest_streak}
</text>

<text x="750" y="115"
text-anchor="middle"
font-family="Arial, Helvetica, sans-serif"
font-size="13"
fill="{pink}">
Longest Streak
</text>

<text x="750" y="140"
text-anchor="middle"
font-family="Arial, Helvetica, sans-serif"
font-size="11"
fill="{yellow}">
{escape(longest_range)}
</text>

</svg>
"""

os.makedirs("assets", exist_ok=True)

with open("assets/github-stats.svg", "w", encoding="utf-8") as f:
    f.write(svg)

print("GitHub stats generated successfully.")
print("Total Contributions:", total_contributions)
print("Current Streak:", current_streak)
print("Longest Streak:", longest_streak)