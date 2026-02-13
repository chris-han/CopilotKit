#!/bin/bash

# Script to sync a branch with upstream repository
# Usage: ./sync-branch-with-upstream.sh <branch-name> [upstream-branch]

set -e

BRANCH_NAME="${1:-feat/re-architecture-monorepo}"
UPSTREAM_BRANCH="${2:-main}"
UPSTREAM_REMOTE="upstream"
ORIGIN_REMOTE="origin"

echo "============================="
echo "Branch Sync Script"
echo "============================="
echo "Branch: $BRANCH_NAME"
echo "Upstream Branch: $UPSTREAM_BRANCH"
echo "============================="

# Check if upstream remote exists
if ! git remote | grep -q "^${UPSTREAM_REMOTE}$"; then
    echo "Error: Upstream remote '${UPSTREAM_REMOTE}' not found."
    echo "Please add it with: git remote add upstream https://github.com/CopilotKit/CopilotKit.git"
    exit 1
fi

# Fetch latest changes
echo "Fetching latest changes..."
git fetch "$UPSTREAM_REMOTE" "$UPSTREAM_BRANCH"
git fetch "$ORIGIN_REMOTE"

# Check if branch exists locally
if git rev-parse --verify "$BRANCH_NAME" >/dev/null 2>&1; then
    echo "Branch $BRANCH_NAME exists locally"
else
    echo "Branch $BRANCH_NAME does not exist locally. Creating it..."
    if git rev-parse --verify "${ORIGIN_REMOTE}/${BRANCH_NAME}" >/dev/null 2>&1; then
        git checkout -b "$BRANCH_NAME" "${ORIGIN_REMOTE}/${BRANCH_NAME}"
    else
        echo "Branch does not exist on origin either. Creating from upstream/${UPSTREAM_BRANCH}..."
        git checkout -b "$BRANCH_NAME" "${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH}"
    fi
fi

# Checkout the branch
git checkout "$BRANCH_NAME"

# Show current status
echo ""
echo "Current status:"
COMMITS_BEHIND=$(git rev-list --count ${BRANCH_NAME}..${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH})
COMMITS_AHEAD=$(git rev-list --count ${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH}..${BRANCH_NAME})
echo "  - $COMMITS_BEHIND commits behind ${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH}"
echo "  - $COMMITS_AHEAD commits ahead of ${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH}"

if [ "$COMMITS_BEHIND" -eq 0 ] && [ "$COMMITS_AHEAD" -eq 0 ]; then
    echo ""
    echo "✓ Branch is already in sync with ${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH}"
    exit 0
fi

echo ""
echo "Options:"
echo "  1. Merge upstream/${UPSTREAM_BRANCH} into $BRANCH_NAME (preserves commit history)"
echo "  2. Rebase $BRANCH_NAME on upstream/${UPSTREAM_BRANCH} (cleaner history, may cause conflicts)"
echo "  3. Reset $BRANCH_NAME to upstream/${UPSTREAM_BRANCH} (DESTRUCTIVE: loses all branch commits)"
echo "  4. Cancel"
echo ""
read -p "Choose an option (1-4): " OPTION

case $OPTION in
    1)
        echo "Merging ${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH} into $BRANCH_NAME..."
        git merge "${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH}" -m "Merge ${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH} into $BRANCH_NAME"
        echo ""
        echo "✓ Merge complete!"
        ;;
    2)
        echo "Rebasing $BRANCH_NAME on ${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH}..."
        git rebase "${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH}"
        echo ""
        echo "✓ Rebase complete!"
        ;;
    3)
        echo "WARNING: This will DESTROY all commits on $BRANCH_NAME that are not in ${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH}"
        read -p "Are you sure? (yes/no): " CONFIRM
        if [ "$CONFIRM" = "yes" ]; then
            git reset --hard "${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH}"
            echo ""
            echo "✓ Branch reset complete!"
        else
            echo "Cancelled."
            exit 1
        fi
        ;;
    4)
        echo "Cancelled."
        exit 0
        ;;
    *)
        echo "Invalid option."
        exit 1
        ;;
esac

echo ""
echo "To push changes to origin, run:"
echo "  git push origin $BRANCH_NAME --force-with-lease"
echo ""
echo "Done!"
