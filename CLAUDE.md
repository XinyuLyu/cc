# CLAUDE.md

This file provides guidance to AI assistants (Claude and others) working with this repository. It documents the project structure, development workflows, and conventions to follow.

---

## Project Overview

> **Note:** This repository is currently in its initial state. Update this section with a description of the project once development begins.

- **Repository:** XinyuLyu/cc
- **Purpose:** _[Describe the project purpose here]_
- **Primary Language:** _[e.g., TypeScript, Python, Go]_
- **Framework/Runtime:** _[e.g., Node.js, React, Django]_

---

## Repository Structure

```
cc/
├── CLAUDE.md          # This file — AI assistant guidance
├── README.md          # Project overview for humans
├── src/               # Main source code
├── tests/             # Test files
├── docs/              # Documentation
└── ...
```

> Update this tree as the project evolves.

---

## Development Setup

### Prerequisites

_List required tools and versions here. Example:_

```bash
node >= 20
npm >= 10
# or
python >= 3.11
# or
go >= 1.22
```

### Initial Setup

```bash
git clone <repo-url>
cd cc

# Install dependencies (update for your package manager)
npm install        # Node.js
# pip install -r requirements.txt   # Python
# go mod download                   # Go
```

### Environment Variables

```bash
cp .env.example .env
# Fill in required values in .env
```

List required environment variables and their purpose:

| Variable | Required | Description |
|----------|----------|-------------|
| _TBD_    | Yes      | _Description_ |

---

## Common Commands

Update these commands once the project toolchain is established.

### Running the Project

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm start            # Start production server
```

### Testing

```bash
npm test             # Run all tests
npm run test:watch   # Run tests in watch mode
npm run test:coverage # Run tests with coverage
```

### Linting & Formatting

```bash
npm run lint         # Check for lint errors
npm run lint:fix     # Auto-fix lint errors
npm run format       # Format code (e.g., Prettier)
npm run typecheck    # TypeScript type checking
```

---

## Git Workflow

### Branch Naming

Branches follow this naming convention:

```
<type>/<short-description>
```

Types:
- `feat/` — new features
- `fix/` — bug fixes
- `chore/` — maintenance tasks
- `docs/` — documentation-only changes
- `refactor/` — code restructuring without behavior changes
- `test/` — adding or updating tests

AI-generated branches use the prefix `claude/` (e.g., `claude/feature-name-<id>`).

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary>

[optional body]

[optional footer(s)]
```

**Types:** `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `style`, `perf`, `ci`

**Examples:**
```
feat(auth): add OAuth2 login support
fix(api): handle null response from user endpoint
docs: update setup instructions in README
```

- Use the **imperative mood** in the summary ("add" not "adds" or "added")
- Keep the summary line under 72 characters
- Reference issues in the footer: `Closes #123`

### Pull Requests

- Keep PRs focused and small — one logical change per PR
- Write a clear description of what changed and why
- Include test coverage for new functionality
- Ensure CI passes before requesting review

---

## Code Conventions

_Update this section with project-specific conventions once the stack is chosen._

### General Principles

- **Simplicity over cleverness** — write code that is easy to read and understand
- **DRY but not over-abstracted** — avoid premature abstractions
- **Fail fast** — validate inputs early and surface errors clearly
- **No dead code** — remove unused code rather than commenting it out

### Naming

| Construct     | Convention       | Example                   |
|---------------|-----------------|---------------------------|
| Files         | kebab-case       | `user-profile.ts`         |
| Classes       | PascalCase       | `UserProfile`             |
| Functions      | camelCase        | `getUserProfile()`        |
| Constants     | SCREAMING_SNAKE  | `MAX_RETRY_COUNT`         |
| Types/Interfaces | PascalCase    | `UserProfileResponse`     |

### Error Handling

- Prefer explicit error types over generic `Error`
- Always handle promise rejections
- Log errors with enough context to debug (avoid exposing sensitive data)
- Distinguish between expected errors (user input) and unexpected errors (bugs)

### Security

- Never commit secrets, API keys, or credentials
- Validate all external input at system boundaries
- Use parameterized queries to prevent SQL injection
- Sanitize output to prevent XSS
- Keep dependencies up to date; audit regularly with `npm audit` / equivalent

---

## Testing Conventions

_Update this section based on the testing framework chosen._

### Philosophy

- Aim for high confidence, not 100% coverage for its own sake
- Test behavior, not implementation details
- Unit tests for pure functions and business logic
- Integration tests for API endpoints and database interactions
- End-to-end tests for critical user flows

### File Organization

```
tests/
├── unit/            # Unit tests (mirror src/ structure)
├── integration/     # Integration tests
└── e2e/             # End-to-end tests
```

Test files co-located with source:
```
src/
├── user.ts
└── user.test.ts     # or user.spec.ts
```

### Test Naming

```
describe('UserService', () => {
  describe('getUser', () => {
    it('returns user when found', () => { ... })
    it('throws NotFoundError when user does not exist', () => { ... })
  })
})
```

---

## AI Assistant Guidelines

### When Making Changes

1. **Read before editing** — always read a file before modifying it
2. **Minimal changes** — only change what is necessary for the task
3. **No unsolicited refactoring** — do not clean up surrounding code unless asked
4. **No feature creep** — implement exactly what was requested
5. **No unnecessary comments** — only add comments where logic is non-obvious

### When Adding Code

- Follow existing patterns in the codebase
- Match the surrounding code style exactly
- Run lint and tests before committing
- Do not add `console.log` / debug statements to committed code

### When Exploring

- Use `Glob` and `Grep` for targeted searches
- Read key configuration files to understand the project setup
- Check `package.json` (or equivalent) for scripts and dependencies

### What to Avoid

- **Do not** add error handling for impossible cases
- **Do not** introduce backwards-compatibility shims unless required
- **Do not** create helper utilities for one-off operations
- **Do not** add type annotations or docstrings to code you didn't change
- **Do not** use feature flags unless explicitly requested
- **Do not** design for hypothetical future requirements

### Risky Operations — Always Confirm First

- Deleting files or directories
- Force-pushing or resetting git history
- Modifying CI/CD pipelines
- Dropping or migrating database tables
- Pushing to `main` or `master`

---

## CI/CD

_Update this section once CI/CD is configured._

### Pipeline Overview

| Stage       | Tool          | Trigger               |
|-------------|---------------|-----------------------|
| Lint        | _TBD_         | Every push/PR         |
| Test        | _TBD_         | Every push/PR         |
| Build       | _TBD_         | Every push/PR         |
| Deploy      | _TBD_         | Merge to main         |

### Required Checks

All PRs must pass:
- [ ] Lint
- [ ] Type checking
- [ ] All tests
- [ ] Build succeeds

---

## Dependencies

### Adding Dependencies

- Prefer well-maintained packages with broad adoption
- Check bundle size impact for frontend packages
- Pin major versions; allow minor/patch updates
- Document why a non-obvious dependency was added

### Removing Dependencies

- Ensure nothing still imports the package before removing
- Update lock file and commit it alongside `package.json`

---

## Troubleshooting

_Populate this section with common issues and their solutions as they are discovered._

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| _TBD_   | _TBD_       | _TBD_    |

---

## Changelog

| Date       | Author | Change                        |
|------------|--------|-------------------------------|
| 2026-02-27 | Claude | Initial CLAUDE.md created     |
