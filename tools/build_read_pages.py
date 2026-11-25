#!/usr/bin/env python3
"""Build the static Read the Scripts pages.

Reads the original UTF-8 scripts in scripts/*.txt (byte-for-byte copies of
Brian's files) and writes:

- scripts/download/*.txt — the same text with a UTF-8 BOM, for Windows Notepad
- scripts/rewrite-project-scripts.zip — those Notepad copies
- read/*.html — one reading page per script
- scripts.html — the index

Run from the site root, after the original .txt files are in scripts/:

    python3 tools/build_read_pages.py

To copy originals in from a folder of Brian's .txt files first:

    python3 tools/build_read_pages.py --import /path/to/folder
"""

import argparse
import html
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
DOWNLOADS = SCRIPTS / "download"
READ = ROOT / "read"
ZIP_NAME = "rewrite-project-scripts.zip"
BOM = b"\xef\xbb\xbf"

TITLE_RE = re.compile(
    r"^Buffy the Vampire Slayer\. Season (six|seven), episode (\d+)"
    r"(?:, part (\d+))?\. (.+)\.$"
)
CHAPTER_RE = re.compile(r"^CHAPTER\s+(\d+)$")
CHAPTER_INLINE_RE = re.compile(r"^Chapter\s+(\d+)\.\s+(.+)$")
FILE_RE = re.compile(
    r"Season (six|seven) episode (\d+)(?: part (\d+))?\.\s+(.+?)\s+-\s+Completed",
    re.IGNORECASE,
)

SEASON_WORD = {"six": 6, "seven": 7}
SEASON_NAME = {6: "Season Six", 7: "Season Seven"}


def slugify(text):
    text = text.lower().replace("'", "").replace("’", "")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def esc(text):
    return html.escape(text, quote=False)


def import_sources(folder):
    SCRIPTS.mkdir(parents=True, exist_ok=True)
    copied = 0
    for path in sorted(Path(folder).glob("*.txt")):
        match = FILE_RE.search(path.name)
        if not match:
            raise SystemExit(f"Could not read the episode name from {path.name}")
        season = SEASON_WORD[match.group(1).lower()]
        episode = int(match.group(2))
        part = int(match.group(3)) if match.group(3) else None
        data = path.read_bytes()
        if data.startswith(BOM):
            raise SystemExit(f"{path.name} already has a BOM; originals should not.")
        title_line = data.decode("utf-8").splitlines()[0]
        parsed = TITLE_RE.match(title_line)
        if not parsed:
            raise SystemExit(f"Unexpected title line in {path.name}: {title_line}")
        name = parsed.group(4)
        if "5x5" in path.name.lower():
            slug = "5x5"
        else:
            slug = slugify(name)
        code = f"s{season}e{episode:02d}" + (f"p{part}" if part else "")
        dest = SCRIPTS / f"{code}-{slug}.txt"
        dest.write_bytes(data)
        if dest.read_bytes() != data:
            raise SystemExit(f"Copy changed bytes: {dest}")
        copied += 1
    if copied != 31:
        raise SystemExit(f"Expected 31 scripts, copied {copied}")


def load_catalog():
    items = []
    for path in sorted(SCRIPTS.glob("s[67]e*.txt")):
        data = path.read_bytes()
        if data.startswith(BOM):
            raise SystemExit(f"{path.name} should be the original file, without a BOM")
        text = data.decode("utf-8")
        title_line = text.splitlines()[0]
        parsed = TITLE_RE.match(title_line)
        if not parsed:
            raise SystemExit(f"Unexpected title line in {path.name}: {title_line}")
        season = SEASON_WORD[parsed.group(1)]
        episode = int(parsed.group(2))
        part = int(parsed.group(3)) if parsed.group(3) else None
        name = parsed.group(4)
        code = f"s{season}e{episode:02d}" + (f"p{part}" if part else "")
        expected = f"{code}-{slugify(name) if '5x5' not in path.name else '5x5'}.txt"
        if path.name != expected:
            raise SystemExit(f"{path.name} does not match its title line ({expected})")
        if part:
            label = f"Ep {episode:02d}, Part {part} – {name}"
        else:
            label = f"Ep {episode:02d} – {name}"
        listen = None
        if season == 6 and part is None and 8 <= episode <= 16:
            listen = f"ep-{episode:02d}"
        items.append({
            "season": season,
            "episode": episode,
            "part": part or 0,
            "name": name,
            "label": label,
            "title_line": title_line,
            "code": code,
            "stem": path.stem,
            "path": path,
            "text": text,
            "listen": listen,
        })
    items.sort(key=lambda item: (item["season"], item["episode"], item["part"]))
    if len(items) != 31:
        raise SystemExit(f"Expected 31 scripts in scripts/, found {len(items)}")
    return items


