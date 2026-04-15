#!/bin/zsh

set -e

MESSAGE="${1:-update site}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "This directory is not a git repository."
  exit 1
fi

if [ -z "$(git status --porcelain)" ]; then
  echo "No changes to deploy."
  exit 0
fi

git add .
git commit -m "$MESSAGE"
git push

echo ""
echo "Deployment pushed to GitHub."
echo "Render will auto-deploy the latest commit."
