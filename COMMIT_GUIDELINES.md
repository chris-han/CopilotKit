# Commit Message Guidelines

This repository uses [Conventional Commits](https://www.conventionalcommits.org/) format for commit messages, enforced by commitlint.

## Format

Commit messages must follow this format:

```
<type>(<scope>): <subject>
```

- **type**: The type of change (required)
- **scope**: The scope of the change (optional)
- **subject**: A brief description of the change (required)

### Types

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, missing semicolons, etc)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `build`: Changes to build system or dependencies
- `ci`: Changes to CI configuration files and scripts
- `chore`: Other changes that don't modify src or test files
- `revert`: Reverts a previous commit

### Examples

```
feat: add user authentication
fix: resolve navigation bug
docs: update README with installation steps
ci(commitlint): add commit message template
refactor(api): simplify error handling
```

## Tools to Help You

### 1. Interactive Commit Helper (Recommended)

Use the interactive commit helper script:

```bash
pnpm commit
```

This will guide you through creating a properly formatted commit message.

### 2. Git Commit Template

When you run `git commit` (without `-m`), you'll see a template with instructions in your editor.

### 3. Manual Commits

If you prefer to write commit messages manually, just follow the format:

```bash
git commit -m "feat: add new feature"
```

## Validation

All commits are validated:
- **Locally**: When you commit (via husky hook)
- **CI/CD**: In pull requests and pushes to main

If your commit message doesn't follow the format, you'll see an error like:
```
✖   subject may not be empty [subject-empty]
✖   type may not be empty [type-empty]
```

## Resources

- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [commitlint Documentation](https://github.com/conventional-changelog/commitlint)
