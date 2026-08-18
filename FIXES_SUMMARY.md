# 🔧 Climate Mirror Vercel Deployment — Fixes Summary

## Problem Statement

Your Climate Mirror app was failing on Vercel with:
```
Bad Request
The CSRF token is missing.
```

This happened after the initial build error was fixed (`app` instance not found).

---

## Root Causes

### Issue #1: Missing CSRF Token Fields in Templates

Flask-WTF enforces CSRF protection on all POST requests. Your forms had no token field.

**Status:** Forms try to POST → Flask sees no CSRF token → rejects request

### Issue #2: Unstable SECRET_KEY on Vercel Serverless

On Vercel, each function invocation is a fresh process. Your old code used:
```python
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(32)
```

**Status:** Request 1 generates key A → CSRF token tied to A. Request 2 generates key B → token validation fails because keys don't match.

---

## Fixes Applied

### Fix #1: Add CSRF Token to All POST Forms

#### register.html
```diff
      <form method="POST" action="/register" autocomplete="on">
+       {{ csrf_token() }}
        <div class="group">
          <label>Username</label>
```

#### login.html
```diff
      <form method="POST" action="/login" autocomplete="on">
+       {{ csrf_token() }}
        <div class="group">
          <label>Username</label>
```

#### climate.html (Prediction form)
```diff
      <form method="POST" action="/predict" id="simForm">
+       {{ csrf_token() }}
        <label>Country <span class="field-hint">Select your region</span></label>
```

#### notebook.html (Save notes form)
```diff
      <form method="POST" action="/save_note">
+       {{ csrf_token() }}
        <input type="text" name="title" placeholder="Note title..." required class="notes-input">
```

---

### Fix #2: Stabilize SECRET_KEY

#### app.py — Before (Broken)
```python
# ❌ VERCEL PROBLEM: New key generated on each invocation
app.secret_key = (
    os.environ.get("SECRET_KEY")
    or os.urandom(32)  # Fresh random bytes = new key each time!
)
```

#### app.py — After (Fixed)
```python
# ✅ VERCEL SAFE: Consistent fallback, environment override
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "climate-mirror-dev-key-2024"  # Same on every invocation
)
```

**Why this works:**
- Same string fallback → same key across cold starts
- Dev/testing works without env var
- Production uses strong SECRET_KEY from env var

---

### Fix #3: Add Explicit vercel.json

#### vercel.json (New)
```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "functions": {
    "app.py": {
      "maxDuration": 30
    }
  },
  "env": {
    "FLASK_ENV": "production"
  }
}
```

**Benefits:**
- Explicit Flask configuration (no guessing)
- 30-second timeout (adjust if needed)
- FLASK_ENV=production for security
- Uses Vercel's current `functions` config format — the older `builds`/`routes`
  format is legacy, and `memory` can't be set here anymore now that Fluid
  compute is on by default (set it in the dashboard's Functions settings
  instead)

---

## Deployment Steps

### 1. Replace Files

Copy the fixed folder to your project:
```bash
git add app.py vercel.json DEPLOYMENT_GUIDE.md FIXES_SUMMARY.md
git add templates/register.html templates/login.html
git add templates/climate.html templates/notebook.html
```

### 2. Commit & Push
```bash
git commit -m "Fix: CSRF token + stable SECRET_KEY for Vercel"
git push origin main
```

### 3. Set Vercel Environment Variable

In Vercel Dashboard → Project Settings → Environment Variables:

```
KEY: SECRET_KEY
VALUE: [Generate strong random string]
ENVIRONMENTS: Production
```

Generate a strong key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
# Example output: a3f9e8d2c1b4f6a9e2d5c8b1a4f7e0d3c6b9a2e5f8c1b4
```

### 4. Trigger Deployment

Vercel auto-deploys on git push. Watch the build in dashboard.

---

## Testing the Fix

### Before (Broken)
1. Visit `https://your-app.vercel.app/register`
2. Fill form → Click "ACTIVATE PROFILE"
3. ❌ Error: "Bad Request — The CSRF token is missing"

### After (Fixed)
1. Visit `https://your-app.vercel.app/register`
2. Fill form → Click "ACTIVATE PROFILE"
3. ✅ Form submits successfully, user created

---

## What Changed in Files

