#!/usr/bin/env python3
"""
Build the GitHub Pages site for the book into docs/.

Only the table of contents (toc.md), the abstracts (abstracts/*.md),
the bios (bios/*.md) and the author photos (images/<slug>.jpg, optional)
are published; nothing else in the repo is copied.
Chapter order comes from structure/chap_order.txt, which must match the
entries in toc.md.

Usage: bin/site.py          (then commit docs/ and push)
Needs pandoc on the PATH.
"""

import html
import re
import shutil
import subprocess
from pathlib import Path

TOP = Path(__file__).resolve().parent.parent
OUT = TOP / "docs"
ASSETS = TOP / "site"
PHOTOS = TOP / "images"         # author photos, named like the bios
ORDER = TOP / "structure" / "chap_order.txt"

SITE_TITLE = "By the Sweat of Your Brow"
SUBTITLE = "The Concept of Work in the History of European Philosophy"
EDITORS = {"callahan": ("Gene Callahan", "New York University")}

# The name of each author as toc.md gives it -> the name of their bio file.
AUTHORS = {
    "Gene Callahan": "callahan",
    "James Bernard Murphy": "murphy",
    "James Alexander": "alexander",
    "Tamás Nyirkos": "nyirkos",
    "Orsolya Horváth": "horvath",
    "Tyler Chamberlain": "chamberlain",
    "Jason Ferrell": "ferrell",
    "Maria Pia Paganelli": "paganelli",
    "William Lombardo": "lombardo",
    "Nathanael Blake": "blake",
    "Jonathan Askonas": "askonas",
    "Spartaco Pupo": "pupo",
    "Gabriel F. Benzecry": "benzecry",
    "Nicholas A. Jensen": "jensen",
    "Sarah J. Wilford": "wilford",
    "W. J. Coats": "coats",
    "Ferenc Hörcher": "horcher",
    "Josefina Araos Bralic": "bralic",
    "Matías Petersen": "petersen",
    "Gülşen Seven": "seven",
    "Christopher Tollefsen": "tollefsen",
}

COMMONS = "https://commons.wikimedia.org/wiki/File:"

# Art for the home page and the bio pages: file in site/images/ ->
# (credit, Commons file name).
ART = {
    "work.jpg": ('Ford Madox Brown, <em>Work</em>, 1863, Birmingham Museum '
                 'and Art Gallery.',
                 "Ford_Madox_Brown_-_Work_-_Google_Art_Project.jpg"),
    "harvesters.jpg": ('Pieter Bruegel the Elder, <em>The Harvesters</em>, '
                       '1565, Metropolitan Museum of Art, New York.',
                       "Pieter_Bruegel_the_Elder-_The_Harvesters_-_"
                       "Google_Art_Project.jpg"),
}

