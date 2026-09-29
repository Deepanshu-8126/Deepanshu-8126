"""
GitHub Profile Analytics Dashboard — auto-generated daily by GitHub Actions.
Data: GitHub REST API + public contribution calendar. No 3rd-party stats servers.
"""
import os, re, json, urllib.request
from datetime import datetime, timedelta, timezone, date
import pandas as pd, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

USER = os.getenv("GH_USER", "Deepanshu-8126")
OUT = "assets/github-dashboard.png"
TOKEN = os.getenv("GITHUB_TOKEN")
IST = timezone(timedelta(hours=5, minutes=30))

def get(url, raw=False):
    h = {"User-Agent": "dash"}
    if TOKEN and "api.github.com" in url: h["Authorization"] = f"Bearer {TOKEN}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=30) as r:
        b = r.read().decode()
    return b if raw else json.loads(b)

# ---------- COLLECT ----------
user = get(f"https://api.github.com/users/{USER}")
repos = [r for r in get(f"https://api.github.com/users/{USER}/repos?per_page=100") if not r["fork"]]
langs = {}
for r in repos:
    for k, v in get(r["languages_url"]).items():
        langs[k] = langs.get(k, 0) + v
html = get(f"https://github.com/users/{USER}/contributions", raw=True)

# contribution calendar
ids = dict(re.findall(r'data-date="([\d-]+)" id="([^"]+)"', html))
tips = dict(re.findall(r'for="([^"]+)"[^>]*>(No|\d+) contribution', html))
cal = pd.DataFrame([(d, 0 if tips.get(i, "No") == "No" else int(tips[i])) for d, i in ids.items()], columns=["date", "n"])
cal["date"] = pd.to_datetime(cal["date"]); cal = cal.sort_values("date").reset_index(drop=True)

# ---------- ANALYZE ----------
total = int(cal["n"].sum())
active = int((cal["n"] > 0).sum())
def streaks(s):
    best = cur = 0
    for v in s: cur = cur + 1 if v > 0 else 0; best = max(best, cur)
    cs = 0
    arr = list(s)
    if arr and arr[-1] == 0: arr = arr[:-1]          # today not done yet is OK
    for v in reversed(arr):
        if v > 0: cs += 1
        else: break
    return cs, best
cur_streak, best_streak = streaks(cal["n"])
best_day = cal.loc[cal["n"].idxmax()]
stars = sum(r["stargazers_count"] for r in repos)
monthly = cal.groupby(cal["date"].dt.to_period("M"))["n"].sum()
weekday = cal.groupby(cal["date"].dt.dayofweek)["n"].mean()
langs = {("Jupyter" if k=="Jupyter Notebook" else k): v for k, v in langs.items()}
lang_s = pd.Series(langs).sort_values(ascending=False)
top_l = lang_s.head(6); 
if len(lang_s) > 6: top_l["Other"] = lang_s[6:].sum()
repo_lang = pd.Series([("Jupyter" if r["language"]=="Jupyter Notebook" else r["language"]) or "Other" for r in repos]).value_counts().head(7)
recent = sorted(repos, key=lambda r: r["pushed_at"], reverse=True)[:6]

# ---------- VISUALIZE ----------
BG, CARD, GRID, TXT, MUTED = "#0D1117", "#161B22", "#2D1B69", "#E5E7EB", "#94A3B8"
CY, PU, PK, YE, GR = "#00E5FF", "#7C3AED", "#C084FC", "#FBBF24", "#22C55E"
LC = {"Jupyter": "#F37626", "Jupyter Notebook": "#F37626", "Python": "#3776AB", "JavaScript": "#F7DF1E", "TypeScript": "#3178C6",
      "Dart": "#00B4AB", "HTML": "#E34F26", "CSS": "#663399", "Other": "#64748B"}
pal = [CY, PU, PK, YE, GR, "#F97316", "#64748B"]
lc = lambda k, i: LC.get(k, pal[i % len(pal)])

plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": TXT})
fig = plt.figure(figsize=(16, 11.5), facecolor=BG)
gs = fig.add_gridspec(4, 12, height_ratios=[0.5, 1.05, 1.15, 1.15], hspace=0.62, wspace=0.9,
                      left=0.035, right=0.975, top=0.885, bottom=0.05)

