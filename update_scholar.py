import re
import time
from typing import Any, Callable, Iterable

from scholarly import scholarly, ProxyGenerator

USER_ID = "oloLqe4AAAAJ"
BADGE_PREFIX_PATTERN = r"https://img\.shields\.io/badge/Google%20Scholar-"
BADGE_SUFFIX_PATTERN = (
    r"-(?:[0-9A-Fa-f]{3}(?:[0-9A-Fa-f]{3})?|[A-Za-z]+)(?:\?[^)\s]+)?"
)
CITATION_BADGE_PATTERN = (
    rf"(?P<prefix>{BADGE_PREFIX_PATTERN})"
    rf"(?P<count>\d+)"
    rf"(?P<suffix>{BADGE_SUFFIX_PATTERN})"
)

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


def fetch_citation_count(user_id: str) -> int:
    pg = ProxyGenerator()
    pg.FreeProxies()
    scholarly.use_proxy(pg)

    profile = retry("search_author_id", lambda: scholarly.search_author_id(user_id))
    profile = retry("fill profile", lambda: scholarly.fill(profile, sections=["basics"]))
    citation_count = safe_int(profile.get("citedby", 0))
    print(f"Citation count: {citation_count}")
    return citation_count


def update_readme(readme_content: str, citation_count: int) -> str:
    updated_content, badge_subs = re.subn(
        CITATION_BADGE_PATTERN,
        rf"\g<prefix>{citation_count}\g<suffix>",
        readme_content,
    )
    if badge_subs == 0:
        print("Warning: citation badge URL not found; attempting placeholder replacement.")
        updated_content = updated_content.replace("<!-- CITATION_COUNT -->", str(citation_count))

    return updated_content


def main() -> None:
    citation_count = fetch_citation_count(USER_ID)

    with open("README.md", "r", encoding="utf-8") as readme_file:
        readme_content = readme_file.read()

    updated_content = update_readme(readme_content, citation_count)

    with open("README.md", "w", encoding="utf-8") as readme_file:
        readme_file.write(updated_content)

    print(f"README.md updated: {citation_count} citations.")


if __name__ == "__main__":
    main()