# Banner art for each abstract page: slug -> (vertical focal point of the
# crop, credit, Commons file name).  Images live in
# site/images/abstracts/<slug>.jpg; a slug missing here falls back to
# harvesters.jpg.
BANNERS = {
    "intro": ("13%", 'Masaccio, <em>The Expulsion from the Garden of '
              'Eden</em>, 1424&ndash;28, Brancacci Chapel, Florence.',
              "Expulsion_from_the_Garden_of_Eden_Masaccio_Cappella_"
              "Brancacci.jpg"),
    "plato_aristotle": ("28%", 'Diego Vel&aacute;zquez, <em>The Forge of '
                        'Vulcan</em>, 1630, Museo del Prado, Madrid.',
                        "Vel%C3%A1zquez_-_La_Fragua_de_Vulcano_(Museo_del_"
                        "Prado,_1630).jpg"),
    "newtestament": ("45%", 'John Everett Millais, <em>Christ in the House '
                     'of His Parents</em>, 1849&ndash;50, Tate Britain, '
                     'London.',
                     "Sir_John_Everett_Millais_002.jpg"),
    "aquinas": ("76%", 'The Limbourg brothers and Barth&eacute;lemy '
                'd&rsquo;Eyck, <em>October</em>, from the <em>Tr&egrave;s '
                'Riches Heures du Duc de Berry</em>, 1412&ndash;16 and '
                'c. 1440, Mus&eacute;e Cond&eacute;, Chantilly.',
                "Les_Tr%C3%A8s_Riches_Heures_du_duc_de_Berry_octobre.jpg"),
    "luther": ("30%", 'Quentin Matsys, <em>The Moneylender and His '
               'Wife</em>, 1514, Mus&eacute;e du Louvre, Paris.',
               "Massysm_Quentin_%E2%80%94_The_Moneylender_and_his_Wife_"
               "%E2%80%94_1514.jpg"),
    "bacon": ("38%", 'Joseph Wright of Derby, <em>An Experiment on a Bird '
              'in the Air Pump</em>, 1768, National Gallery, London.',
              "An_Experiment_on_a_Bird_in_an_Air_Pump_by_Joseph_Wright_of_"
              "Derby,_1768.jpg"),
    "locke": ("40%", 'Jean-Fran&ccedil;ois Millet, <em>Man with a Hoe</em>, '
              'c. 1860&ndash;62, J. Paul Getty Museum, Los Angeles.',
              "Millet,_Jean-Fran%C3%A7ois_-_Man_with_a_Hoe_-_"
              "Google_Art_Project.jpg"),
    "smith": ("14%", 'Louis-Jacques Goussier (design) and A.-J. Defehrt '
              '(engraving), '
              '<em>&Eacute;pinglier</em> (pin-making), plate II, from '
              'Diderot and d&rsquo;Alembert&rsquo;s <em>Encyclop&eacute;die'
              '</em>, 1762.',
              "Defehrt_epinglier_pl2.jpg"),
    "hegel": ("45%", 'Joseph Wright of Derby, <em>An Iron Forge</em>, 1772, '
              'Tate Britain, London.',
              "Joseph_Wright_-_An_Iron_Forge_-_Google_Art_Project.jpg"),
    "kierkegaard": ("35%", 'Jean-Fran&ccedil;ois Millet, <em>The Angelus'
                    '</em>, 1857&ndash;59, Mus&eacute;e d&rsquo;Orsay, Paris.',
                    "Jean-Fran%C3%A7ois_Millet_(II)_001.jpg"),
    "marx": ("40%", 'Claude Monet, <em>Anglers on the Seine at Poissy</em>, '
             '1882, &Ouml;sterreichische Galerie Belvedere, Vienna.',
             "Claude_Monet_-_Angler_auf_der_Seine_bei_Poissy_-_1288_-_"
             "%C3%96sterreichische_Galerie_Belvedere.jpg"),
    "weber": ("45%", 'Rembrandt van Rijn, <em>The Syndics of the Drapers&rsquo; '
              'Guild</em>, 1662, Rijksmuseum, Amsterdam.',
              "Rembrandt_-_De_Staalmeesters-_het_college_van_staalmeesters_"
              "(waardijns)_van_het_Amsterdamse_lakenbereidersgilde_-_"
              "Google_Art_Project.jpg"),
    "gentile": ("35%", 'Giuseppe Pellizza da Volpedo, <em>The Fourth Estate'
                '</em>, 1901, Museo del Novecento, Milan.',
                "Quarto_Stato.jpg"),
    "mises": ("55%", 'Gustave Courbet, <em>The Stone Breakers</em>, 1849 '
              '(destroyed 1945).',
              "Gustave_Courbet_018.jpg"),
    "stein": ("28%", 'Johannes Vermeer, <em>The Milkmaid</em>, c. 1660, '
              'Rijksmuseum, Amsterdam.',
              "Johannes_Vermeer_-_Het_melkmeisje_-_Google_Art_Project.jpg"),
    "oakeshott": ("28%", 'Pierre-Auguste Renoir, <em>Luncheon of the Boating '
                  'Party</em>, 1880&ndash;81, Phillips Collection, '
                  'Washington.',
                  "Pierre-Auguste_Renoir_-_Luncheon_of_the_Boating_Party_-_"
                  "Google_Art_Project.jpg"),
    "pieper": ("55%", 'Georges Seurat, <em>A Sunday on La Grande Jatte'
               '</em>, 1884&ndash;86, Art Institute of Chicago.',
               "Georges_Seurat_-_A_Sunday_on_La_Grande_Jatte_--_1884_-_"
               "Google_Art_Project.jpg"),
    "arendt": ("30%", 'Pieter Bruegel the Elder, <em>The Tower of Babel</em>, '
               '1563, Kunsthistorisches Museum, Vienna.',
               "Pieter_Bruegel_the_Elder_-_The_Tower_of_Babel_(Vienna)_-_"
               "Google_Art_Project_-_edited.jpg"),
    "macintyre": ("33%", 'Johannes Vermeer, <em>The Lacemaker</em>, '
                  'c. 1669&ndash;71, Mus&eacute;e du Louvre, Paris.',
                  "Johannes_Vermeer_-_The_lacemaker_(c.1669-1671).jpg"),
    "geuss": ("45%", 'Gustave Caillebotte, <em>The Floor Scrapers</em>, '
              '1875, Mus&eacute;e d&rsquo;Orsay, Paris.',
              "Gustave_Caillebotte_-_The_Floor_Planers_-_"
              "Google_Art_Project.jpg"),
    "nnlt": ("70%", 'Jean-Fran&ccedil;ois Millet, <em>The Gleaners</em>, '
             '1857, Mus&eacute;e d&rsquo;Orsay, Paris.',
             "Jean-Fran%C3%A7ois_Millet_-_Gleaners_-_Google_Art_Project.jpg"),
}