fig.text(0.035, 0.95, f"{(user.get('name') or USER).upper()}  ·  GITHUB ANALYTICS", fontsize=24, weight="bold", color=CY)
fig.text(0.035, 0.918, f"@{USER}  •  Data Analyst · Python Developer · ML Enthusiast  •  auto-updated {datetime.now(IST):%d %b %Y, %I:%M %p IST}",
         fontsize=10.5, color=MUTED)

def style(ax, title):
    ax.set_facecolor(CARD); ax.tick_params(colors=MUTED, labelsize=8)
    for sp in ax.spines.values(): sp.set_color(GRID)
    ax.grid(color=GRID, alpha=0.45, lw=0.6); ax.set_axisbelow(True)
    ax.set_title(title, loc="left", color=TXT, fontsize=11.5, weight="bold", pad=9)

# KPI cards
kpis = [("CONTRIBUTIONS", f"{total:,}", "last 12 months", CY),
        ("CURRENT STREAK", f"{cur_streak}d", "keep it going 🔥".replace(" 🔥", ""), YE),
        ("LONGEST STREAK", f"{best_streak}d", f"{active} active days", PK),
        ("PUBLIC REPOS", f"{len(repos)}", f"{len(lang_s)} languages", PU),
        ("FOLLOWERS", f"{user['followers']}", f"{stars} stars earned", GR),
        ("BEST DAY", f"{int(best_day['n'])}", f"{best_day['date']:%d %b %Y}", "#F97316")]
for i, (t, v, sub, ac) in enumerate(kpis):
    ax = fig.add_subplot(gs[0, i*2:i*2+2]); ax.set_facecolor(CARD); ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_color(GRID)
    ax.axhline(1, color=ac, lw=6)
    ax.text(0.08, 0.68, t, fontsize=8.5, color=MUTED, weight="bold", transform=ax.transAxes)
    ax.text(0.08, 0.28, v, fontsize=21, color=ac, weight="bold", transform=ax.transAxes)
    ax.text(0.08, 0.07, sub, fontsize=8, color=MUTED, transform=ax.transAxes)

# Heatmap
ax = fig.add_subplot(gs[1, :]); style(ax, f"Contribution Heatmap — {total:,} contributions in the last year"); ax.grid(False)
start = cal["date"].min() - pd.Timedelta(days=(cal["date"].min().dayofweek + 1) % 7)
cmap = ["#1A1F2E", "#2D1B69", "#5B21B6", "#7C3AED", "#00B8D4", "#00E5FF"]
q = np.percentile(cal.loc[cal.n > 0, "n"], [25, 50, 75, 90]) if active else [1, 2, 3, 4]
for _, r in cal.iterrows():
    w = (r["date"] - start).days // 7; d = (r["date"].dayofweek + 1) % 7
    lvl = 0 if r.n == 0 else 1 + int(np.searchsorted(q, r.n, side="left"))
    ax.add_patch(FancyBboxPatch((w + 0.1, 6 - d + 0.1), 0.8, 0.8, boxstyle="round,pad=0,rounding_size=0.18",
                                fc=cmap[min(lvl, 5)], ec="none"))
