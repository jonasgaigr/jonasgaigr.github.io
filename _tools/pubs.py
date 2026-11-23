"""Publications: from publications.bib to the Publications page and the homepage.

Runs before every render (pre-render in _quarto.yml), or by hand:
    python _tools/pubs.py

1. Asks ORCID for the list of works. Any work not yet in publications.bib is
   appended to it, with authors and volume details from Crossref when it has a
   DOI. Without a connection (or with PUBS_OFFLINE=1) this step is skipped and
   the file is used as it is.
2. Writes _publications.qmd (the list on publications.qmd, grouped by year)
   and _recent.qmd (the five newest works, for the homepage).

Standard library only.
"""
import datetime
import html
import json
import os
import re
import sys
import urllib.request

ORCID = "0009-0004-0267-1382"
ME = "gaigr"                      # family name to set in bold
RECENT = 5                        # works shown on the homepage
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
BIB = os.path.join(ROOT, "publications.bib")
UA = {"User-Agent": "pubs.py (Quarto site build)", "Accept": "application/json"}


# ---------------------------------------------------------------- BibTeX in

def parse_bib(text):
    """A small BibTeX reader: @type{key, field = {value} | "value" | number, ...}"""
    entries, i, n = [], 0, len(text)
    while True:
        i = text.find("@", i)
        if i < 0:
            return entries
        # skip '@' inside comment lines
        line_start = text.rfind("\n", 0, i) + 1
        if text[line_start:i].lstrip().startswith("%"):
            i += 1
            continue
        m = re.match(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", text[i:])
        if not m:
            i += 1
            continue
        e = {"type": m.group(1).lower(), "key": m.group(2)}
        i += m.end()
        while i < n:
            while i < n and text[i] in " \t\r\n,":
                i += 1
            if i < n and text[i] == "}":
                i += 1
                break
            fm = re.match(r"([\w-]+)\s*=\s*", text[i:])
            if not fm:
                raise ValueError(f"publications.bib: cannot read entry {e['key']} near: {text[i:i + 40]!r}")
            name = fm.group(1).lower()
            i += fm.end()
            if text[i] == "{":
                depth, j = 0, i
                while j < n:
                    if text[j] == "{":
                        depth += 1
                    elif text[j] == "}":
                        depth -= 1
                        if depth == 0:
                            break
                    j += 1
                value, i = text[i + 1:j], j + 1
            elif text[i] == '"':
                j = text.index('"', i + 1)
                value, i = text[i + 1:j], j + 1
            else:
                vm = re.match(r"[^,}\s]+", text[i:])
                value, i = vm.group(0), i + vm.end()
            e[name] = re.sub(r"\s+", " ", value).strip()
        entries.append(e)


def split_top(s, sep=" and "):
    """split on sep, but not inside braces"""
    out, depth, cur, i = [], 0, "", 0
    while i < len(s):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
        if depth == 0 and s.startswith(sep, i):
            out.append(cur)
            cur, i = "", i + len(sep)
            continue
        cur += s[i]
        i += 1
    out.append(cur)
    return [x.strip() for x in out if x.strip()]


def tex(s):
    """BibTeX value -> HTML: \\emph{} and \\textit{} to <i>, braces dropped, -- to an en dash"""
    s = html.escape(s, quote=False).replace("\\&amp;", "&amp;")
    s = re.sub(r"\\(?:emph|textit)\s*\{", "\x01", s)
    s = re.sub(r"\\textbf\s*\{", "\x02", s)
    out, stack = "", []
    for ch in s:
        if ch in "\x01\x02":
            stack.append("</i>" if ch == "\x01" else "</b>")
            out += "<i>" if ch == "\x01" else "<b>"
        elif ch == "{":
            stack.append("")
        elif ch == "}":
            out += stack.pop() if stack else ""
        else:
            out += ch
    return out.replace("---", "\u2014").replace("--", "\u2013")


def plain(s):
    return re.sub(r"<[^>]+>", "", tex(s))


# ---------------------------------------------------------------- names

def initials(given):
    parts = []
    for word in given.replace(".", ". ").split():
        if not word.strip("."):
            continue
        parts.append("-".join(p.strip(".")[0] + "." for p in word.split("-") if p.strip(".")))
    return " ".join(parts)


def name(person):
    person = person.strip("{} ")
    if "," in person:
        family, given = [x.strip() for x in person.split(",", 1)]
    else:
        bits = person.split()
        family, given = bits[-1], " ".join(bits[:-1])
    family = family.strip("{}")
    return family, (f"{family}, {initials(given)}" if given else family)


def is_me(family):
    return family.casefold() == ME


def authors_full(e):
    """For the Publications page: everyone, or the first three ... me et al. for long lists"""
    people = [name(p) for p in split_top(e.get("author", ""))]
    show = [html.escape(n) if not is_me(f) else f"<strong>{html.escape(n)}</strong>" for f, n in people]
    if len(people) > 20:
        mine = [k for k, (f, _) in enumerate(people) if is_me(f)]
        head = ", ".join(show[:3])
        if mine and mine[0] >= 3:
            return f"{head}, \u2026 {show[mine[0]]} et al."
        return f"{head} et al."
    if len(show) <= 1:
        return "".join(show)
    return ", ".join(show[:-1]) + " &amp; " + show[-1]


def authors_short(e):
    """For the homepage: all of up to three authors, otherwise the first et al., incl. me"""
    people = [name(p) for p in split_top(e.get("author", ""))]
    if len(people) <= 3:
        n = [html.escape(x) for _, x in people]
        return n[0] if len(n) == 1 else ", ".join(n[:-1]) + " &amp; " + n[-1]
    first = html.escape(people[0][1])
    if is_me(people[0][0]):
        return f"{first} et al."
    mine = [x for f, x in people if is_me(f)]
    return f"{first} et al., incl. {html.escape(mine[0])}" if mine else f"{first} et al."


# ---------------------------------------------------------------- formatting

def venue(e):
    if e.get("pubstate") == "inpreparation":
        where = e.get("journal")
        return f"In preparation for <i>{tex(where)}</i>." if where else "In preparation."
    where = e.get("journal") or e.get("booktitle") or e.get("institution") or e.get("publisher") or e.get("howpublished")
    if not where:
        return ""
    s = f"<i>{tex(where)}</i>"
    vol, num, pages = e.get("volume"), e.get("number"), e.get("pages")
    if vol:
        s += f" {tex(vol)}" + (f"({tex(num)})" if num else "")
    elif num and e.get("year"):
        s += f" {tex(num)}/{e['year']}"
    if pages:
        s += f": {tex(pages)}"
    return s + "."


def link(e, short):
    doi = (e.get("doi") or "").strip()
    if doi:
        doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
        href = f"https://doi.org/{doi}"
        return href, ("DOI" if short else f"doi.org/{doi}")
    url = e.get("url")
    if url:
        host = re.sub(r"^https?://(www\.)?", "", url).split("/")[0]
        pdf = url.lower().endswith(".pdf")
        return url, ("PDF" if short and pdf else "Link" if short else host + (" (PDF)" if pdf else ""))
    return None, None


def sort_key(e):
    d = e.get("date") or e.get("year") or "0"
    return tuple(int(x) for x in re.findall(r"\d+", d)[:3]) + (0,) * 3


def title_html(e, english):
    t = tex(e.get("title", ""))
    if english and e.get("titleen"):
        return tex(e["titleen"])
    if e.get("titleen"):
        return f"{t} ({tex(e['titleen'])})"
    return t


def page_item(e):
    yr = f" ({e['year']})" if e.get("year") else ""
    title = title_html(e, english=False)
    end = "" if title.endswith((".", "?", "!")) else "."
    s = f'<span class="pub-kind">{html.escape(e.get("kind", "Work"))}</span> {authors_full(e)}{yr} {title}{end} {venue(e)}'
    href, label = link(e, short=False)
    if href:
        s += f' <a href="{html.escape(href)}">{html.escape(label)}</a>'
    return f"<li>{s.strip()}</li>"


def home_item(e):
    title = title_html(e, english=True)
    end = "" if title.endswith((".", "?", "!")) else "."
    v = venue(e).replace("<i>", "<cite>").replace("</i>", "</cite>", 1)
    who = authors_short(e)
    who += "" if who.endswith(".") else "."
    s = f'<span class="k">{html.escape(e.get("kind", "Work"))}</span>{who} {title}{end} {v}'
    href, label = link(e, short=True)
    if href:
        s += f' <a href="{html.escape(href)}">{label}</a>'
    return f"            <li>{s.strip()}</li>"


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def build(entries):
    done = [e for e in entries if e.get("pubstate") != "inpreparation"]
    prep = [e for e in entries if e.get("pubstate") == "inpreparation"]
    done.sort(key=sort_key, reverse=True)

    years = []
    for e in done:
        y = e.get("year", "Undated")
        if not years or years[-1][0] != y:
            years.append((y, []))
        years[-1][1].append(e)

    head = "<!-- Generated by _tools/pubs.py from publications.bib. Edit publications.bib, not this file. -->\n\n"
    out = [head]
    for y, items in years:
        out.append(f"## {y}\n\n```{{=html}}\n<ul class=\"pubs\">\n" + "\n".join(page_item(e) for e in items) + "\n</ul>\n```\n")
    if prep:
        out.append("## In preparation\n\n```{=html}\n<ul class=\"pubs\">\n" + "\n".join(page_item(e) for e in prep) + "\n</ul>\n```\n")
    write(os.path.join(ROOT, "_publications.qmd"), "\n".join(out))

    recent = done[:RECENT]
    groups = []
    for e in recent:
        y = e.get("year", "")
        if not groups or groups[-1][0] != y:
            groups.append((y, []))
        groups[-1][1].append(e)
    rows = []
    for y, items in groups:
        rows.append(f"        <li>\n          <h3>{y}</h3>\n          <ul>\n" + "\n".join(home_item(e) for e in items) + "\n          </ul>\n        </li>")
    write(os.path.join(ROOT, "_recent.qmd"), head + "```{=html}\n      <ol class=\"core\">\n" + "\n".join(rows) + "\n      </ol>\n```\n")
    return len(done), len(prep)


# ---------------------------------------------------------------- ORCID

TYPES = {
    "journal-article": ("article", "Paper"), "report": ("techreport", "Report"),
    "preprint": ("misc", "Preprint"), "book-chapter": ("incollection", "Chapter"),
    "book": ("book", "Book"), "conference-paper": ("inproceedings", "Conference paper"),
    "conference-poster": ("misc", "Poster"), "conference-abstract": ("misc", "Abstract"),
    "data-set": ("misc", "Data"), "software": ("misc", "Software"),
    "dissertation-thesis": ("phdthesis", "Thesis"), "lecture-speech": ("misc", "Talk"),
}


def get_json(url, timeout=8):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return json.load(r)


def norm(s):
    return re.sub(r"[^0-9a-z]", "", plain(s or "").casefold())


def norm_doi(d):
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", (d or "").strip()).casefold()


def val(d, *path):
    for p in path:
        if not isinstance(d, dict):
            return None
        d = d.get(p)
    return d


def fix_case(family):
    return family.title() if family.isupper() and len(family) > 2 else family


def entry_from_orcid(rec, taken):
    btype, kind = TYPES.get(rec.get("type"), ("misc", "Other"))
    f = {}
    f["title"] = re.sub(r"<[^>]+>", "", val(rec, "title", "title", "value") or "").strip()
    tr = val(rec, "title", "translated-title", "value")
    if tr:
        f["titleen"] = tr
    if val(rec, "journal-title", "value"):
        f["journal" if btype == "article" else "howpublished"] = val(rec, "journal-title", "value")
    date = rec.get("publication-date") or {}
    parts = [val(date, k, "value") for k in ("year", "month", "day")]
    parts = [p for p in parts if p]
    if parts:
        f["year"] = parts[0]
        f["date"] = "-".join(parts)
    doi = next((x["external-id-value"] for x in val(rec, "external-ids", "external-id") or []
                if x.get("external-id-type") == "doi" and x.get("external-id-relationship") == "self"), None)
    if doi:
        f["doi"] = doi.lower()
    elif val(rec, "url", "value"):
        f["url"] = val(rec, "url", "value")

    authors = None
    cit = rec.get("citation") or {}
    if cit.get("citation-type") == "bibtex":
        m = re.search(r"author\s*=\s*\{(.*?)\}\s*,\s*\w+\s*=", cit.get("citation-value", ""), re.S)
        if m:
            authors = m.group(1)
    if doi:
        try:
            cr = get_json("https://api.crossref.org/works/" + urllib.request.quote(doi))["message"]
            people = [f"{fix_case(a['family'])}, {a['given']}" if a.get("given") else a.get("family") or a.get("name", "")
                      for a in cr.get("author", [])]
            if people and not authors:
                authors = " and ".join(people)
            for k, ck in (("volume", "volume"), ("number", "issue"), ("pages", "page")):
                if cr.get(ck):
                    f[k] = cr[ck].replace("-", "--")
            if not f.get("pages") and cr.get("article-number"):
                f["pages"] = cr["article-number"]
            if btype == "article" and not f.get("journal") and cr.get("container-title"):
                f["journal"] = cr["container-title"][0]
        except Exception:
            pass
    if not authors:
        names = [val(c, "credit-name", "value") for c in val(rec, "contributors", "contributor") or []]
        names = [n for n in names if n]
        if names:
            authors = " and ".join(f"{fix_case(n.split()[-1])}, {' '.join(n.split()[:-1])}" if len(n.split()) > 1 else n for n in names)
    if authors:
        f["author"] = authors
    f["kind"] = kind
    f["orcid"] = str(rec.get("put-code"))

    first = re.sub(r"[^a-z]", "", (name(split_top(authors)[0])[0] if authors else "work").casefold()
                   .translate(str.maketrans("áäčďéěíľňóôřšťúůýž", "aacdeeilnoorstuuyz")))
    key = f"{first or 'work'}{f.get('year', '')}"
    base, k = key, 0
    while key in taken:
        k += 1
        key = base + "abcdefghijklmnopqrstuvwxyz"[k - 1]
    taken.add(key)

    width = max(len(x) for x in f)
    body = ",\n".join(f"  {x.ljust(width)} = {{{v.replace('{', '').replace('}', '')}}}" for x, v in f.items())
    return f"@{btype}{{{key},\n{body}\n}}\n", f["title"]


def sync(entries):
    if os.environ.get("PUBS_OFFLINE"):
        return []
    try:
        works = get_json(f"https://pub.orcid.org/v3.0/{ORCID}/works")
    except Exception as err:
        print(f"pubs: ORCID not reached ({err.__class__.__name__}); using publications.bib as it is")
        return []
    codes = {e.get("orcid") for e in entries if e.get("orcid")}
    dois = {norm_doi(e.get("doi")) for e in entries if e.get("doi")}
    titles = {norm(e.get(k)) for e in entries for k in ("title", "titleen") if e.get(k)}
    taken = {e["key"] for e in entries}
    new = []
    for g in works.get("group", []):
        sums = g.get("work-summary", [])
        if not sums or any(str(s.get("put-code")) in codes for s in sums):
            continue
        s = sums[0]
        ids = [norm_doi(x["external-id-value"]) for x in val(s, "external-ids", "external-id") or [] if x.get("external-id-type") == "doi"]
        if any(d in dois for d in ids) or norm(val(s, "title", "title", "value")) in titles:
            continue
        try:
            rec = get_json(f"https://pub.orcid.org/v3.0/{ORCID}/work/{s['put-code']}")
        except Exception:
            continue
        new.append(entry_from_orcid(rec, taken))
    if new:
        stamp = datetime.date.today().isoformat()
        with open(BIB, "a", encoding="utf-8", newline="\n") as fh:
            for text, title in new:
                fh.write(f"\n% Added from ORCID on {stamp}. Check the authors, title and kind, then delete this line.\n{text}")
                print(f"pubs: added from ORCID: {title}")
    return new


def main():
    text = open(BIB, encoding="utf-8").read()
    entries = parse_bib(text)
    if sync(entries):
        entries = parse_bib(open(BIB, encoding="utf-8").read())
    n, p = build(entries)
    print(f"pubs: {n} works and {p} in preparation written to _publications.qmd and _recent.qmd")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"pubs: {err}", file=sys.stderr)
        sys.exit(1)