# Abstracts whose banner needs more height to show what's going on in the
# painting (the "tall" class in style.css).
TALL_BANNERS = {"nnlt", "pieper", "oakeshott"}

FONTS = ("https://fonts.googleapis.com/css2?"
         "family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;"
         "0,9..144,800;1,9..144,400"
         "&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;"
         "1,8..60,400"
         "&family=Oswald:wght@500&display=swap")

NUMBERS = ["zero", "one", "two", "three", "four", "five", "six", "seven",
           "eight", "nine", "ten", "eleven", "twelve", "thirteen",
           "fourteen", "fifteen", "sixteen", "seventeen", "eighteen",
           "nineteen", "twenty", "twenty-one", "twenty-two", "twenty-three",
           "twenty-four", "twenty-five"]


def md_to_html(text: str) -> str:
    return subprocess.run(["pandoc", "-f", "markdown", "-t", "html5",
                           "--wrap=none"],
                          input=text, capture_output=True, text=True,
                          check=True).stdout


def inline(text: str) -> str:
    """Escape a one-line string, keeping *emphasis*."""
    return re.sub(r"\*([^*]+)\*", r"<em>\1</em>", html.escape(text.strip()))


def strip_rules(text: str) -> str:
    """Drop separator lines (====, ****, ____) the source files use."""
    return "\n".join(line for line in text.splitlines()
                     if not re.fullmatch(r"\s*[=*_]{3,}\s*", line))


def paragraphs(text: str) -> list:
    return [p for p in re.split(r"\n\s*\n", strip_rules(text).strip())
            if p.strip()]


def abstract_path(slug: str) -> Path:
    return TOP / "abstracts" / f"{slug}.md"


def surname(name: str) -> str:
    return name.split()[-1]


def abstract_body(e) -> str:
    """The abstract without whatever header it has.  The files vary: most
    open with a title (usually a # heading) and then an author line, some
    have only one of those, and some start straight in on the text."""
    paras = paragraphs(abstract_path(e["slug"]).read_text(encoding="utf-8"))
    first = paras[0].strip() if paras else ""
    if first.startswith("#") or ("\n" not in first and len(first) < 120
                                 and not first.endswith(".")):
        paras = paras[1:]
    if paras and len(paras[0]) < 200 and any(
            surname(n) in paras[0] for n, _ in e["authors"]):
        paras = paras[1:]
    return "\n\n".join(paras)


def banner(slug: str) -> tuple:
    """The banner div for an abstract page and its footer credit."""
    if slug not in BANNERS:
        return '<div class="banner"></div>', credit("harvesters.jpg")
    focus, text, commons = BANNERS[slug]
    kind = "banner tall" if slug in TALL_BANNERS else "banner"
    div = (f'<div class="{kind}" style="background-image: url(\'../images/'
           f'abstracts/{slug}.jpg\'); background-position: center {focus};">'
           f'</div>')
    return div, commons_credit(text, commons)


def commons_credit(text: str, commons: str) -> str:
    return (f'{text} <a href="{COMMONS}{commons}">Public domain, via '
            f'Wikimedia Commons</a>.')


def credit(name: str) -> str:
    return commons_credit(*ART[name])


