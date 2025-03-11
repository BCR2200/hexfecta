#!/usr/bin/env bash

. setup.bash

python tba_awards_scraper.py

# Check if there are any changes in the repository
if [[ -n $(git status -s) ]]; then
	echo "Changes detected in the repository"

	# Stage all changes
	git add .

	# Create a commit with timestamp
	commit_message="Auto update: $(date '+%Y-%m-%d %H:%M:%S')"
	git commit -m "$commit_message"

	# Push changes
	echo "Pushing changes to remote repository..."
	git push origin HEAD
	git push origin main:gh-pages

	echo "Successfully committed and pushed changes"
else
	echo "No changes detected in the repository"
fi

