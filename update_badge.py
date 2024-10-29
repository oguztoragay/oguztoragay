import re
from scholarly import scholarly

USER_ID = "oloLqe4AAAAJ"  # Replace this with your actual Google Scholar user ID

# Fetch the citation count
profile = scholarly.search_author_id(USER_ID)
profile = scholarly.fill(profile)
citation_count = profile['citedby']

# Read the README file
with open("README.md", "r", encoding="utf-8") as readme_file:
    readme_content = readme_file.read()

# Update the badge URL with the new citation count
new_badge_url = f"https://img.shields.io/badge/Citations-{citation_count}-4285F4?style=flat&logo=google-scholar&logoColor=white"
updated_readme_content = re.sub(
    r"https://img\.shields\.io/badge/Citations-\d+-4285F4\?style=flat&logo=google-scholar&logoColor=white",
    new_badge_url,
    readme_content
)

# Save changes to README.md
with open("README.md", "w", encoding="utf-8") as readme_file:
    readme_file.write(updated_readme_content)
