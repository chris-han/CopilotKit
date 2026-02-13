# Branch Synchronization Tools

This directory contains tools to help sync branches between a fork and the upstream repository.

## Files

### BRANCH_SYNC_ANALYSIS.md
Detailed analysis of the current branch sync issue between the fork and upstream repository. This document explains:
- Current state of branches
- Root cause of sync issues
- Recommendations for fixing the issue

### scripts/sync-branch-with-upstream.sh
Interactive script to sync a local branch with an upstream branch.

## How to Sync Your Branch

### Option 1: Using the Interactive Script

1. Make sure you have the upstream remote configured:
   ```bash
   git remote add upstream https://github.com/CopilotKit/CopilotKit.git
   ```

2. Run the sync script:
   ```bash
   ./scripts/sync-branch-with-upstream.sh feat/re-architecture-monorepo main
   ```

3. Choose one of the sync options:
   - **Option 1 (Merge)**: Preserves all commit history. Best if you have local commits you want to keep.
   - **Option 2 (Rebase)**: Creates a cleaner history. May cause conflicts if there are divergent changes.
   - **Option 3 (Reset)**: Completely replaces your branch with upstream. **WARNING**: This destroys any local commits!

4. Push the changes:
   ```bash
   git push origin feat/re-architecture-monorepo --force-with-lease
   ```

### Option 2: Manual Sync

#### To Merge Upstream Changes

```bash
# Fetch latest changes
git fetch upstream main
git fetch origin

# Checkout your branch
git checkout feat/re-architecture-monorepo

# Merge upstream/main
git merge upstream/main

# Push changes
git push origin feat/re-architecture-monorepo
```

#### To Rebase on Upstream

```bash
# Fetch latest changes
git fetch upstream main
git fetch origin

# Checkout your branch
git checkout feat/re-architecture-monorepo

# Rebase on upstream/main
git rebase upstream/main

# Push changes (force push required after rebase)
git push origin feat/re-architecture-monorepo --force-with-lease
```

#### To Reset Branch to Upstream (Destructive)

```bash
# Fetch latest changes
git fetch upstream main

# Checkout your branch
git checkout feat/re-architecture-monorepo

# Reset to upstream/main (destroys local commits!)
git reset --hard upstream/main

# Force push to origin
git push origin feat/re-architecture-monorepo --force
```

## Understanding the Current Issue

The `feat/re-architecture-monorepo` branch in the fork is:
- **1 commit behind** `upstream/main`
- Missing the actual monorepo re-architecture changes (PR #3187)
- Does not have an upstream branch to track (the branch only exists in the fork)

### Why This Happened

The monorepo re-architecture was completed and merged into the main branch of CopilotKit/CopilotKit. However, the `feat/re-architecture-monorepo` branch in the fork was not updated with these changes.

### Recommended Action

**Merge or rebase the branch with `upstream/main`** to include the latest monorepo re-architecture changes:

```bash
./scripts/sync-branch-with-upstream.sh feat/re-architecture-monorepo main
```

Then choose Option 1 (Merge) or Option 2 (Rebase) depending on your preference.

## Checking Branch Status

To check if your branch is in sync with upstream:

```bash
# Fetch latest
git fetch upstream main

# Check commits behind
git rev-list --count feat/re-architecture-monorepo..upstream/main

# Check commits ahead
git rev-list --count upstream/main..feat/re-architecture-monorepo
```

If both return `0`, your branch is in sync!

## Best Practices

1. **Regularly sync with upstream**: Keep your branches up-to-date by regularly merging or rebasing from upstream.

2. **Use --force-with-lease**: When force-pushing, use `--force-with-lease` instead of `--force` to avoid accidentally overwriting others' work.

3. **Communicate with team**: Before force-pushing a shared branch, make sure others on your team are aware.

4. **Backup important work**: Before using destructive operations like reset, create a backup branch:
   ```bash
   git checkout -b feat/re-architecture-monorepo-backup feat/re-architecture-monorepo
   ```

## Troubleshooting

### Error: "upstream remote not found"
```bash
git remote add upstream https://github.com/CopilotKit/CopilotKit.git
```

### Error: "Your branch and 'origin/...' have diverged"
This happens after a rebase. Use `--force-with-lease` to push:
```bash
git push origin feat/re-architecture-monorepo --force-with-lease
```

### Merge Conflicts
If you encounter conflicts during merge or rebase:
1. Resolve conflicts in the files marked
2. Stage resolved files: `git add <file>`
3. Continue:
   - For merge: `git merge --continue`
   - For rebase: `git rebase --continue`

Or abort the operation:
- For merge: `git merge --abort`
- For rebase: `git rebase --abort`