def blocks(text):
    """Turn the script into headings and paragraphs, in order."""
    lines = text.splitlines()
    index = 1  # skip the title line; it is rendered separately
    while index < len(lines) and lines[index].strip() == "":
        index += 1
    output = []
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if stripped == "":
            index += 1
            continue
        chapter = CHAPTER_RE.match(stripped)
        if chapter:
            index += 1
            while index < len(lines) and lines[index].strip() == "":
                index += 1
            if index >= len(lines):
                raise SystemExit(f"CHAPTER {chapter.group(1)} has no name")
            name = lines[index].strip()
            if CHAPTER_RE.match(name) or name == "---":
                raise SystemExit(f"CHAPTER {chapter.group(1)} is not followed by a name")
            output.append(("chapter", chapter.group(1), name))
            index += 1
            continue
        inline = CHAPTER_INLINE_RE.match(stripped)
        if inline:
            output.append(("chapter-line", inline.group(1), stripped))
            index += 1
            continue
        if stripped in {"PREVIOUSLY", "PREVIOUSLY ON..."}:
            output.append(("label", stripped))
            index += 1
            continue
        if stripped == "---":
            output.append(("break",))
            index += 1
            continue
        output.append(("p", line.strip()))
        index += 1
    return output


def render_body(text):
    parts = []
    seen = {}
    for block in blocks(text):
        kind = block[0]
        if kind == "p":
            parts.append(f"      <p>{esc(block[1])}</p>")
        elif kind == "label":
            parts.append(f"      <h2 class=\"script-label\">{esc(block[1])}</h2>")
        elif kind == "break":
            parts.append("      <hr>")
        elif kind == "chapter":
            number, name = block[1], block[2]
            seen[number] = seen.get(number, 0) + 1
            suffix = "" if seen[number] == 1 else f"-{seen[number]}"
            parts.append(
                "      <h2 class=\"chapter\" id=\"chapter-"
                + esc(number)
                + suffix
                + "\"><span class=\"chapter-num\">CHAPTER "
                + esc(number)
                + "</span> "
                + esc(name)
                + "</h2>"
            )
        elif kind == "chapter-line":
            number, line = block[1], block[2]
            seen[number] = seen.get(number, 0) + 1
            suffix = "" if seen[number] == 1 else f"-{seen[number]}"
            parts.append(
                "      <h2 class=\"chapter\" id=\"chapter-"
                + esc(number)
                + suffix
                + "\">"
                + esc(line)
                + "</h2>"
            )
    return "\n".join(parts)