nweeks = (cal["date"].max() - start).days // 7 + 1
ax.set_xlim(0, nweeks); ax.set_ylim(0, 7); ax.set_yticks([5.5, 3.5, 1.5]); ax.set_yticklabels(["Mon", "Wed", "Fri"])
mt = [((d - start).days // 7, d.strftime("%b")) for d in pd.date_range(start, cal["date"].max(), freq="MS")]
ax.set_xticks([m[0] + 0.5 for m in mt]); ax.set_xticklabels([m[1] for m in mt])
for sp in ax.spines.values(): sp.set_visible(False)
for i, c in enumerate(cmap):
    ax.add_patch(FancyBboxPatch((nweeks - 7 + i * 1.05, -1.25), 0.8, 0.8, boxstyle="round,pad=0,rounding_size=0.18", fc=c, ec="none", clip_on=False))
ax.text(nweeks - 7.4, -0.95, "Less", ha="right", color=MUTED, fontsize=8); ax.text(nweeks - 0.6, -0.95, "More", color=MUTED, fontsize=8)

# Monthly trend
ax = fig.add_subplot(gs[2, :7]); style(ax, "Monthly Contributions")
x = np.arange(len(monthly)); ax.bar(x, monthly.values, color=[CY if v == monthly.max() else PU for v in monthly.values], width=0.7, alpha=0.9)
ax.plot(x, monthly.rolling(3, min_periods=1).mean().values, color=YE, lw=2, marker="o", ms=4, label="3-month avg")
for xi, v in zip(x, monthly.values): ax.text(xi, v + monthly.max() * 0.02, int(v), ha="center", color=TXT, fontsize=7.5)
ax.set_xticks(x); ax.set_xticklabels([p.strftime("%b\n%y") for p in monthly.index])
ax.legend(facecolor=CARD, edgecolor=GRID, labelcolor=TXT, fontsize=8, loc="upper left")

# Language donut
ax = fig.add_subplot(gs[2, 7:]); ax.set_facecolor(BG)
pct = top_l / top_l.sum() * 100
ax.pie(top_l.values, colors=[lc(k, i) for i, k in enumerate(top_l.index)], startangle=90, counterclock=False,
       wedgeprops=dict(width=0.33, edgecolor=BG, lw=2), center=(-0.55, 0))
ax.text(-0.55, 0.06, f"{len(lang_s)}", ha="center", fontsize=22, weight="bold"); ax.text(-0.55, -0.2, "languages", ha="center", fontsize=8, color=MUTED)
for i, (k, p) in enumerate(pct.items()):
    y = 0.75 - i * 0.28
    ax.add_patch(plt.Rectangle((0.72, y - 0.07), 0.14, 0.14, color=lc(k, i)))
    ax.text(0.95, y, f"{k}", va="center", fontsize=9); ax.text(2.35, y, f"{p:.1f}%", va="center", ha="right", fontsize=9, weight="bold", color=lc(k, i) if k != "Other" else MUTED)
ax.set_xlim(-1.7, 2.45); ax.set_ylim(-1.15, 1.15); ax.set_aspect("equal")
ax.set_title("Top Languages (by code size)", color=TXT, fontsize=11.5, weight="bold", loc="left")

# Weekday
ax = fig.add_subplot(gs[3, :4]); style(ax, "Avg Contributions by Weekday")
wd = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]; wv = weekday.reindex(range(7)).fillna(0).values
bars = ax.bar(wd, wv, color=[CY if v == wv.max() else PK for v in wv], width=0.65)
for b, v in zip(bars, wv): ax.text(b.get_x() + b.get_width()/2, v + wv.max()*0.03, f"{v:.1f}", ha="center", fontsize=8)

# Repos by language
ax = fig.add_subplot(gs[3, 4:7]); style(ax, "Repos by Primary Language")
ax.barh(repo_lang.index[::-1], repo_lang.values[::-1], color=[lc(k, i) for i, k in enumerate(repo_lang.index[::-1])])
ax.tick_params(axis="y", labelsize=8)

# Recent activity
ax = fig.add_subplot(gs[3, 7:]); ax.set_facecolor(CARD); ax.set_xticks([]); ax.set_yticks([])
for sp in ax.spines.values(): sp.set_color(GRID)
ax.set_title("Recently Active Repositories", loc="left", color=TXT, fontsize=11.5, weight="bold", pad=9)
for i, r in enumerate(recent):
    y = 0.88 - i * 0.16
    days = (datetime.now(timezone.utc) - datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00"))).days
    ax.plot(0.04, y, "o", color=lc(r["language"] or "Other", i), ms=8, transform=ax.transAxes)
    ax.text(0.08, y, r["name"][:32], va="center", fontsize=9.5, weight="bold", transform=ax.transAxes)
    ax.text(0.66, y, r["language"] or "—", va="center", fontsize=8, color=MUTED, transform=ax.transAxes)
    ax.text(0.97, y, "today" if days == 0 else f"{days}d ago", va="center", ha="right", fontsize=8, color=CY, transform=ax.transAxes)

os.makedirs("assets", exist_ok=True)
fig.savefig(OUT, dpi=110, facecolor=BG); plt.close()
print("saved", OUT, "| total", total, "| streak", cur_streak, best_streak)
