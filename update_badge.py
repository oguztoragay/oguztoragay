import re
from scholarly import scholarly

USER_ID = "oloLqe4AAAAJ"  # Replace with your Google Scholar user ID

# Fetch the citation count
profile = scholarly.search_author_id(USER_ID)
profile = scholarly.fill(profile)
citation_count = profile['citedby']

# Read the README file
with open("README.md", "r", encoding="utf-8") as readme_file:
    readme_content = readme_file.read()

# Replace the placeholder with the actual citation count
new_readme_content = readme_content.replace("<!-- CITATION_COUNT -->", str(citation_count))

# Save changes to README.md
with open("README.md", "w", encoding="utf-8") as readme_file:
    readme_file.write(new_readme_content)

print(f"README.md updated with citation count: {citation_count}")