def chrome(prefix, current_scripts):
    current = " aria-current=\"page\"" if current_scripts else ""
    return f"""  <a class="skip-link" href="#content">Skip to content</a>
  <div class="page">
    <header class="site-header">
      <img class="banner" src="{prefix}images/banner_sunnydale_final.jpg" width="1280" height="720" alt="Night sky and full moon over a town. Title card: The Rewrite Project, Seasons Six and Seven. Buffy the Vampire Slayer. A full-cast audio drama. Best with headphones." fetchpriority="high">
    </header>

    <div class="layout">
      <nav class="panel" aria-label="Navigate">
        <p class="panel-title"><span>Navigate</span></p>
        <ul class="nav-list">
          <li><a class="bevel" href="{prefix}index.html"><span class="tri" aria-hidden="true"></span>Home</a></li>
          <li><a class="bevel" href="{prefix}episodes.html"><span class="tri" aria-hidden="true"></span>Episodes</a></li>
          <li><a class="bevel" href="{prefix}about.html"><span class="tri" aria-hidden="true"></span>About</a></li>
          <li><a class="bevel" href="{prefix}scripts.html"{current}><span class="tri" aria-hidden="true"></span>Scripts</a></li>
          <li><a class="bevel" href="https://www.youtube.com/@brian_belmont87"><span class="tri" aria-hidden="true"></span>YouTube channel</a></li>
          <li><a class="bevel" href="https://www.reddit.com/r/BtVsRewriteProject/"><span class="tri" aria-hidden="true"></span>Reddit</a></li>
        </ul>
      </nav>
""", """      <aside class="side" aria-label="About the project">
        <section class="panel">
          <h2 class="panel-title"><span>The Project</span></h2>
          <p>A free, non-commercial, full-cast audio drama.</p>
          <p>The Rewrite Project, Seasons Six and Seven. Best with headphones.</p>
        </section>
        <section class="panel">
          <h2 class="panel-title"><span>Listen</span></h2>
          <p>The episodes are published on YouTube.</p>
          <ul class="stack">
            <li><a class="bevel" href="https://www.youtube.com/@brian_belmont87"><span class="tri" aria-hidden="true"></span>YouTube channel</a></li>
            <li><a class="bevel" href="https://www.reddit.com/r/BtVsRewriteProject/"><span class="tri" aria-hidden="true"></span>Reddit</a></li>
          </ul>
        </section>
        <section class="panel">
          <h2 class="panel-title"><span>Read the Scripts</span></h2>
          <ul class="stack">
            <li><a class="bevel" href=\"""" + prefix + """scripts.html"><span class="tri" aria-hidden="true"></span>Read the Scripts</a></li>
          </ul>
        </section>
      </aside>
    </div>

    <footer class="site-footer">
      <div class="rule" aria-hidden="true">
        <span class="rule-cap"></span>
        <span class="rule-line"></span>
        <span class="rule-gem rule-gem-sm"></span>
        <span class="rule-line rule-line-mid"></span>
        <span class="rule-gem"></span>
        <span class="rule-line rule-line-mid"></span>
        <span class="rule-gem rule-gem-sm"></span>
        <span class="rule-line"></span>
        <span class="rule-cap"></span>
      </div>
      <p class="disclaimer">A free, non-commercial fan project. Buffy the Vampire Slayer and its characters belong to their respective owners. No copyright infringement intended.</p>
      <ul class="socials">
        <li>
          <a class="social" href="https://www.youtube.com/@brian_belmont87">
            <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true"><rect x="1.5" y="5" width="21" height="14" rx="3.2" fill="#ff2a2a"/><path d="M10.2 8.8v6.4l5.6-3.2z" fill="#fff"/></svg>
            YouTube
          </a>
        </li>
        <li>
          <a class="social" href="https://www.reddit.com/r/BtVsRewriteProject/">
            <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><circle cx="12" cy="13.2" r="7" fill="#ff4500"/><circle cx="9.4" cy="12.4" r="1.05" fill="#fff"/><circle cx="14.6" cy="12.4" r="1.05" fill="#fff"/><path d="M9.2 15.4c.9.75 1.8 1.1 2.8 1.1s1.9-.35 2.8-1.1" fill="none" stroke="#fff" stroke-width="1.1" stroke-linecap="round"/><circle cx="17.5" cy="7.7" r="1.55" fill="#ff4500"/><path d="M12.3 8.4 16.2 7.3" fill="none" stroke="#ff4500" stroke-width="1.15" stroke-linecap="round"/></svg>
            Reddit
          </a>
        </li>
      </ul>
      <p class="visit-count">Visitors: <span data-visits>156</span></p>
    </footer>
  </div>
"""


def page_shell(title, description, prefix, body, current_scripts=True):
    head, foot = chrome(prefix, current_scripts)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{html.escape(description, quote=True)}">
  <meta name="theme-color" content="#0b0910">
  <link rel="icon" href="{prefix}favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="{prefix}css/style.css">
