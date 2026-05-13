import re
import time
from typing import Any, Callable, Iterable

from scholarly import scholarly

USER_ID = "oloLqe4AAAAJ"  # Replace with your Google Scholar user ID
BADGE_PREFIX_PATTERN = r"https://img\.shields\.io/badge/Google%20Scholar-"
BADGE_SUFFIX_PATTERN = (
    r"-(?:[0-9A-Fa-f]{3}(?:[0-9A-Fa-f]{3})?|[A-Za-z]+)(?:\?[^)\s]+)?"
)
CITATION_BADGE_PATTERN = (
    rf"(?P<prefix>{BADGE_PREFIX_PATTERN})"
    rf"(?P<count>\d+)"
    rf"(?P<suffix>{BADGE_SUFFIX_PATTERN})"
)
PUBLICATIONS_PATTERN = r"<!-- PUBLICATIONS_START -->.*?<!-- PUBLICATIONS_END -->"

MAX_RETRIES = 3
RETRY_DELAYS = (2, 5, 10)


def retry(operation_name: str, func: Callable[[], Any], delays: Iterable[int] = RETRY_DELAYS) -> Any:
    attempts = [0, *list(delays)]
    last_error = None
    for attempt, delay in enumerate(attempts, start=1):
        try:
            return func()
        except Exception as exc:
            last_error = exc
            if attempt == len(attempts):
                break
            print(
                f"{operation_name} failed on attempt {attempt}/{len(attempts)}: {exc}. "
                f"Retrying in {delay}s..."
            )
            time.sleep(delay)
    raise RuntimeError(f"{operation_name} failed after {len(attempts)} attempts") from last_error


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


def fetch_profile(user_id: str) -> dict[str, Any]:
    profile = retry("search_author_id", lambda: scholarly.search_author_id(user_id))
    profile = retry("fill profile", lambda: scholarly.fill(profile))
    print(f"Profile keys: {sorted(profile.keys())}")
    return profile


def build_publication_rows(profile: dict[str, Any], user_id: str) -> list[tuple[str, Any, int, str]]:
    publications = profile.get("publications", [])
    print(f"Found {len(publications)} publications in profile.")
    rows = []

    for index, pub in enumerate(publications, start=1):
        try:
            pub = retry(f"fill publication #{index}", lambda pub=pub: scholarly.fill(pub))
        except Exception as exc:
            print(f"Warning: failed to fill publication #{index}: {exc}")

        bib = pub.get("bib", {}) if isinstance(pub, dict) else {}
        title = bib.get("title", "N/A")
        year = bib.get("pub_year", "N/A")
        cited_by = safe_int(pub.get("num_citations", 0)) if isinstance(pub, dict) else 0
        author_pub_id = pub.get("author_pub_id", "") if isinstance(pub, dict) else ""

        if author_pub_id:
            url = (
                f"https://scholar.google.com/citations"
                f"?view_op=view_citation&hl=en&user={user_id}"
                f"&citation_for_view={author_pub_id}"
            )
        else:
            url = f"https://scholar.google.com/citations?user={user_id}&hl=en"

        rows.append((title, year, cited_by, url))

    def year_key(row: tuple[str, Any, int, str]) -> int:
        return safe_int(row[1], default=0)

    rows.sort(key=year_key, reverse=True)
    return rows


def build_publications_block(rows: list[tuple[str, Any, int, str]], user_id: str) -> str:
    table_lines = [
        "| # | Title | Year | Citations |",
        "|---|-------|------|-----------|",
    ]

    for i, (title, year, cited_by, url) in enumerate(rows, 1):
        safe_title = str(title).replace("|", "\\|").replace("\n", " ").strip()
        safe_year = str(year).replace("|", "\\|").replace("\n", " ").strip()
        table_lines.append(f"| {i} | [{safe_title}]({url}) | {safe_year} | {cited_by} |")

    footer = (
        "\n*Auto-updated every 3 hours via GitHub Actions · "
        f"[View full list on Google Scholar](https://scholar.google.com/citations?user={user_id}&hl=en)*\n"
    )
    return "\n".join(table_lines) + footer


def update_readme(readme_content: str, citation_count: int, pub_block: str) -> str:
    updated_content, badge_subs = re.subn(
        CITATION_BADGE_PATTERN,
        rf"\g<prefix>{citation_count}\g<suffix>",
        readme_content,
    )
    if badge_subs == 0:
        print("Warning: citation badge URL not found; attempting placeholder replacement.")
        updated_content = updated_content.replace("<!-- CITATION_COUNT -->", str(citation_count))

    updated_content, pub_subs = re.subn(
        PUBLICATIONS_PATTERN,
        f"<!-- PUBLICATIONS_START -->\n{pub_block}<!-- PUBLICATIONS_END -->",
        updated_content,
        flags=re.DOTALL,
    )
    if pub_subs == 0:
        raise RuntimeError(
            "Could not find publications markers in README.md. "
            "Expected <!-- PUBLICATIONS_START --> and <!-- PUBLICATIONS_END -->"
        )

    return updated_content


def main() -> None:
    profile = fetch_profile(USER_ID)
    citation_count = safe_int(profile.get("citedby", 0))
    rows = build_publication_rows(profile, USER_ID)
    pub_block = build_publications_block(rows, USER_ID)

    with open("README.md", "r", encoding="utf-8") as readme_file:
        readme_content = readme_file.read()

    updated_content = update_readme(readme_content, citation_count, pub_block)

    with open("README.md", "w", encoding="utf-8") as readme_file:
        readme_file.write(updated_content)

    print(f"README.md updated: {citation_count} citations, {len(rows)} publications.")


if __name__ == "__main__":
    main()
