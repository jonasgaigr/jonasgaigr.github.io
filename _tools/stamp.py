"""Post-render: write the date of this render into the footer ("Last updated").

_quarto.yml puts the placeholder RENDERDATE in the footer; this replaces it in
every page Quarto has just written.
"""
import datetime
import glob
import os

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

today = datetime.date.today()
stamp = f'<time datetime="{today.isoformat()}">{today.day} {MONTHS[today.month - 1]} {today.year}</time>'

out_dir = os.environ.get("QUARTO_PROJECT_OUTPUT_DIR", "_site")
listed = os.environ.get("QUARTO_PROJECT_OUTPUT_FILES", "")
files = [f for f in listed.splitlines() if f.strip()] or glob.glob(os.path.join(out_dir, "**", "*.html"), recursive=True)

n = 0
for f in files:
    if not f.endswith(".html"):
        continue
    if not os.path.isabs(f) and not os.path.exists(f):
        f = os.path.join(out_dir, f)
    if not os.path.exists(f):
        continue
    with open(f, encoding="utf-8") as fh:
        text = fh.read()
    if "RENDERDATE" in text:
        with open(f, "w", encoding="utf-8", newline="") as fh:
            fh.write(text.replace("RENDERDATE", stamp))
        n += 1
print(f"stamp: footer date set on {n} pages")
