import re
from scholarly import scholarly

USER_ID = "oloLqe4AAAAJ"  # Replace with your Google Scholar user ID
CITATION_BADGE_PATTERN = (
    r"(https://img\.shields\.io/badge/Google%20Scholar-)"
    r"(?:\d+|<!--\s*CITATION_COUNT\s*-->)"
    r"(-[0-9A-Fa-f]{6})"
)

# Fetch profile and fill publications
profile = scholarly.search_author_id(USER_ID)
profile = scholarly.fill(profile)
citation_count = profile['citedby']

# Build sorted publications list (most recent first)
publications = profile.get('publications', [])
rows = []
for pub in publications:
    bib = pub.get('bib', {})
    title = bib.get('title', 'N/A')
    year = bib.get('pub_year', 'N/A')
    cited_by = pub.get('num_citations', 0)
    author_pub_id = pub.get('author_pub_id', '')
    if author_pub_id:
        url = (
            f"https://scholar.google.com/citations"
            f"?view_op=view_citation&hl=en&user={USER_ID}"
            f"&citation_for_view={author_pub_id}"
        )
    else:
        url = f"https://scholar.google.com/citations?user={USER_ID}&hl=en"
    rows.append((title, year, cited_by, url))

def _year_key(r):
    try:
        return int(r[1])
    except ValueError:
        return 0

rows.sort(key=_year_key, reverse=True)

# Build Markdown table
table_lines = [
    "| # | Title | Year | Citations |",
    "|---|-------|------|-----------|",
]
for i, (title, year, cited_by, url) in enumerate(rows, 1):
    table_lines.append(f"| {i} | [{title}]({url}) | {year} | {cited_by} |")

footer = (
    f"\n*Auto-updated every 3 hours via GitHub Actions · "
    f"[View full list on Google Scholar](https://scholar.google.com/citations?user={USER_ID}&hl=en)*\n"
)
pub_block = "\n".join(table_lines) + footer

# Read the README file
with open("README.md", "r", encoding="utf-8") as readme_file:
    readme_content = readme_file.read()

# Replace the citation count placeholder or existing count in the badge URL
readme_content, badge_subs = re.subn(
    CITATION_BADGE_PATTERN,
    rf"\1{citation_count}\2",
    readme_content,
)
if badge_subs == 0:
    print("Warning: citation badge URL not found; attempting placeholder replacement.")
    readme_content = readme_content.replace("<!-- CITATION_COUNT -->", str(citation_count))

# Replace the publications block between markers
readme_content = re.sub(
    r"<!-- PUBLICATIONS_START -->.*?<!-- PUBLICATIONS_END -->",
    f"<!-- PUBLICATIONS_START -->\n{pub_block}<!-- PUBLICATIONS_END -->",
    readme_content,
    flags=re.DOTALL,
)

# Save changes to README.md
with open("README.md", "w", encoding="utf-8") as readme_file:
    readme_file.write(readme_content)

print(f"README.md updated: {citation_count} citations, {len(rows)} publications.")

