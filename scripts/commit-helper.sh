#!/bin/bash

# Commit Helper Script
# This script helps create conventional commit messages

echo "🎯 Conventional Commit Helper"
echo "=============================="
echo ""
echo "Select a commit type:"
echo "1) feat     - A new feature"
echo "2) fix      - A bug fix"
echo "3) docs     - Documentation only changes"
echo "4) style    - Code style changes (formatting, missing semi colons, etc)"
echo "5) refactor - Code change that neither fixes a bug nor adds a feature"
echo "6) perf     - Performance improvements"
echo "7) test     - Adding or updating tests"
echo "8) build    - Changes to build system or dependencies"
echo "9) ci       - Changes to CI configuration files and scripts"
echo "10) chore   - Other changes that don't modify src or test files"
echo "11) revert  - Reverts a previous commit"
echo ""

read -p "Enter number (1-11): " type_num

case $type_num in
  1) TYPE="feat";;
  2) TYPE="fix";;
  3) TYPE="docs";;
  4) TYPE="style";;
  5) TYPE="refactor";;
  6) TYPE="perf";;
  7) TYPE="test";;
  8) TYPE="build";;
  9) TYPE="ci";;
  10) TYPE="chore";;
  11) TYPE="revert";;
  *) echo "Invalid selection"; exit 1;;
esac

read -p "Enter commit subject (brief description): " SUBJECT

if [ -z "$SUBJECT" ]; then
  echo "Error: Subject cannot be empty"
  exit 1
fi

read -p "Enter scope (optional, press Enter to skip): " SCOPE

if [ -n "$SCOPE" ]; then
  COMMIT_MSG="${TYPE}(${SCOPE}): ${SUBJECT}"
else
  COMMIT_MSG="${TYPE}: ${SUBJECT}"
fi

echo ""
echo "Generated commit message:"
echo "  $COMMIT_MSG"
echo ""
read -p "Do you want to commit with this message? (y/n): " confirm

if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
  git commit -m "$COMMIT_MSG"
  echo "✅ Committed successfully!"
else
  echo "❌ Commit cancelled"
  exit 1
fi
