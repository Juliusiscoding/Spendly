# Spec 04 — Profile page design

## Goal
Give a signed-in user a finished, styled `/profile` page: an identity card with their
initials, name, email and join date, a summary of their spending in rupees with this
month's figure featured, and their five most recent expenses with colour-coded category
pills. The page works from a phone up to a desktop and is the place mobile users log
out from.

## Scope
- In scope: `templates/profile.html` and `static/css/profile.css` (both rebuilt from
  scratch), a two-column layout that collapses to one column, the identity card, three
  summary tiles, the recent-expenses table with category pills, the empty state, and
  `tests/test_profile.py` covering both the route and the rendered markup.
- Already done and not changed here: the `login_required` decorator, `format_inr` /
  the `inr` filter, `_initials`, the `profile()` route and its queries, and the login
  redirects to `/profile` (all in `app.py`, commit `5f54728`).
- Out of scope: editing the name, email or password, deleting the account, profile
  photos, charts or a category breakdown, filtering or paging the expense list, and
  adding, editing or deleting expenses (Steps 7, 8 and 9). Expense rows have no edit or
  delete links yet; the "Add expense" buttons lead to the Step 7 placeholder.

## Files touched
- `templates/profile.html` (new): extends `base.html`, loads `profile.css` in the
  `head` block and Lucide icons (pinned `lucide@1.81.0` from unpkg) plus a
  `lucide.createIcons()` IIFE in the `scripts` block. Lucide is loaded on this page
  only; `base.html` is unchanged.
- `static/css/profile.css` (new): every class prefixed `pf-`.
- `tests/test_profile.py` (new).
- `app.py`: no changes. The template uses only the variables the route already passes.
- `static/css/style.css`, `templates/base.html`: no changes.
- No schema changes.

## Behaviour

### `GET /profile` (existing, unchanged)
For reference, the template receives exactly these variables:

| Variable          | Type / example                                                       |
|-------------------|----------------------------------------------------------------------|
| `user`            | row with `name`, `email`                                             |
| `initials`        | `"AR"` (from `_initials`, `"?"` for a blank name)                    |
| `member_since`    | `"November 2026"`                                                    |
| `total_spent`     | float, all-time sum                                                  |
| `month_spent`     | float, current calendar month                                        |
| `expense_count`   | int                                                                  |
| `recent_expenses` | up to 5 dicts: `display_date` (`"05 Nov 2026"`), `category`, `description`, `amount` |

Error paths stay as implemented: signed out → 302 to `/login`; session for a deleted
user → session cleared, 302 to `/login`. There are no forms on this page, so there is
no validation table.

### Page structure (`profile.html`)
`{% block title %}Profile · Spendly{% endblock %}`. Markup, top to bottom:

```
<section class="pf-section">
  <div class="pf-inner">
    <header class="pf-page-header"> eyebrow + heading </header>
    <div class="pf-layout">
      <aside class="pf-identity"> … </aside>
      <div class="pf-main"> stats + recent </div>
    </div>
  </div>
</section>
```

1. **Page header (`.pf-page-header`)**
   - `.pf-eyebrow`: "Your profile", styled like the existing `.hero-badge` pill
     (`--accent-light` background, `--accent` text, uppercase, 0.75rem, `999px` radius).
   - `<h1 class="pf-title">`: "Welcome back, {{ user.name }}" in `--font-display`,
     `clamp(1.5rem, 4vw, 2rem)`.
