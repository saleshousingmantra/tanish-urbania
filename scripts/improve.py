#!/usr/bin/env python3
"""Tanish Urbania upgrade (idempotent). Usage: python3 improve.py  (site folder: /home/user/tanish-urbania)"""
import os, re, glob, json, html, shutil
from PIL import Image

SITE = "/home/user/tanish-urbania"; TOOLS = "/home/user/tanish-tools"
os.chdir(SITE)
URL = "https://tanish-urbania.com"; DATE = "2026-11-26"; VER = "20261126a"
BRAND = "Tanish Urbania Charholi"
CAT = "project"; CATNAME = "Tanish Urbania Project"

def rd(p): return open(p, encoding="utf-8").read()
def wr(p, t):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True); open(p, "w", encoding="utf-8").write(t)
def esc(s): return html.escape(s, quote=True)
def slugify(t): return re.sub(r"[^a-z0-9]+", "-", html.unescape(re.sub(r"<[^>]+>", "", t)).lower()).strip("-")
def mins(b): return max(2, round(len(re.sub(r"<[^>]+>", " ", b).split()) / 200))
def pages(): return [f for f in glob.glob("**/*.html", recursive=True) if not f.startswith(("node_modules/",))]

# ------------------------------------------------------------------ 1. images (fix the ".." file names)
def images():
    for f in glob.glob("images/*..*"):
        dst = f.replace("..", ".")
        if not os.path.exists(dst): shutil.copy(f, dst)
        os.remove(f)
    for junk in ["images/yw-only-black-bg-512.png", "images/yw-only-black-bg.ico", "images/yw-only-black-bg.png", "images/og-image(1).webp"]:
        if os.path.exists(junk): os.remove(junk)
    for b in ["aerial-1", "aerial-2", "courtyard", "elevation-1", "elevation-2"]:
        for ext, q in (("webp", 78), ("jpg", 80)):
            src, dst = f"images/{b}.{ext}", f"images/{b}-640.{ext}"
            if os.path.exists(src) and not os.path.exists(dst):
                im = Image.open(src).convert("RGB"); h = round(im.size[1] * 640 / im.size[0])
                im.resize((640, h), Image.LANCZOS).save(dst, "WEBP" if ext == "webp" else "JPEG", quality=q, **({"method": 6} if ext == "webp" else {"optimize": True}))

def srcset_html(t):
    def pic(m):
        pict = m.group(0)
        if "-640.webp" in pict: return pict
        ms = re.search(r'<source type="image/webp" srcset="(/?(?:\.\./)*)images/([a-z0-9-]+)\.webp">', pict)
        if not ms or not os.path.exists(f"images/{ms.group(2)}-640.webp"): return pict
        pre, base = ms.group(1), ms.group(2); w = Image.open(f"images/{base}.webp").size[0]
        sizes = "100vw" if "hero-slide" in m.group(1) else ("(max-width: 800px) 100vw, 760px" if "article-img" in pict else "(max-width: 700px) 86vw, 380px")
        new = f'<source type="image/webp" srcset="{pre}images/{base}-640.webp 640w, {pre}images/{base}.webp {w}w" sizes="{sizes}">'
        return pict.replace(ms.group(0), new)
    # include 120 chars of context before <picture> so we know if it is a hero slide
    return re.sub(r'(.{0,120})<picture>.*?</picture>', lambda m: m.group(1) + pic(re.match(r'(.*)', m.group(0)[len(m.group(1)):], re.S) and type("M", (), {"group": lambda s, i=0, _m=m: (m.group(0)[len(m.group(1)):] if i == 0 else m.group(1))})()), t, flags=re.S)

