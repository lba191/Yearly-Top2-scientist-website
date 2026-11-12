from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


for path in (ROOT / "dist").glob("*.html"):
    text = path.read_text(encoding="utf-8")
    author_credit = (
        '<div class="author-credit" aria-label="Site author">'
        '<strong>Bian Liu</strong>'
        '<span class="author-role">PhD student · Department of Building Environment and Energy Engineering</span>'
        '<span class="author-university">The Hong Kong Polytechnic University (PolyU)</span>'
        '<a class="author-email" href="mailto:bi-an.liu@connect.polyu.hk">bi-an.liu@connect.polyu.hk</a>'
        '</div>'
    )
    if 'class="author-credit"' not in text:
        text = text.replace('</a><nav class="nav">', f'</a>{author_credit}<nav class="nav">')
    text = re.sub(r'assets/styles\.css(?:\?v=\d+)?', 'assets/styles.css?v=12', text)
    text = re.sub(
        r'<a(?: class="active")? href="rankings\.html">Rankings</a>',
        '<a href="downloads.html">Downloads</a>',
        text,
    )
    text = re.sub(r'assets/app\.js(?:\?v=\d+)?', 'assets/app.js?v=12', text)
    path.write_text(text, encoding="utf-8")


scientists = ROOT / "dist" / "scientists.html"
text = scientists.read_text(encoding="utf-8")
text = text.replace(
    "Search more than 408,000 conservatively linked profiles and inspect rank, citation, index, and affiliation changes across releases.",
    "Search conservatively linked profiles using full names, initials, joined names, reordered names, or partial name combinations.",
)
text = text.replace(
    "Type at least two letters of a name…",
    "Try Ling Tim Wong, L.T. Wong, Wong LT, or a partial name…",
)
text = text.replace(
    "Try Ling Tim Wong, L.T. Wong, Wong LT, or a partial name…",
    "Search by scientist name…",
)
scientists.write_text(text, encoding="utf-8")


overview = ROOT / "dist" / "index.html"
text = overview.read_text(encoding="utf-8")
text = text.replace("<h2>Leading institutions</h2>", "<h2>Institution representation</h2>")
text = text.replace(
    '<p class="note">Complete counts for the selected release.</p><div id="institutions"></div>',
    '<p class="note" id="institution-total">All ranked affiliations for the selected release.</p><div id="institutions"></div>',
)
text = text.replace(
    '<p class="note">Complete affiliation-country counts.</p><div id="countries"></div>',
    '<p class="note" id="country-total">All affiliation-country counts.</p><div id="countries"></div>',
)
text = text.replace(
    '<p class="note">Leading broad fields in the complete release.</p><div id="fields"></div>',
    '<p class="note" id="field-total">All broad fields in the complete release.</p><div id="fields"></div>',
)
overview.write_text(text, encoding="utf-8")