2. **Identity card (`<aside class="pf-card pf-identity">`)**
   - `.pf-avatar`: 72px circle showing `initials`, `--accent` background, `--paper`
     text, `--font-display` 1.5rem, `aria-hidden="true"`.
   - `.pf-name` (`<h2>`, `--font-display`, 1.25rem): `user.name`.
   - `.pf-email` (`--ink-muted`, 0.875rem, `overflow-wrap: anywhere` so long addresses
     don't overflow): `user.email`.
   - A `--border-soft` divider, then `<dl class="pf-details">` with one row:
     "Member since" / `member_since`. Labels uppercase 0.75rem `--ink-muted`.
   - A full-width "Log out" link, class `btn-ghost pf-logout`, to `url_for('logout')`.
     This is the only log-out control under 600px, where the navbar hides non-CTA links.
3. **Summary tiles (`.pf-stats`)**: three `.pf-stat` cards, in this order:
   | Modifier          | Label (`.pf-stat-label`) | Value (`.pf-stat-value`)        |
   |-------------------|--------------------------|---------------------------------|
   | `pf-stat--feature`| This month               | `month_spent \| inr`            |
   | —                 | Total spent              | `total_spent \| inr`            |
   | —                 | Expenses recorded        | `expense_count` (plain integer) |
   - Values `--font-display` 1.5rem, `font-variant-numeric: tabular-nums`.
   - `pf-stat--feature` is inverted: `--ink` background, `--paper` value text,
     `--ink-faint` label, and a 3px `--accent-2` top border.
4. **Recent expenses (`.pf-card .pf-recent`)**
   - `.pf-recent-header`: `<h2 class="pf-card-title">Recent expenses</h2>` left; when
     `recent_expenses` is non-empty, a `btn-primary` "Add expense" link to
     `url_for('add_expense')` right.
   - With expenses: `<div class="pf-table-wrap"><table class="pf-table">` with columns
     Date, Category, Description, Amount (`<th class="pf-amount">`).
     - Date: `expense.display_date`, `--ink-muted`, `white-space: nowrap`.
     - Category: `<span class="pf-pill pf-pill--{{ tone }}">{{ expense.category }}</span>`
       where `tone` comes from a fixed map in the template (see Implementation notes).
     - Description: the text, or `—` when empty or `None`.
     - Amount: `expense.amount | inr`, class `pf-amount` (right-aligned, tabular
       numbers, weight 600).
     - `<thead>` uppercase 0.75rem `--ink-muted`; rows separated by `--border-soft`;
       row hover background `--paper`.
   - Empty state (no `recent_expenses`): instead of the header button and table,
     `.pf-empty` — a dashed `--border` box, centred, with `<p>` "No expenses yet.",
     a muted line "Start tracking where your rupees go.", and a `btn-primary` link
     "Add your first expense" to `url_for('add_expense')`. Tiles still read `₹0.00`,
     `₹0.00`, `0`.

### Category pill tones
| Category                         | Class              | Background / text                 |
|----------------------------------|--------------------|-----------------------------------|
| Food                             | `pf-pill--green`   | `--accent-light` / `--accent`     |
| Bills, Shopping                  | `pf-pill--amber`   | `--accent-2-light` / `--accent-2` |
| Health                           | `pf-pill--red`     | `--danger-light` / `--danger`     |
| Anything else (Transport, Entertainment, Other, unknown) | `pf-pill--neutral` | `--paper-warm` / `--ink-soft` |

Pills: `--radius-sm`, 0.75rem, weight 500, `padding: 0.25rem 0.75rem`, `white-space: nowrap`.

### Icons (Lucide)
Each icon is `<i data-lucide="…" aria-hidden="true"></i>` next to a visible text label,
so the page still reads correctly if the CDN fails. One icon per label, no more:

| Where                        | Icon        |
|------------------------------|-------------|
| "Member since" label         | `calendar`  |
| Log out button               | `log-out`   |
| "This month" tile label      | `calendar`  |
| "Total spent" tile label     | `wallet`    |
| "Expenses recorded" label    | `receipt`   |
| "Recent expenses" heading    | `clock`     |
| Add expense buttons          | `plus`      |
| Empty state (32px, muted)    | `receipt`   |

Sizes: 16px inline with text, 20px in buttons, 32px in the empty state.

### Layout and responsive rules (`profile.css`)
- `.pf-section`: `padding: 3rem 2rem 5rem`. `.pf-inner`: `max-width: var(--max-width)`,
  centred.
- `.pf-page-header`: `margin-bottom: 2rem`.
- `.pf-layout`: `display: grid; grid-template-columns: 300px 1fr; gap: 1.5rem;
  align-items: start`. `.pf-identity` is `position: sticky; top: 88px` (60px navbar +
  28px).
- `.pf-main`: `display: grid; gap: 1.5rem`. `.pf-stats`: 3 equal columns, `gap: 1rem`.
- `.pf-card`, `.pf-stat`: `--paper-card` background, 1px `--border`,
  `--radius-md`, padding 1.5rem, and a subtle shadow
  `0 1px 2px rgba(0,0,0,0.04), 0 1px 3px rgba(0,0,0,0.06)` (the only literal colours
  allowed).
- Font sizes stay on the scale 0.75 / 0.875 / 1 / 1.25 / 1.5 / 2rem; spacing on the
  4px grid (0.25, 0.5, 0.75, 1, 1.5, 2, 2.5, 3rem). These follow
  `.claude/skills/frontend-design/SKILLS.md`.
- `@media (max-width: 900px)`: `.pf-layout` one column, `.pf-identity` not sticky and
  laid out as a row (avatar left, text right, log-out button full width below).
- `@media (max-width: 768px)`: `.pf-table-wrap` `overflow-x: auto`; the Description
  column (`.pf-col-desc`) is hidden.
- `@media (max-width: 600px)`: `.pf-section` padding `2rem 1rem 4rem`; `.pf-stats`
  one column.

## Implementation notes
- No new Python. Don't add imports, helpers or queries to `app.py`; if the template
  seems to need a value the route doesn't pass, derive it in Jinja.
- Tone map in the template, set once before the loop:
  `{% set tones = {"Food": "green", "Bills": "amber", "Shopping": "amber", "Health": "red"} %}`
  then `{% set tone = tones.get(expense.category, "neutral") %}`. Never build a class
  name from the raw category string; it is user data and may contain spaces.
- Jinja autoescapes `user.name`, `user.email`, `category` and `description`; don't use
  `|safe` anywhere.
- Use `{{ expense.description or "—" }}` so both `""` and `None` show the dash.
- Use the `inr` filter for every money value; never format amounts by hand or
  hard-code `₹` next to a number.
- Colours, radii and fonts come only from the `:root` variables in `style.css`. No new
  hex values (the shadow `rgba` values above are the one exception).
- Pin Lucide to an exact version (`lucide@1.81.0`), never `@latest`, and guard the call:
  `(function () { if (window.lucide) { lucide.createIcons(); } })();`.
- Mark the Description `<th>` and each description `<td>` with `class="pf-col-desc"`
  for the mobile rule.
- Seed data trap: the demo account's expenses are all dated in the current month, so
  "This month" equals "Total spent" there. That is expected. Tests use the empty temp
  DB from `conftest.py` and insert their own rows, including one outside the month.
- Trap: with `profile.html` deleted, any request to `/profile` raises
  `TemplateNotFound` today. Nothing in `tests/test_login.py` renders `/profile` (it
  only checks redirect `Location`), which is why the suite still passes.

## Acceptance criteria
- [ ] Signed out, `GET /profile` redirects to `/login`; a stale session is cleared and
      redirected to `/login`.
- [ ] Signed in, `GET /profile` returns 200 with title "Profile · Spendly" and loads
      `css/profile.css`.
- [ ] The identity card shows the initials avatar, name, email and "Member since
      <Month YYYY>", plus a "Log out" link to `/logout`.
- [ ] Tiles show This month, Total spent and Expenses recorded, in that order, with
      ₹ and Indian grouping (e.g. `₹1,23,456.50`); other users' expenses are excluded.
- [ ] At most five recent expenses, newest first; an empty description shows `—`.
- [ ] Category pills use the tone map: Food green, Bills/Shopping amber, Health red,
      anything else neutral.
- [ ] A user with no expenses sees "No expenses yet.", an "Add your first expense"
      link to `/expenses/add`, `₹0.00` totals, and no table.
- [ ] HTML in a description or name is escaped, not rendered.
- [ ] Lucide icons render on `/profile`, and Lucide is loaded only on `/profile`.
- [ ] Every class in `profile.html` and `profile.css` (other than the shared
      `btn-primary` / `btn-ghost`) starts with `pf-`.
- [ ] Layout is two columns above 900px, one column below; the table scrolls and hides
      Description under 768px; the tiles stack under 600px (checked manually).
- [ ] All existing tests in `tests/` still pass.

## Tests (`tests/test_profile.py`, pytest + pytest-flask)
- Fixtures/helpers: `conftest.py` gives a fresh empty DB per test (`temp_db`) and the
  `client`. Add `_insert_user(temp_db, name, email)` using `generate_password_hash`,
  `user` ("Asha Rao", `asha@example.com`) and `other_user` fixtures, an
  `add_expense(temp_db, user_id, amount, day, category="Food", description="")` helper,
  and `sign_in(client, user_id, name)` that sets `session["user_id"]` and
  `session["user_name"]` via `client.session_transaction()`.
- Route behaviour:
  - Signed out → 302, `Location` ends with `/login`.
  - Stale session (user id 999) → 302 to `/login` and an empty session.
  - Signed in → 200, contains `Profile · Spendly`, `css/profile.css`, `Asha Rao`,
    `asha@example.com`, `>AR<`, `Member since`, and `href="/logout"`.
- Totals: two expenses today (100, 250.5), one on `2020-01-15` (1000), and one for
  `other_user` (5000). Response contains `₹350.50`, `₹1,350.50` and `>3<`, and not
  `₹5,000.00`.
- Tile order: the index of "This month" in the response is before "Total spent", which
  is before "Expenses recorded".
- Recent list: seven expenses with descriptions `e1`…`e7` on consecutive past dates.
  Only the five newest appear, in newest-first order (compare `resp.data.index(...)`).
- Pill tones: one Food, one Bills, one Health and one Transport expense → the response
  contains `pf-pill--green`, `pf-pill--amber`, `pf-pill--red` and `pf-pill--neutral`.
- Lucide: `/profile` contains `lucide@1.81.0` and `createIcons`; `/` does not contain
  `lucide`.
- Empty description renders `—`.
- Escaping: a description of `<script>alert(1)</script>` appears as
  `&lt;script&gt;` and the raw tag does not.
- Empty state: `No expenses yet.`, `Add your first expense`, `href="/expenses/add"`,
  `₹0.00`, and no `<table`.
- Indian grouping on the page: one expense of 123456.5 → `₹1,23,456.50` appears.
- `format_inr` unit tests: `0 → ₹0.00`, `450 → ₹450.00`, `1899 → ₹1,899.00`,
  `123456.5 → ₹1,23,456.50`, `10000000 → ₹1,00,00,000.00`.
- `_initials` unit tests: `"Asha Rao" → "AR"`, `"madonna" → "M"`,
  `"Ana Maria Lopez" → "AM"`, `"" → "?"`.