# ------------------------------------------------------------------ 2. icons and social image
def icons():
    og = Image.open("images/og-image.jpg") if os.path.exists("images/og-image.jpg") else None
    src = os.path.join(TOOLS, "logo-source.jpg")
    if not os.path.exists(src):
        shutil.copy("images/og-image.jpg", src) if og and og.size[0] == 1523 else None
    im = Image.open(src).convert("RGB"); W, H = im.size
    bg = im.getpixel((8, 8))
    px = im.load(); xs = []; ys = []
    for y in range(0, H, 2):
        for x in range(W // 3, W, 2):
            r, g, b = px[x, y]
            if r > 110 and g < 70 and b < 90 and r - g > 60: xs.append(x); ys.append(y)
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    side = max(x1 - x0, y1 - y0); cx, cy = (x0 + x1) // 2, (y0 + y1) // 2; pad = int(side * .12); half = side // 2 + pad
    mark = im.crop((cx - half, cy - half, cx + half, cy + half)).convert("RGBA")
    # keep only the red pinwheel (drop the navy wordmark fragments); alpha from "redness"
    data = []
    for r, g, b, _ in mark.getdata():
        red = r - max(g, b)
        a = 0 if red < 25 else min(255, (red - 25) * 4)
        data.append((139, 30, 45, a) if a else (0, 0, 0, 0))
    tmark = Image.new("RGBA", mark.size); tmark.putdata(data)
    def sq(img, n, bgc=None):
        o = img.resize((n, n), Image.LANCZOS)
        if bgc is None: return o
        base = Image.new("RGBA", (n, n), bgc); base.alpha_composite(o); return base.convert("RGB")
    sq(tmark, 16).save("favicon-16x16.png"); sq(tmark, 32).save("favicon-32x32.png"); sq(tmark, 48).save("favicon-48x48.png")
    tmark.resize((256, 256), Image.LANCZOS).save("favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    sq(tmark, 180, (255, 255, 255, 255)).save("apple-touch-icon.png")
    sq(tmark, 192, (255, 255, 255, 255)).save("android-chrome-192x192.png"); sq(tmark, 512, (255, 255, 255, 255)).save("android-chrome-512x512.png")
    # 1200x630 social image: the full logo centred on its own background colour
    canvas = Image.new("RGB", (1200, 630), bg); h = 560; w = round(W * h / H)
    if w > 1100: w = 1100; h = round(H * w / W)
    logo = im.resize((w, h), Image.LANCZOS); canvas.paste(logo, ((1200 - w) // 2, (630 - h) // 2)); canvas.save("images/og-image.jpg", quality=88, optimize=True)

# ------------------------------------------------------------------ 3. fonts + css
def fonts():
    os.makedirs("fonts", exist_ok=True)
    out = ""; seen = set()
    for blk in rd(os.path.join(TOOLS, "fonts.css")).splitlines():
        fam = re.search(r"font-family:'([^']+)'", blk).group(1); fn = re.search(r"url\(\.\./fonts/([^)]+)\)", blk).group(1); ur = re.search(r"unicode-range:([^}]*)", blk).group(1)
        key = (fam, fn)
        if key in seen: continue
        seen.add(key); shutil.copy(os.path.join(TOOLS, fn), f"fonts/{fn}")
        wt = "500 700" if fam.startswith("Cormorant") else "400 600"
        out += f"@font-face{{font-family:'{fam}';font-style:normal;font-weight:{wt};font-display:swap;src:url(../fonts/{fn}) format('woff2');unicode-range:{ur}}}\n"
    c = rd("css/style.css")
    if "cormorant-garamond-latin" not in c: c = out + c
    if ".h1-brand" not in c:
        c += """
/* SEO upgrade additions */
.h1-brand{display:block;font-family:var(--sans,Inter,system-ui,sans-serif);font-size:.28em;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--gold-light);margin-bottom:.5em}
.article h1 .h1-brand{color:var(--brick)}
.hero h1 .h1-loc{display:block;font-family:var(--sans,Inter,system-ui,sans-serif);font-size:.26em;font-weight:500;letter-spacing:.14em;text-transform:uppercase;color:var(--gold-light);margin-top:.35em;text-shadow:none}
.footer-links{display:flex;flex-wrap:wrap;justify-content:center;gap:8px 20px;margin:14px 0 4px}.footer-links a{color:rgba(255,255,255,.82);font-size:.9rem;text-decoration:none}.footer-links a:hover{color:#fff;text-decoration:underline}
.smap{display:grid;gap:26px;padding:8px 0 40px}.smap section h2{font-size:1.3rem;margin:0 0 .5em}.smap ul{list-style:none;margin:0;padding:0;display:grid;gap:7px}.smap a{color:var(--brick)}
@media(min-width:800px){.smap{grid-template-columns:repeat(3,1fr)}}
.tw{overflow-x:auto;margin:0 0 1.4em}.article-body table.compare{width:100%;border-collapse:collapse;font-size:.95rem;background:#fff;border:1px solid var(--line)}
.article-body table.compare th,.article-body table.compare td{padding:.7em .9em;text-align:left;border-bottom:1px solid var(--line)}.article-body table.compare th{background:var(--tint)}
@media(max-width:640px){.article-body table.compare th,.article-body table.compare td{padding:.55em .5em;font-size:.86rem;vertical-align:top}}
"""
    wr("css/style.css", c)

# ------------------------------------------------------------------ 4. site-wide html edits
def head_tweaks(t, f):
    depth = f.count("/")
    # remove Google Fonts
    t = re.sub(r'\s*<link rel="preconnect" href="https://fonts\.(?:googleapis|gstatic)\.com"[^>]*>', "", t)
    t = re.sub(r'\s*<link (?:rel="stylesheet" )?href="https://fonts\.googleapis\.com/css2[^>]*>', "", t)
    t = re.sub(r'\s*<link href="https://fonts\.googleapis\.com/css2[^>]*rel="stylesheet">', "", t)
    root = "/" if "/css/style.css" in t or 'href="/' in t else "../" * depth
    if "cormorant-garamond-latin-1.woff2" not in t:
        pre = (f'<link rel="preload" as="font" type="font/woff2" crossorigin href="{root}fonts/cormorant-garamond-latin-1.woff2">\n  '
               f'<link rel="preload" as="font" type="font/woff2" crossorigin href="{root}fonts/inter-latin-3.woff2">\n  ')
        t = re.sub(r'(<link rel="stylesheet" href="[^"]*css/style\.css[^"]*">)', lambda m: pre + m.group(1), t, count=1)
    # hero preload with srcset
    t = t.replace('<link rel="preload" as="image" href="images/aerial-1.webp" type="image/webp" fetchpriority="high">',
                  '<link rel="preload" as="image" href="images/aerial-1.webp" imagesrcset="images/aerial-1-640.webp 640w, images/aerial-1.webp 1084w" imagesizes="100vw" type="image/webp" fetchpriority="high">')
    # cache-busting + defer
    t = re.sub(r'((?:href|src)="(?:/|(?:\.\./)*)(?:css/style\.css|config\.js|form\.js|index\.js))(?:\?v=[^"]*)?"', lambda m: m.group(1) + f'?v={VER}"', t)
    t = re.sub(r'<script src="([^"]*(?:config|form|index)\.js\?v=[^"]*)"></script>', r'<script src="\1" defer></script>', t)
    t = t.replace('<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>', '<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2" defer></script>')
    return t

def alt_text(t):
    def sub(m):
        v = html.unescape(m.group(1))
        if not v.strip() or "urbania" in v.lower(): return m.group(0)
        return f'alt="{esc("Tanish Urbania: " + v[0].lower() + v[1:])}"'
    return re.sub(r'alt="([^"]*)"', sub, t)

def h1s(t, f):
    if f == "index.html":
        t = t.replace("<h1>Tanish Urbania</h1>", '<h1>Tanish Urbania <span class="h1-loc">Charholi, Pune</span></h1>')
        return t
    if f.startswith(("blog/", "sitemap/")):
        m = re.search(r"<h1>(.*?)</h1>", t, re.S)
        if m and "urbania" not in m.group(1).lower() and "h1-brand" not in m.group(1):
            t = t.replace(m.group(0), f'<h1><span class="h1-brand">{BRAND}</span> {m.group(1)}</h1>', 1)
    return t

def footer_links(t):
    if 'class="footer-links"' in t: return t
    nav = ('<nav class="footer-links" aria-label="Footer"><a href="/">Home</a><a href="/blog/">Guides</a><a href="/blog/project/">Project details</a>'
           '<a href="/blog/project/tanish-urbania-2-and-3-bhk-homes/">2 &amp; 3 BHK homes</a><a href="/sitemap/">Site map</a></nav>')
    return t.replace('<p class="disclaimer">', nav + '\n      <p class="disclaimer">', 1)

def sitewide():
    for f in pages():
        t = rd(f); o = t
        t = head_tweaks(t, f); t = alt_text(t); t = h1s(t, f); t = footer_links(t)
        t = re.sub(r'(<nav class="chips"[^>]*>.*?)(</nav>)', lambda m: m.group(1) if "/blog/project/" in m.group(1) else m.group(1) + ('<a class="chip" href="/blog/project/">Project details</a>' if True else "") + m.group(2), t, flags=re.S)
        t = srcset_pics(t)
        if t != o: wr(f, t)

def srcset_pics(t):
    def sub(m):
        pict = m.group(0)
        if "-640.webp" in pict: return pict
        ms = re.search(r'<source type="image/webp" srcset="(/?(?:\.\./)*)images/([a-z0-9-]+)\.webp">', pict)
        if not ms or not os.path.exists(f"images/{ms.group(2)}-640.webp"): return pict
        pre, base = ms.group(1), ms.group(2); w = Image.open(f"images/{base}.webp").size[0]
        ctx = t[max(0, m.start() - 130):m.start()]
        sizes = "100vw" if "hero-slide" in ctx else ("(max-width: 800px) 100vw, 760px" if "article-img" in pict else "(max-width: 700px) 86vw, 380px")
        return pict.replace(ms.group(0), f'<source type="image/webp" srcset="{pre}images/{base}-640.webp 640w, {pre}images/{base}.webp {w}w" sizes="{sizes}">')
    return re.sub(r"<picture>.*?</picture>", sub, t, flags=re.S)

# ------------------------------------------------------------------ 5. project pages
P = {}
P["tanish-urbania-overview"] = dict(
    img="aerial-1", imgalt="Tanish Urbania: aerial view of the residential wings in Charholi, Pune", tag="Project overview", mins=3,
    t="Tanish Urbania Charholi: Project Overview & Facts",
    h="Tanish Urbania Charholi: project overview",
    d="Tanish Urbania by Tanish Group, Charholi, PCMC, Pune: 12 residential wings, 2 and 3 BHK homes near Ajinkya D.Y. Patil University. Overview and facts.",
    dek="Everything about Tanish Urbania in Charholi in one place: the developer, the wings, the homes and the location.",
    body='''<p>Tanish Urbania is a contemporary residential community in Charholi, in the PCMC area of Pune. It is also searched as Tanish Urbania Charholi or Tanish Urbania PCMC, and this page brings the main facts together.</p>
<h2>Project snapshot</h2>
<div class="tw"><table class="compare"><thead><tr><th>Detail</th><th>Information</th></tr></thead><tbody>
<tr><td>Developer</td><td>Tanish Group</td></tr><tr><td>Architecture</td><td>YW Architects</td></tr>
<tr><td>Location</td><td>Charholi, PCMC, Pune, near Ajinkya D.Y. Patil University</td></tr>
<tr><td>Wings</td><td>12 residential wings</td></tr>
<tr><td>Homes</td><td>2 BHK (approx. 720–770 sq ft) and 3 BHK (approx. 920–980 sq ft)</td></tr>
<tr><td>Pricing</td><td>Shared on enquiry</td></tr></tbody></table></div>
<h2>Design and planning</h2>
<p>The twelve wings are positioned to give open space, daylight and cross ventilation. The architecture is defined by clean geometry, vertical accents and balanced proportions, with generous balconies and a subtle play of colour. Landscaped zones are spread through the master plan so that residents have open areas that bring people together.</p>
<h2>Location</h2>
<p>Charholi is one of the faster-developing pockets of Pimpri-Chinchwad, with new infrastructure and landmark projects emerging around it. Read the <a href="/blog/overview/locality-overview/">Charholi locality overview</a> and the guide to <a href="/blog/location-connectivity/roads-metro-rail-airport/">roads, metro, rail and airport</a>, or check live routes on <a href="https://www.google.com/maps/search/?api=1&amp;query=Tanish+Urbania+Charholi+Pune" target="_blank" rel="noopener">Google Maps</a>.</p>
<h2>Next steps</h2>
<ul><li>Compare the sizes in the <a href="/blog/project/tanish-urbania-2-and-3-bhk-homes/">2 and 3 BHK homes guide</a>.</li><li>Read the <a href="/blog/buying-guides/pre-launch-home-buying-checklist/">checklist for buying before the launch</a>.</li><li>Ask the sales team for the price list, floor plans and RERA registration details.</li></ul>
<p>Information is indicative and subject to change. Please confirm RERA registration details with the sales team before booking.</p>''')
P["tanish-urbania-2-and-3-bhk-homes"] = dict(
    img="elevation-2", imgalt="Tanish Urbania: front elevation of the 2 and 3 BHK towers", tag="2 and 3 BHK homes", mins=3,
    t="Tanish Urbania 2 & 3 BHK Homes: Sizes & Features",
    h="Tanish Urbania 2 and 3 BHK homes: sizes and features",
    d="Tanish Urbania, Charholi: 2 BHK approx. 720–770 sq ft and 3 BHK approx. 920–980 sq ft, with balconies, cross ventilation and daylight. Sizes and questions.",
    dek="The two home types at Tanish Urbania, with approximate sizes, features and the questions to ask before you choose.",
    body='''<p>Tanish Urbania offers two home types in Charholi, PCMC: 2 BHK and 3 BHK. Here is how they compare and what to ask the sales team before you decide.</p>
<h2>Sizes at a glance</h2>
<div class="tw"><table class="compare"><thead><tr><th>Home type</th><th>Approx. size</th><th>Features</th><th>Price</th></tr></thead><tbody>
<tr><td>2 BHK</td><td>720 – 770 sq ft</td><td>Generous balconies, cross ventilation and daylight, efficient well-planned layouts</td><td>On request</td></tr>
<tr><td>3 BHK</td><td>920 – 980 sq ft</td><td>Spacious living for families, generous balconies, cross ventilation and daylight</td><td>On request</td></tr></tbody></table></div>
<p>Areas are approximate. Pricing, floor plans and the brochure are shared on enquiry.</p>
<h2>Which one suits you</h2>
<p>A 2 BHK suits couples, small families and first-time buyers who want an efficient layout. A 3 BHK suits families who want an extra bedroom for children, guests or a home office. For a fuller comparison, read <a href="/blog/buying-guides/2-bhk-vs-3-bhk/">2 BHK or 3 BHK: how to choose the right home</a>.</p>
<h2>Questions to ask before you choose</h2>
<ol><li>Is the stated size carpet area or built-up area?</li><li>Which wings and floors have each home type, and what are the views?</li><li>What is the total package, and what does it include?</li><li>What is the payment schedule, and what is the RERA registration number?</li></ol>
<p>Design matters as much as size. Read how <a href="/blog/buying-guides/light-and-ventilation-in-apartment-design/">light and ventilation</a> shape daily life, and see the <a href="/blog/project/tanish-urbania-overview/">Tanish Urbania project overview</a>.</p>''')
ORDER = list(P)

def build_pages():
    tpl = rd("blog/buying-guides/2-bhk-vs-3-bhk/index.html") if "h1-brand" not in rd("blog/buying-guides/2-bhk-vs-3-bhk/index.html") else rd("blog/buying-guides/2-bhk-vs-3-bhk/index.html")
    cards = ""
    for s in ORDER:
        g = P[s]; t = tpl; path = f"/blog/{CAT}/{s}/"
        body = g["body"]
        m = mins(body)
        t = re.sub(r"<title>.*?</title>", f"<title>{esc(g['t'])}</title>", t, flags=re.S)
        for pat in [r'(<meta name="description" content=")[^"]*', r'(<meta property="og:description" content=")[^"]*', r'(<meta name="twitter:description" content=")[^"]*']:
            t = re.sub(pat, lambda x: x.group(1) + esc(g["d"]), t)
        for pat in [r'(<meta property="og:title" content=")[^"]*', r'(<meta name="twitter:title" content=")[^"]*', r'(<meta property="og:image:alt" content=")[^"]*']:
            t = re.sub(pat, lambda x: x.group(1) + esc(g["t"]), t)
        for pat in [r'(<link rel="canonical" href=")[^"]*', r'(<meta property="og:url" content=")[^"]*', r'(<link rel="alternate" hreflang="[^"]*" href=")[^"]*']:
            t = re.sub(pat, lambda x: x.group(1) + URL + path, t)
        t = re.sub(r'(<meta property="article:published_time" content=")[^"]*', lambda x: x.group(1) + DATE, t)
        t = re.sub(r'(<meta property="article:section" content=")[^"]*', lambda x: x.group(1) + CATNAME, t)
        ld = {"@context": "https://schema.org", "@graph": [
            {"@type": "BlogPosting", "headline": g["h"], "description": g["d"], "image": f"{URL}/images/{g['img']}.jpg", "datePublished": DATE, "dateModified": DATE,
             "mainEntityOfPage": URL + path, "inLanguage": "en-IN", "articleSection": CATNAME,
             "author": {"@type": "Organization", "name": "Tanish Group", "url": URL + "/"},
             "publisher": {"@type": "Organization", "name": "Tanish Group", "logo": {"@type": "ImageObject", "url": URL + "/android-chrome-512x512.png"}},
             "about": {"@id": URL + "/#project"}},
            {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": URL + q} for i, (n, q) in enumerate([("Home", "/"), ("Blog", "/blog/"), (CATNAME, f"/blog/{CAT}/"), (g["h"], path)])]}]}
        t = re.sub(r'<script type="application/ld\+json">.*?</script>', lambda x: '<script type="application/ld+json">\n' + json.dumps(ld, ensure_ascii=False, indent=2) + "\n  </script>", t, count=1, flags=re.S)
        others = [o for o in ORDER if o != s]
        rel = "".join(f'''<a class="post-card" href="/blog/{CAT}/{o}/">
            <picture><source type="image/webp" srcset="/images/{P[o]["img"]}.webp"><img width="1080" height="492" src="/images/{P[o]["img"]}.jpg" alt="{esc(P[o]["imgalt"])}" loading="lazy"></picture>
            <div class="post-meta"><span class="tag">{CATNAME}</span><span>{P[o]["mins"]} min read</span></div>
            <h3>{P[o]["h"][:1].upper()+P[o]["h"][1:]}</h3>
            <p>{P[o]["dek"]}</p>
            <span class="read-more">Read article &rarr;</span>
          </a>''' for o in others)
        art = f'''<article class="article">
      <div class="container narrow">
        <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/blog/">Blog</a> / <a href="/blog/{CAT}/">{CATNAME}</a></nav>
        <div class="post-meta"><a class="tag" href="/blog/{CAT}/">{CATNAME}</a><span>{m} min read</span></div>
        <h1>{g["h"][:1].upper()+g["h"][1:]}</h1>
        <p class="byline">By <a href="/">Tanish Group</a> &middot; Published <time datetime="{DATE}">26 November 2026</time> &middot; Updated <time datetime="{DATE}">26 November 2026</time></p>
        <picture><source type="image/webp" srcset="/images/{g["img"]}.webp"><img class="article-img" fetchpriority="high" width="1080" height="492" src="/images/{g["img"]}.jpg" alt="{esc(g["imgalt"])}"></picture>
        <div class="article-body">{body}</div>
        <div class="cta-box">
          <h3>Interested in Tanish Urbania?</h3>
          <p>2 BHK and 3 BHK Elite Homes in Charholi, PCMC. Register to get pricing and floor plans.</p>
          <a class="btn btn-primary" href="/#contact">Enquire Now</a>
        </div>
      </div>
      <div class="container related">
        <h2>Keep reading</h2>
        <div class="post-grid two">
          {rel}
          <a class="post-card" href="/blog/{CAT}/">
            <picture><source type="image/webp" srcset="/images/aerial-2.webp"><img width="1080" height="492" src="/images/aerial-2.jpg" alt="All Tanish Urbania project guides" loading="lazy"></picture>
            <div class="post-meta"><span class="tag">{CATNAME}</span></div>
            <h3>All Tanish Urbania project guides</h3>
            <p>Project overview, home sizes and features in one place.</p>
            <span class="read-more">View all &rarr;</span>
          </a>
        </div>
      </div>
    </article>'''
        t = re.sub(r'<article class="article">.*?</article>', lambda x: art, t, count=1, flags=re.S)
        wr(f"blog/{CAT}/{s}/index.html", t)
    # category page cloned from the buying-guides category page
    t = rd("blog/buying-guides/index.html"); path = f"/blog/{CAT}/"
    title = "Tanish Urbania Project Details | Charholi, Pune"
    desc = "Tanish Urbania, Charholi, PCMC: project overview, 2 and 3 BHK sizes and features, and what to ask before you choose. By Tanish Group."
    t = re.sub(r"<title>.*?</title>", f"<title>{esc(title)}</title>", t, flags=re.S)
    for pat in [r'(<meta name="description" content=")[^"]*', r'(<meta property="og:description" content=")[^"]*', r'(<meta name="twitter:description" content=")[^"]*']:
        t = re.sub(pat, lambda x: x.group(1) + esc(desc), t)
    for pat in [r'(<meta property="og:title" content=")[^"]*', r'(<meta name="twitter:title" content=")[^"]*', r'(<meta property="og:image:alt" content=")[^"]*']:
        t = re.sub(pat, lambda x: x.group(1) + esc(title), t)
    for pat in [r'(<link rel="canonical" href=")[^"]*', r'(<meta property="og:url" content=")[^"]*', r'(<link rel="alternate" hreflang="[^"]*" href=")[^"]*']:
        t = re.sub(pat, lambda x: x.group(1) + URL + path, t)
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "CollectionPage", "name": CATNAME, "url": URL + path, "inLanguage": "en-IN", "hasPart": [{"@type": "BlogPosting", "headline": P[s]["h"], "url": f"{URL}/blog/{CAT}/{s}/"} for s in ORDER]},
        {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": URL + q} for i, (n, q) in enumerate([("Home", "/"), ("Blog", "/blog/"), (CATNAME, path)])]}]}
    t = re.sub(r'<script type="application/ld\+json">.*?</script>', lambda x: '<script type="application/ld+json">\n' + json.dumps(ld, ensure_ascii=False, indent=2) + "\n  </script>", t, count=1, flags=re.S)
    t = re.sub(r'<span>Buying Guides</span></nav>', f'<span>{CATNAME}</span></nav>', t, count=1)
    t = re.sub(r"<h1>.*?</h1>", f'<h1><span class="h1-brand">{BRAND}</span> Project details: overview, homes and features</h1>', t, count=1, flags=re.S)
    t = re.sub(r'<p class="lead">.*?</p>', '<p class="lead">The facts about Tanish Urbania in Charholi, PCMC: the developer, the wings, the 2 and 3 BHK homes, and what to ask before you choose.</p>', t, count=1, flags=re.S)
    t = re.sub(r'<div class="cat-intro">.*?</div>', '<div class="cat-intro"><p>Tanish Urbania is a contemporary residential community by Tanish Group in Charholi, Pune, with twelve residential wings and 2 and 3 BHK homes. These pages gather the project facts in one place and point to the buying and locality guides.</p></div>', t, count=1, flags=re.S)
    t = t.replace('<a class="chip active" href="/blog/buying-guides/">Buying Guides</a>', '<a class="chip" href="/blog/buying-guides/">Buying Guides</a>')
    t = t.replace('<a class="chip" href="/blog/project/">Project details</a>', '<a class="chip active" href="/blog/project/">Project details</a>')
    grid = "".join(f'''<a class="post-card" href="/blog/{CAT}/{s}/">
            <picture><source type="image/webp" srcset="/images/{P[s]["img"]}.webp"><img width="1080" height="492" src="/images/{P[s]["img"]}.jpg" alt="{esc(P[s]["imgalt"])}" loading="lazy"></picture>
            <div class="post-meta"><span class="tag">{CATNAME}</span><span>{P[s]["mins"]} min read</span></div>
            <h3>{P[s]["h"][:1].upper()+P[s]["h"][1:]}</h3>
            <p>{P[s]["dek"]}</p>
            <span class="read-more">Read article &rarr;</span>
          </a>''' for s in ORDER)
    t = re.sub(r'(<div class="post-grid">).*?(</div>\s*</div></section>)', lambda x: x.group(1) + "\n" + grid + "\n      " + x.group(2), t, count=1, flags=re.S)
    wr(f"blog/{CAT}/index.html", t)

def hub_links():
    # blog hub: topic card, chip (done in sitewide) and two article cards
    t = rd("blog/index.html")
    if f"/blog/{CAT}/" not in t.replace('class="chip" href="/blog/project/"', ""):
        card = f'<a class="cat-card" href="/blog/{CAT}/"><h3>{CATNAME}</h3><p>Overview, home sizes and features</p><span class="count">{len(ORDER)} articles</span></a>'
        t = t.replace('<div class="cat-grid">', '<div class="cat-grid">' + card, 1)
    if f"/blog/{CAT}/{ORDER[0]}/" not in t:
        g = "".join(f'''<a class="post-card" href="/blog/{CAT}/{s}/">
            <picture><source type="image/webp" srcset="/images/{P[s]["img"]}.webp"><img width="1080" height="492" src="/images/{P[s]["img"]}.jpg" alt="{esc(P[s]["imgalt"])}" loading="lazy"></picture>
            <div class="post-meta"><span class="tag">{CATNAME}</span><span>{P[s]["mins"]} min read</span></div>
            <h3>{P[s]["h"][:1].upper()+P[s]["h"][1:]}</h3>
            <p>{P[s]["dek"]}</p>
            <span class="read-more">Read article &rarr;</span>
          </a>''' for s in ORDER)
        t = t.replace('<div class="post-grid">', '<div class="post-grid">' + g, 1)
    wr("blog/index.html", t)
    # home page: guides teaser + project quick links
    t = rd("index.html")
    if "/blog/project/" not in t.replace('href="/blog/project/"', "x") or 'class="gl-quick"' not in t:
        q = ('<p class="center gl-quick"><a href="/blog/project/tanish-urbania-overview/">Project overview</a><a href="/blog/project/tanish-urbania-2-and-3-bhk-homes/">2 &amp; 3 BHK homes</a>'
             '<a href="/blog/nearby-schools/schools-and-colleges/">Schools nearby</a><a href="/blog/nearby-hospitals/hospitals-and-healthcare/">Hospitals nearby</a><a href="/sitemap/">Site map</a></p>')
        t = t.replace('<p class="center more"><a class="btn btn-ghost-dark" href="blog/">View all articles</a></p>', q + '\n      <p class="center more"><a class="btn btn-ghost-dark" href="blog/">View all articles</a></p>', 1)
        c = rd("css/style.css")
        if ".gl-quick" not in c:
            wr("css/style.css", c + "\n.gl-quick{display:flex;flex-wrap:wrap;justify-content:center;gap:8px;margin:18px 0 6px}.gl-quick a{font-size:.85rem;font-weight:500;color:var(--navy);background:#fff;border:1px solid var(--line);border-radius:999px;padding:.45em 1em;text-decoration:none}.gl-quick a:hover{border-color:var(--brick);color:var(--brick)}\n")
        wr("index.html", t)

def sitemap_page():
    t = rd("blog/buying-guides/index.html"); path = "/sitemap/"
    title = "Site Map | Tanish Urbania, Charholi"; desc = "Site map of Tanish Urbania, Charholi, Pune: the project page, home sizes, FAQ and every guide in one place."
    t = re.sub(r"<title>.*?</title>", f"<title>{esc(title)}</title>", t, flags=re.S)
    for pat in [r'(<meta name="description" content=")[^"]*', r'(<meta property="og:description" content=")[^"]*', r'(<meta name="twitter:description" content=")[^"]*']:
        t = re.sub(pat, lambda x: x.group(1) + esc(desc), t)
    for pat in [r'(<meta property="og:title" content=")[^"]*', r'(<meta name="twitter:title" content=")[^"]*', r'(<meta property="og:image:alt" content=")[^"]*']:
        t = re.sub(pat, lambda x: x.group(1) + esc(title), t)
    for pat in [r'(<link rel="canonical" href=")[^"]*', r'(<meta property="og:url" content=")[^"]*', r'(<link rel="alternate" hreflang="[^"]*" href=")[^"]*']:
        t = re.sub(pat, lambda x: x.group(1) + URL + path, t)
    ld = {"@context": "https://schema.org", "@graph": [{"@type": "WebPage", "name": "Site map", "url": URL + path}, {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Home", "item": URL + "/"}, {"@type": "ListItem", "position": 2, "name": "Site map", "item": URL + path}]}]}
    t = re.sub(r'<script type="application/ld\+json">.*?</script>', lambda x: '<script type="application/ld+json">\n' + json.dumps(ld, ensure_ascii=False, indent=2) + "\n  </script>", t, count=1, flags=re.S)
    groups = {}
    for f in sorted(glob.glob("blog/*/*/index.html")):
        c = f.split("/")[1]; h = re.search(r"<h1>(.*?)</h1>", rd(f), re.S).group(1)
        h = re.sub(r"<[^>]+>", "", re.sub(r'<span class="h1-brand">.*?</span>', "", h)).strip()
        groups.setdefault(c, []).append(("/" + f[:-10], html.unescape(h)))
    names = {"project": CATNAME, "overview": "Pune & Charholi overview", "location-connectivity": "Location & connectivity", "investment": "Investment", "nearby-schools": "Nearby schools & colleges", "nearby-hospitals": "Nearby hospitals", "nearby-it-hubs": "Nearby employment & IT hubs", "nearby-malls": "Nearby malls & shopping", "buying-guides": "Buying guides"}
    sec = lambda h, items: f'<section><h2>{esc(h)}</h2><ul>' + "".join(f'<li><a href="{u}">{esc(n)}</a></li>' for u, n in items) + "</ul></section>"
    main_ = [("/", "Tanish Urbania: home page"), ("/#homes", "2 & 3 BHK homes"), ("/#gallery", "Gallery"), ("/#location", "Location"), ("/#faq", "FAQ"), ("/#contact", "Enquire and register interest"), ("/blog/", "All guides")]
    body = '<div class="smap">' + sec("Tanish Urbania, Charholi", main_) + "".join(sec(names.get(c, c), [(f"/blog/{c}/", "All " + names.get(c, c).lower())] + items) for c, items in sorted(groups.items(), key=lambda kv: (kv[0] != "project", kv[0]))) + "</div>"
    t = re.sub(r'<main class="blog-main">.*?</main>', lambda x: f'<main class="blog-main"><section class="blog-hero"><div class="container"><nav class="crumbs light" aria-label="Breadcrumb"><a href="/">Home</a> / <span>Site map</span></nav><p class="section-label">Find anything</p><h1><span class="h1-brand">{BRAND}</span> Site map</h1><p class="lead">Every page of Tanish Urbania in one place.</p></div></section><section class="section"><div class="container">{body}</div></section></main>', t, count=1, flags=re.S)
    wr("sitemap/index.html", t)

# ------------------------------------------------------------------ 6. structured data, sitemap.xml, htaccess
def schema():
    t = rd("index.html"); pat = r'(<script type="application/ld\+json">)(.*?)(</script>)'
    m = re.search(pat, t, re.S); d = json.loads(m.group(2)); g = d["@graph"]
    for x in g:
        if x.get("@type") == "ApartmentComplex" and "@id" not in x: x["@id"] = URL + "/#project"
        if x.get("@type") == "Organization" and "@id" not in x: x["@id"] = URL + "/#org"
    have = {x.get("@id") for x in g}
    def img(n, f, cap):
        w, h = Image.open(f"images/{f}").size
        return {"@type": "ImageObject", "@id": f"{URL}/#img-{n}", "url": f"{URL}/images/{f}", "contentUrl": f"{URL}/images/{f}", "width": w, "height": h, "caption": cap, "inLanguage": "en-IN"}
    imgs = [img("aerial", "aerial-1.jpg", "Tanish Urbania: aerial view of the residential wings in Charholi, Pune"), img("elevation", "elevation-1.jpg", "Tanish Urbania: modern elevation of the apartments in Charholi, Pune"),
            img("courtyard", "courtyard.jpg", "Tanish Urbania: view from a balcony over the landscaped courtyard")]
    new = imgs + [
        {"@type": "BreadcrumbList", "@id": URL + "/#breadcrumb", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Tanish Urbania, Charholi, Pune", "item": URL + "/"}]},
        {"@type": "ItemList", "@id": URL + "/#projectpages", "name": "Tanish Urbania project pages and guides", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": P[s]["h"][:1].upper() + P[s]["h"][1:], "url": f"{URL}/blog/{CAT}/{s}/"} for i, s in enumerate(ORDER)]},
        {"@type": "Place", "@id": URL + "/#place", "name": "Tanish Urbania, Charholi, PCMC, Pune", "hasMap": "https://www.google.com/maps/search/?api=1&query=Tanish+Urbania+Charholi+Pune",
         "address": {"@type": "PostalAddress", "addressLocality": "Charholi, Pimpri-Chinchwad", "addressRegion": "Maharashtra", "addressCountry": "IN"}}]
    for node in new:
        if node["@id"] not in have: g.append(node)
    for x in g:
        if x.get("@id") == URL + "/#org" and "contactPoint" not in x:
            x["contactPoint"] = {"@type": "ContactPoint", "contactType": "sales", "telephone": "+917264011256", "areaServed": "IN", "availableLanguage": ["en", "hi", "mr"]}
        if x.get("@type") == "ApartmentComplex" and "containedInPlace" not in x:
            x["containedInPlace"] = {"@id": URL + "/#place"}; x["image"] = [{"@id": i["@id"]} for i in imgs]
        if x.get("@type") == "WebPage" and "breadcrumb" not in x:
            x["breadcrumb"] = {"@id": URL + "/#breadcrumb"}; x["about"] = {"@id": URL + "/#project"}
    wr("index.html", t[:m.start()] + m.group(1) + json.dumps(d, ensure_ascii=False, indent=2) + m.group(3) + t[m.end():])
    # every guide: link the article to the project
    for f in glob.glob("blog/**/index.html", recursive=True):
        tt = rd(f); mm = re.search(pat, tt, re.S)
        if not mm: continue
        dd = json.loads(mm.group(2)); ch = False
        for x in dd.get("@graph", []):
            if x.get("@type") == "BlogPosting" and "about" not in x: x["about"] = {"@id": URL + "/#project"}; ch = True
        if ch: wr(f, tt[:mm.start()] + mm.group(1) + json.dumps(dd, ensure_ascii=False, indent=2) + mm.group(3) + tt[mm.end():])

def sitemap_xml():
    sm = rd("sitemap.xml")
    add = ["/sitemap/", f"/blog/{CAT}/"] + [f"/blog/{CAT}/{s}/" for s in ORDER]
    for u in add:
        if URL + u not in sm: sm = sm.replace("</urlset>", f"  <url>\n    <loc>{URL}{u}</loc>\n    <lastmod>{DATE}</lastmod>\n  </url>\n</urlset>")
    wr("sitemap.xml", sm)

def htaccess():
    wr(".htaccess", """# Tanish Urbania: Apache/LiteSpeed rules for Hostinger
RewriteEngine On
RewriteCond %{HTTPS} off [OR]
RewriteCond %{HTTP_HOST} ^www\\. [NC]
RewriteCond %{HTTP_HOST} ^(?:www\\.)?(.+)$ [NC]
RewriteRule ^ https://%1%{REQUEST_URI} [L,R=301]

ErrorDocument 404 /404.html
Options -Indexes

<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/css application/javascript application/json application/ld+json application/xml image/svg+xml
</IfModule>

<IfModule mod_expires.c>
  ExpiresActive On
  ExpiresByType image/webp "access plus 1 year"
  ExpiresByType image/jpeg "access plus 1 year"
  ExpiresByType image/png "access plus 1 year"
  ExpiresByType image/x-icon "access plus 1 year"
  ExpiresByType font/woff2 "access plus 1 year"
  ExpiresByType text/css "access plus 1 day"
  ExpiresByType application/javascript "access plus 1 day"
  ExpiresByType text/html "access plus 0 seconds"
</IfModule>

<IfModule mod_headers.c>
  Header set X-Content-Type-Options "nosniff"
  Header set X-Frame-Options "SAMEORIGIN"
  Header set Referrer-Policy "strict-origin-when-cross-origin"
</IfModule>
""")

if __name__ == "__main__":
    images(); icons(); fonts(); build_pages(); hub_links(); sitemap_page(); sitewide(); schema(); sitemap_xml(); htaccess()
    print("done")