def parse_toc():
    """Return the list of entries in toc.md."""
    lines = (TOP / "toc.md").read_text(encoding="utf-8").splitlines()
    raw = []
    for line in lines[lines.index("## Table of Contents") + 1:]:
        if re.match(r"\d+\. ", line):
            raw.append([line.split(". ", 1)[1].strip()])
        elif line.strip() and raw:
            raw[-1].append(line.strip())
    order = [l.strip() for l in ORDER.read_text().splitlines() if l.strip()]
    if len(order) != len(raw):
        raise SystemExit(f"{ORDER.name} has {len(order)} names but toc.md "
                         f"has {len(raw)} entries")
    entries = []
    for num, (slug, parts) in enumerate(zip(order, raw), start=1):
        if len(parts) != 2:
            raise SystemExit(f"toc.md entry {num} should be a title line "
                             f"and an author line: {parts}")
        title = parts[0].rstrip(",")
        # "A and B, Affiliation" when the authors share an affiliation,
        # or "A, Affiliation; B, Affiliation" when they don't.
        groups = []
        for group in parts[1].split("; "):
            byline, _, affil = group.partition(", ")
            groups += [(n.strip(), affil) for n in byline.split(" and ")]
        authors, affils = [], {}
        for name, affil in groups:
            if name not in AUTHORS:
                raise SystemExit(f"toc.md author {name!r} not in AUTHORS")
            if not (TOP / "bios" / f"{AUTHORS[name]}.md").exists():
                raise SystemExit(f"no bios/{AUTHORS[name]}.md for {name}")
            authors.append((name, AUTHORS[name]))
            affils[AUTHORS[name]] = affil
        if not abstract_path(slug).exists():
            raise SystemExit(f"no abstracts/{slug}.md for entry {num}")
        entries.append(dict(num=num, slug=slug, title=title,
                            authors=authors, affils=affils))
    return entries


