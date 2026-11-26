---
description: Write a feature spec for the next Spendly step
argument-hint: <step-number> <feature-name>  (e.g. 03 login-and-logout)
allowed-tools: Read, Glob, Grep, Write, Bash(git status:*), Bash(git log:*), Bash(ls:*)
---

Write a spec for: $ARGUMENTS

The first word of the arguments is the step number (two digits, e.g. `03`) and the
rest is the feature name in kebab-case. Save the spec to
`.claude/specs/<step-number>-<feature-name>.md`. If that file already exists and is
not empty, stop and ask before overwriting it.

## 1. Gather context (read before writing)

- `CLAUDE.md` for the project conventions.
- Every existing spec in `.claude/specs/`, especially the most recent one. Match its
  layout and level of detail, and don't repeat work an earlier spec already covers.
- `app.py`: what is implemented and which placeholder routes mention this step
  (strings like `"... coming in Step N"`).
- `database/db.py` for the schema and the `get_db()`, `init_db()` and `seed_db()`
  helpers.
- The templates, CSS and JS the feature will touch, plus `templates/base.html`.
- `tests/conftest.py` and the existing tests, so the spec's test plan uses the
  existing fixtures.

Don't change any code. This command only writes the spec.

## 2. Write the spec

Use these sections, in this order:

1. `# Spec <NN> — <Feature title>`
2. `## Goal`: two or three sentences on what the user can do afterwards.
3. `## Scope`: an "In scope" bullet and an "Out of scope" bullet. Name the later steps
   that handle out-of-scope items where you know them.
4. `## Files touched`: each file and what changes in it. Say explicitly whether the
   schema changes.
5. `## Behaviour`: one subsection per route (`### GET /path`, `### POST /path`) or
   per UI piece. Give numbered steps. Put validation rules in a table with the check,
   the exact error message and the HTTP status. Say where each success path redirects.
6. `## Implementation notes`: imports, helpers to add or reuse, parameterized SQL,
   `try/finally` around connections, and any trap in the existing code (for example,
   seed data that doesn't satisfy a new rule).
7. `## Acceptance criteria`: a `- [ ]` checklist that can be tested. Always end with
   "All existing tests in `tests/` still pass."
8. `## Tests (tests/test_<feature>.py, pytest + pytest-flask)`: the cases to cover,
   using the fixtures in `conftest.py`.

## 3. Rules for the content

- Follow the stub comments and step numbering already in the code. Don't invent a
  different structure.
- Use exact error messages, status codes, route names and `url_for` endpoint names
  that match `app.py`.
- Security defaults: hash passwords with werkzeug, use `?` placeholders in SQL, never
  echo a password back into a template, and don't reveal whether an account exists.
- UI changes reuse the CSS variables in `static/css/style.css`. Page-specific styles
  go in their own CSS file loaded through the `head` block.
- Money is shown in Indian rupees (₹).
- Make the decisions yourself. Don't leave open questions in the spec unless a choice
  really needs the user.

## 4. Report back

Give the spec's path and a short summary of the main decisions: anything you chose
that the existing code didn't already dictate, and what you left out of scope.
