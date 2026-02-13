# Tax Newsletter Migration Guide

This guide explains how to populate the `utilities/tax-newsletter` submodule with the tax newsletter code that was previously in the CopilotKit repository.

## Overview

The tax newsletter functionality has been moved to a separate repository (`chris-han/KATPN_rss`) and added as a git submodule at `utilities/tax-newsletter/`.

## Steps to Populate the Submodule

### 1. Navigate to the submodule directory

```bash
cd utilities/tax-newsletter
```

### 2. Extract files from the CopilotKit repository

The complete tax newsletter implementation is preserved in commit `0e74fcd` of the CopilotKit repository. You can extract the files using one of these methods:

#### Method A: Extract files individually (from CopilotKit root)

```bash
# From the CopilotKit root directory
cd /path/to/CopilotKit

# Extract the source files
git show 0e74fcd:utilities/tax-newsletter/package.json > /path/to/utilities/tax-newsletter/package.json
git show 0e74fcd:utilities/tax-newsletter/tsconfig.json > /path/to/utilities/tax-newsletter/tsconfig.json
git show 0e74fcd:utilities/tax-newsletter/config.yml > /path/to/utilities/tax-newsletter/config.yml
git show 0e74fcd:utilities/tax-newsletter/.gitignore > /path/to/utilities/tax-newsletter/.gitignore
git show 0e74fcd:utilities/tax-newsletter/README.md > /path/to/utilities/tax-newsletter/README.md

# Extract the source directory
mkdir -p /path/to/utilities/tax-newsletter/src
git show 0e74fcd:utilities/tax-newsletter/src/index.ts > /path/to/utilities/tax-newsletter/src/index.ts

# Extract the workflow (optional - can be kept in main repo or moved to submodule)
git show 0e74fcd:.github/workflows/tax_newsletter.yml > /path/to/utilities/tax-newsletter/.github/workflows/tax_newsletter.yml

# Extract newsletters directory (optional - for reference)
mkdir -p /path/to/utilities/tax-newsletter/newsletters
git show 0e74fcd:newsletters/README.md > /path/to/utilities/tax-newsletter/newsletters/README.md
```

#### Method B: Use git archive (cleaner approach)

```bash
# From the CopilotKit root directory
cd /path/to/CopilotKit

# Create a temporary directory
mkdir -p /tmp/tax-newsletter-extract

# Extract just the tax-newsletter directory
git archive 0e74fcd utilities/tax-newsletter | tar -x -C /tmp/tax-newsletter-extract

# Copy to the submodule
cp -r /tmp/tax-newsletter-extract/utilities/tax-newsletter/* utilities/tax-newsletter/

# Clean up
rm -rf /tmp/tax-newsletter-extract
```

### 3. Commit and push to the KATPN_rss repository

```bash
cd utilities/tax-newsletter

# Add all files
git add .

# Commit
git commit -m "feat: add US-China tax regulations newsletter generator

Initial implementation including:
- TypeScript utility for fetching tax updates from IRS, Treasury, and China sources
- RSS feed and web scraping capabilities
- GitHub Actions workflow for automated weekly generation
- Markdown newsletter output"

# Push to the remote repository
git push origin main
```

### 4. Update the submodule reference in CopilotKit

```bash
# From the CopilotKit root directory
cd /path/to/CopilotKit

# Update the submodule reference
git add utilities/tax-newsletter

# Commit the updated reference
git commit -m "chore: update tax-newsletter submodule to include implementation"

# Push
git push
```

## File Structure in the Submodule

After migration, the submodule should have this structure:

```
utilities/tax-newsletter/
├── .github/
│   └── workflows/
│       └── tax_newsletter.yml    # GitHub Actions workflow
├── src/
│   └── index.ts                  # Main TypeScript source
├── newsletters/                   # Optional: output directory
├── .gitignore
├── README.md
├── config.yml                     # Data sources configuration
├── package.json
├── package-lock.json             # Generated after npm install
└── tsconfig.json
```

## Updating the GitHub Action Workflow

If you keep the workflow in the submodule, you may need to update the paths in `.github/workflows/tax_newsletter.yml`:

```yaml
- name: Install dependencies
  working-directory: ./utilities/tax-newsletter
  run: npm ci

- name: Generate newsletter
  working-directory: ./utilities/tax-newsletter
  run: npm run generate
```

## Notes

- The submodule is currently empty and points to the `chris-han/KATPN_rss` repository
- The original implementation is preserved in CopilotKit's commit `0e74fcd`
- After populating the submodule, users will need to run `git submodule update --init --recursive` when cloning CopilotKit
- The newsletter will continue to work independently in its own repository