</head>
<body>
{head}
      <main id="content" tabindex="-1">
{body}
      </main>

{foot}
  <script src="{prefix}js/visits.js" defer></script>
</body>
</html>
"""


def write_downloads(items):
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    zip_path = SCRIPTS / ZIP_NAME
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in items:
            original = item["path"].read_bytes()
            noted = BOM + original
            dest = DOWNLOADS / item["path"].name
            dest.write_bytes(noted)
            archive.writestr(item["path"].name, noted)


def write_read_pages(items):
    READ.mkdir(parents=True, exist_ok=True)
    for index, item in enumerate(items):
        previous_link = ""
        next_link = ""
        if index > 0:
            previous = items[index - 1]
            previous_link = (
                f"<a class=\"pager-prev\" href=\"{previous['stem']}.html\">Previous: {esc(previous['label'])}</a>"
            )
        if index + 1 < len(items):
            nxt = items[index + 1]
            next_link = (
                f"<a class=\"pager-next\" href=\"{nxt['stem']}.html\">Next: {esc(nxt['label'])}</a>"
            )
        body = f"""        <article class="panel">
          <h1 class="panel-title"><span>{esc(item['name'])}</span></h1>
          <p class="script-download"><a class="bevel" href="../scripts/download/{item['stem']}.txt" download="{item['stem']}.txt"><span class="tri" aria-hidden="true"></span>Download this script (.txt)</a></p>
          <div class="script-text">
      <p class="script-titleline">{esc(item['title_line'])}</p>
{render_body(item['text'])}
          </div>
          <nav class="script-pager" aria-label="More scripts">
            {previous_link}
            {next_link}
          </nav>
        </article>"""
        page = page_shell(
            f"{item['label']} | Read the Scripts",
            item["title_line"],
            "../",
            body,
        )
        (READ / f"{item['stem']}.html").write_text(page, encoding="utf-8")


def write_index(items):
    sections = []
    for season in (6, 7):
        rows = []
        for item in items:
            if item["season"] != season:
                continue
            listen = ""
            if item["listen"]:
                listen = f"<a href=\"episodes.html#{item['listen']}\">Listen</a>"
            rows.append(
                "            <li>"
                f"<span class=\"script-index-title\">{esc(item['label'])}</span>"
                f"<a href=\"read/{item['stem']}.html\">Read</a>"
                f"<a href=\"scripts/download/{item['stem']}.txt\" download=\"{item['stem']}.txt\">Download</a>"
                f"{listen}"
                "</li>"
            )
        sections.append(
            "        <section class=\"panel\">\n"
            f"          <h2 class=\"panel-title\"><span>{SEASON_NAME[season]}</span></h2>\n"
            "          <ul class=\"script-index\">\n"
            + "\n".join(rows)
            + "\n          </ul>\n"
            "        </section>"
        )
    body = """        <section class="panel">
          <h1 class="panel-title"><span>Read the Scripts</span></h1>
          <p class="script-note">These scripts are free to read and download for personal, non-commercial use.</p>
          <p class="script-actions"><a class="bevel" href="scripts/rewrite-project-scripts.zip" download="rewrite-project-scripts.zip"><span class="tri" aria-hidden="true"></span>Download all</a></p>
        </section>
""" + "\n".join(sections)
    page = page_shell(
        "Read the Scripts | The Rewrite Project",
        "Read and download the Rewrite Project scripts. Free for personal, non-commercial use.",
        "",
        body,
    )
    (ROOT / "scripts.html").write_text(page, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Build the Read the Scripts pages.")
    parser.add_argument(
        "--import",
        dest="source",
        help="Folder of original .txt scripts to copy into scripts/ before building.",
    )
    args = parser.parse_args()
    if args.source:
        import_sources(args.source)
    items = load_catalog()
    write_downloads(items)
    write_read_pages(items)
    write_index(items)
    print(f"Built {len(items)} reading pages, download copies, and scripts.html")


if __name__ == "__main__":
    main()