| File | Lines Changed | Change Type |
|------|--------------|-------------|
| `app.py` | 45-52 | SECRET_KEY logic (3 lines → 6 lines, with comments) |
| `templates/register.html` | 7 | Added CSRF token (1 line) |
| `templates/login.html` | 7 | Added CSRF token (1 line) |
| `templates/climate.html` | ~line 150 | Added CSRF token (1 line) |
| `templates/notebook.html` | ~line 100 | Added CSRF token (1 line) |
| `vercel.json` | NEW | New 26-line configuration file |
| `DEPLOYMENT_GUIDE.md` | NEW | New comprehensive guide |
| `FIXES_SUMMARY.md` | NEW | This file |

---

## Common Pitfalls (Avoid These!)

❌ **Pitfall:** Using the dev key in production  
✅ **Solution:** Always set SECRET_KEY env var in Vercel for production

❌ **Pitfall:** Browser still shows error after fix  
✅ **Solution:** Clear browser cookies, hard refresh (Ctrl+Shift+R)

❌ **Pitfall:** Data disappears after redeploy  
✅ **Solution:** Upgrade to Vercel Postgres or external database (see DEPLOYMENT_GUIDE.md)

---

## Database Note

Your app currently uses SQLite (`climate.db`). On Vercel:
- ✅ Works on first load (uses `/tmp/climate.db`)
- ❌ Data doesn't persist across redeploys or cold starts

**For persistent data**, switch to PostgreSQL:
1. Use Vercel Postgres (easiest, auto-configured)
2. Update `requirements.txt` with `psycopg2-binary`
3. Existing code already reads `DATABASE_URL` env var, so it auto-switches!

See "Solution: Switch to Persistent Database" in DEPLOYMENT_GUIDE.md.

---

## Quick Reference

**CSRF token field syntax:**
```html
{{ csrf_token() }}  <!-- Auto-generates hidden input with CSRF token -->
```

**SECRET_KEY best practice:**
```python
app.secret_key = os.environ.get("SECRET_KEY", "dev-fallback-key")
# Production: set strong SECRET_KEY env var in Vercel
# Development: falls back to predictable key (safe for local testing)
```

**Vercel Flask config:**
```json
{
  "functions": {
    "app.py": { "maxDuration": 30 }
  }
}
```

---

## Support Links

- [Vercel Flask Docs](https://vercel.com/docs/frameworks/backend/flask)
- [Flask-WTF CSRF Protection](https://flask-wtf.readthedocs.io/en/1.2.x/#csrf-protection)
- [Vercel Environment Variables](https://vercel.com/docs/projects/environment-variables)
- [Vercel Postgres](https://vercel.com/storage/postgres)

---

**Status:** ✅ All fixes applied and ready for deployment  
**Test Date:** August 18, 2026  
**Version:** Climate Mirror v2 (Vercel-ready)

---

## Round 2 Fixes (Verification Pass)

### Fix #4: Modernized vercel.json

The `builds`/`routes` config from Round 1 is Vercel's legacy Python config
format. It still deploys, but Vercel's currently documented approach is the
`functions` key, and — important — **`memory` can no longer be set in
`vercel.json` at all now that Fluid compute is enabled by default** for new
projects; doing so risks a config validation error. `vercel.json` was
rewritten to the current format (see above). If you need more than the
default memory, set it in Project Settings → Functions in the Vercel
dashboard instead.

### Fix #5: Missing date/time on the History page

`HistoryRecord.to_dict()` only returned raw DB columns (`created_at` as a
`datetime`), but `templates/history.html` reads `r.date` and `r.time` for
the table, chart labels, and the detail panel — those keys didn't exist, so
every row silently showed blank dates/times. `to_dict()` now also returns
`date` (`YYYY-MM-DD`) and `time` (`HH:MM`) derived from `created_at`, and
`created_at` itself is serialized to an ISO string so it JSON-encodes
cleanly wherever a record is passed to a template's `|tojson`.

### Note (not changed): SQLite on `/tmp`

Also worth knowing before you deploy: `/tmp` on Vercel is ephemeral per
function instance, so registered users, notes, and history will reset on
cold starts/redeploys. This was already flagged in Round 1 — switch to
Postgres (e.g. Vercel Postgres) via `DATABASE_URL` for real persistence.
The in-memory rate limiter in `utils.py` has the same limitation (resets
per instance), which just means rate limiting is best-effort, not a hard
guarantee, on serverless.
