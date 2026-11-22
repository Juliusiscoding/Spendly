# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Spendly is a Flask expense-tracker built as a step-by-step teaching project. Much of the app is intentionally unimplemented: placeholder routes in `app.py` return strings like `"Add expense — coming in Step 7"`, and `database/db.py` and `static/js/main.js` are stubs whose comments describe what each step should add. When implementing a feature, follow the step numbering and the contract described in those stub comments rather than inventing a different structure.

The currency throughout the UI is Indian rupees (₹).

## Commands

A virtualenv lives at `.venv/` (Windows layout: `.venv/Scripts/`).

```bash
# Install dependencies
.venv/Scripts/python -m pip install -r requirements.txt

# Run the dev server (debug mode, http://localhost:5001)
.venv/Scripts/python app.py

# Tests (pytest + pytest-flask are installed; no tests/ directory exists yet)
.venv/Scripts/python -m pytest
.venv/Scripts/python -m pytest path/to/test_file.py::test_name
```

There is no linter or build step configured.

## Architecture

- **`app.py`** — the entire Flask app: a single module-level `app` object with all routes. No blueprints or app factory. Routes are split into implemented pages (`/`, `/register`, `/login`, `/terms`, `/privacy`) and student placeholder routes (`/logout`, `/profile`, `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete`).
- **`database/db.py`** — to be written in Step 1. Expected API: `get_db()` (SQLite connection with `row_factory` and foreign keys enabled), `init_db()` (`CREATE TABLE IF NOT EXISTS` for all tables), `seed_db()` (sample dev data). The SQLite file `expense_tracker.db` is gitignored.
- **Templates** — every page extends `templates/base.html`, which provides the navbar, footer, Google Fonts, `style.css`, and `main.js`. Blocks: `title`, `head` (page-specific CSS), `content`, `scripts` (page-specific JS). Always link with `url_for(...)`, matching the endpoint function names in `app.py`.
- **Auth templates** — `login.html` and `register.html` already contain `method="POST"` forms (fields `email`, `password`, etc.) and render an `{{ error }}` variable, but the corresponding routes currently only handle GET. Wiring them up means adding POST handling and passing `error` to `render_template`.
- **Styling** — `static/css/style.css` defines the design tokens in `:root` (`--ink*`, `--paper*`, `--accent*`, `--danger*`, `--radius-*`, `--font-display`/`--font-body`) plus shared components (navbar, footer, auth forms). Reuse these variables instead of hard-coding colors. Page-specific styles go in a separate file loaded via the `head` block (e.g. `landing.css`, whose classes use an `lp-` prefix).
- **JavaScript** — page-specific behavior is written inline in the template's `scripts` block as a vanilla-JS IIFE (see the YouTube modal in `landing.html`); no frameworks or bundler.

## Conventions

- Commit messages use an `area: description` prefix, e.g. `landing: add privacy policy page and route`.