def page(title: str, body: str, root: str, kind: str, credit: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{SITE_TITLE}: {SUBTITLE}. An edited volume.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{root}style.css">
</head>
<body class="{kind}">
<header class="masthead">
<a class="book" href="{root}index.html">{SITE_TITLE}</a>
<span class="sub">Edited by Gene Callahan</span>
</header>
{body}
<footer>
<p><a href="{root}index.html">Contents</a></p>
<p class="credit">{credit}</p>
</footer>
</body>
</html>
"""


def author_links(authors, root: str) -> str:
    return " and ".join(f'<a href="{root}bios/{s}.html">{html.escape(n)}</a>'
                        for n, s in authors)


def affil_span(affil: str) -> str:
    return f'<span class="affil">{html.escape(affil)}</span>' if affil else ""


def byline(e, root: str) -> str:
    """The authors with their affiliations, giving a shared affiliation
    once at the end."""
    shared = set(e["affils"].values())
    if len(shared) == 1:
        return author_links(e["authors"], root) + affil_span(shared.pop())
    return " and ".join(author_links([a], root) + affil_span(e["affils"][a[1]])
                        for a in e["authors"])


def build_index(entries, people) -> str:
    items = []
    for e in entries:
        title = f'<a href="abstracts/{e["slug"]}.html">{inline(e["title"])}</a>'
        items.append(f"""<li>
<span class="num">{e["num"]}</span>
<div><span class="title">{title}</span>
<span class="byline">{byline(e, "")}</span></div>
</li>""")
    editors = "\n".join(f"""<a class="editor" href="bios/{s}.html">
{f'<img src="images/authors/{s}.jpg" alt="{n}">'
 if (PHOTOS / f"{s}.jpg").exists() else ""}
<span class="name">{n}</span>
<span class="role">{r}</span>
</a>""" for s, (n, r) in EDITORS.items())
    scholars = NUMBERS[len(people)].capitalize()
    body = f"""<section class="hero">
<div class="hero-text">
<p class="kicker">An edited volume in the history of ideas</p>
<h1>{SITE_TITLE}</h1>
<p class="subtitle">{SUBTITLE}</p>
<p class="lede">Is work a curse or a calling, the enemy of leisure or a
basic human good? {scholars} scholars trace how the Western tradition has
understood work, from Plato, Aristotle and the New Testament through
Aquinas, Luther, Locke, Smith, Hegel and Marx to Weber, Arendt, Pieper,
Oakeshott and MacIntyre.</p>
<blockquote class="epigraph">By the sweat of your brow you will eat your
food until you return to the ground.<cite>Genesis 3:19</cite></blockquote>
<p class="cta"><a href="#contents">Table of contents &darr;</a></p>
</div>
<figure class="hero-art"><img src="images/work.jpg"
alt="Ford Madox Brown's painting Work: navvies digging up a Hampstead
street in the sun while gentlemen, a flower-seller and ragged children look
on"></figure>
</section>
<section class="editors">
<h2>The Editor</h2>
<div class="editor-row">
{editors}
</div>
</section>
<main id="contents">
<h2>Contents</h2>
<ol class="toc">
{chr(10).join(items)}
</ol>
<p class="hint">Click on a chapter title to read its abstract, or a contributor's
name to read their biography.</p>
</main>"""
    return page(SITE_TITLE, body, "", "home", credit("work.jpg"))


def build_abstract(e, prev, nxt) -> str:
    nav = ['<nav class="chapnav">']
    nav.append(f'<a class="prev" href="{prev["slug"]}.html">&larr; '
               f'{inline(prev["title"])}</a>' if prev else "<span></span>")
    nav.append('<a class="contents" href="../index.html#contents">Contents</a>')
    nav.append(f'<a class="next" href="{nxt["slug"]}.html">'
               f'{inline(nxt["title"])} &rarr;</a>' if nxt else "<span></span>")
    nav.append("</nav>")
    art, footer_credit = banner(e["slug"])
    body = f"""{art}
<main class="paper">
<p class="kicker">Chapter {e["num"]} &middot; Abstract</p>
<h1>{inline(e["title"])}</h1>
<p class="byline">{byline(e, "../")}</p>
<div class="text">
{md_to_html(abstract_body(e))}
</div>
{chr(10).join(nav)}
</main>"""
    plain = re.sub(r"\*", "", e["title"])
    return page(f"{html.escape(plain)} · {SITE_TITLE}", body, "../",
                "abstract", footer_credit)


def bio_text(slug: str, name: str) -> str:
    text = strip_rules((TOP / "bios" / f"{slug}.md")
                       .read_text(encoding="utf-8"))
    text = re.sub(r"\s*\([^()\s]+@[^()\s]+\)", "", text)   # no emails
    first = name.split()[0]
    if not text.lstrip().startswith("**") and text.lstrip().startswith(first):
        # bold the name, as the other bios do
        lead = re.match(r"\s*(\S+(?:\s\S+)*?)\s+(?=[a-z])", text)
        if lead:
            text = f"**{lead.group(1)}** " + text[lead.end():]
    return md_to_html(text)


def build_bio(slug, name, affil, chapters) -> str:
    photo = f'<img class="portrait" src="../images/authors/{slug}.jpg" ' \
        f'alt="{name}">' if (PHOTOS / f"{slug}.jpg").exists() else ""
    role = '<p class="kicker">Editor</p>' if slug in EDITORS \
        else '<p class="kicker">Contributor</p>'
    links = []
    for e in chapters:
        t = f'<a href="../abstracts/{e["slug"]}.html">{inline(e["title"])}</a>'
        links.append(f'<li><span class="num">Chapter {e["num"]}</span> {t}</li>')
    body = f"""<div class="banner"></div>
<main class="paper">
{role}
<div class="bio-head">{photo}
<div><h1>{html.escape(name)}</h1>
{f'<p class="byline"><span class="affil">{html.escape(affil)}</span></p>' if affil else ""}
</div></div>
<div class="text">
{bio_text(slug, name)}
</div>
<h2>In this volume</h2>
<ul class="chapters">
{chr(10).join(links)}
</ul>
</main>"""
    return page(f"{html.escape(name)} · {SITE_TITLE}", body, "../", "bio",
                credit("harvesters.jpg"))


def main():
    entries = parse_toc()
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "abstracts").mkdir(parents=True)
    (OUT / "bios").mkdir()
    shutil.copytree(ASSETS / "images", OUT / "images")
    (OUT / "images" / "authors").mkdir()
    for photo in PHOTOS.glob("*.jpg"):
        shutil.copy(photo, OUT / "images" / "authors")
    shutil.copy(ASSETS / "style.css", OUT / "style.css")
    (OUT / ".nojekyll").touch()

    people = {}         # slug -> (name, affiliation, [entries])
    for e in entries:
        for name, slug in e["authors"]:
            n, a, chs = people.get(slug, (name, "", []))
            people[slug] = (n, a or e["affils"][slug], chs + [e])

    (OUT / "index.html").write_text(build_index(entries, people))

    for i, e in enumerate(entries):
        prev = entries[i - 1] if i > 0 else None
        nxt = entries[i + 1] if i + 1 < len(entries) else None
        (OUT / "abstracts" / f"{e['slug']}.html").write_text(
            build_abstract(e, prev, nxt))

    for slug, (name, affil, chs) in people.items():
        (OUT / "bios" / f"{slug}.html").write_text(
            build_bio(slug, name, affil, chs))
    print(f"site: built {OUT} ({len(entries)} abstracts, {len(people)} bios)")


if __name__ == "__main__":
    main()
