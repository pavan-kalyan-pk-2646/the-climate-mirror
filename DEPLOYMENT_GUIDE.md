# 🚀 Climate Mirror — Vercel Deployment Guide

## Issue: CSRF Token Missing Error

**Root cause:** Your Flask app was deployed, but two things broke CSRF protection:

1. **Missing CSRF token fields in HTML forms** — Flask-WTF requires a token in all POST requests
2. **SECRET_KEY regenerated on each Vercel invocation** — CSRF tokens are tied to the key; a new key on each cold start invalidates old tokens

---

## ✅ Fixes Applied

### 1. **Added CSRF token fields to all POST forms**

Fixed templates:
- `register.html` ✓
- `login.html` ✓
- `climate.html` ✓ (prediction form)
- `notebook.html` ✓ (save notes form)

Each form now includes:
```html
<form method="POST" action="/endpoint">
  {{ csrf_token() }}
  <!-- form fields -->
</form>
```

### 2. **Stabilized SECRET_KEY in app.py**

**Before (broken on Vercel):**
```python
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(32)
# ❌ Each invocation regenerates the key!
```

**After (stable across invocations):**
```python
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "climate-mirror-dev-key-2024"  # Consistent fallback
)
```

### 3. **Added vercel.json**

Explicit Flask configuration for Vercel's Python runtime, using the current
`functions` format (the legacy `builds`/`routes` format is deprecated, and
`memory` can no longer be set from `vercel.json` now that Fluid compute is
on by default — set memory in the dashboard's Functions settings instead):
- 30-second timeout for requests
- FLASK_ENV=production

---

## 📋 Deployment Checklist

### Step 1: Commit & Push All Fixes

```bash
cd your-project-folder
git add .
git commit -m "Fix: CSRF token fields + stable SECRET_KEY for Vercel"
git push origin main
```

### Step 2: Set Production SECRET_KEY (Critical!)

**Do NOT use the default dev key in production.** Set a strong SECRET_KEY env var in Vercel:

1. Go to Vercel dashboard → Project Settings
2. Find **Environment Variables** section
3. Add:
   - **Key:** `SECRET_KEY`
   - **Value:** (generate a strong random string, e.g. 32+ characters)
   - **Environments:** Check "Production"

Example (generate a new one):
```bash
# On your machine
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Step 3: Trigger Deploy

The build should now succeed. Vercel will auto-redeploy on git push.

### Step 4: Test the App

1. Visit your Vercel URL (e.g., `https://the-climate-mirror-aj3u.vercel.app`)
2. Go to `/register` or `/login`
3. Fill out the form and submit
4. ✅ Should work without "CSRF token is missing" error

---

## 🗄️ Database Persistence Issue

**⚠️ Important limitation:** Your app uses SQLite (`climate.db`). On Vercel:
- Filesystem is **read-only** (except `/tmp`)
- `/tmp` **doesn't persist** between function invocations
- User registrations/data **will not survive** restarts or redeploys

### Solution: Switch to Persistent Database

#### Option A: Vercel Postgres (Recommended for simplicity)

1. In Vercel dashboard, click **Storage** → **Create Database** → **Postgres**
2. Vercel auto-injects `DATABASE_URL` env var
3. Update `requirements.txt`:
   ```
   flask>=3.0.0
   werkzeug>=3.0.0
   flask-sqlalchemy>=3.1.0
   flask-wtf>=1.2.0
   fpdf2>=2.7.0
   psycopg2-binary>=2.9.0
   ```
4. Your app already reads `DATABASE_URL` from env, so it will automatically use Postgres!

#### Option B: External Database (Neon, Supabase, PlanetScale)

1. Create a database account (e.g., Neon for PostgreSQL)
2. Get connection string: `postgresql://user:pass@host/dbname`
3. Add to Vercel env var:
   ```
   DATABASE_URL=postgresql://...
   ```

#### Option C: Keep SQLite (Data resets on each deploy)

- No setup needed, but user data is ephemeral
- Good for demo/testing only

---

## 🔧 Environment Variables (Vercel Dashboard)

Set these in **Settings** → **Environment Variables**:

```
SECRET_KEY=your-secure-random-32-char-string
FLASK_ENV=production
DATABASE_URL=postgresql://... (if using external DB)
```

---

## ✨ Quick Verification

After deployment, the **error page should change from:**
```
Bad Request
The CSRF token is missing.
```

**To:**
```
CREATE ACCOUNT
[Registration form loads normally]
```

---

## 🐛 Still Seeing Errors?

### "Bad Request — CSRF token is missing"
- ✅ Confirm all 4 template files have `{{ csrf_token() }}`
- ✅ Confirm `SECRET_KEY` env var is set in Vercel
- ✅ Clear browser cookies and try again (old sessions may have stale tokens)

### "Timeout" or "Function exceeded timeout"
- Increase `maxDuration` in `vercel.json` (up to 60 for Pro)
- Check `routes.py` for slow operations (DB queries, API calls)

### Database errors on Vercel
- Use `/tmp/climate.db` (built-in via app.py logic) for ephemeral SQLite
- OR switch to Vercel Postgres / external database

---

## 📚 Files Modified

| File | Change |
|------|--------|
| `app.py` | Stable SECRET_KEY, better logging |
| `vercel.json` | New Flask runtime config |
| `templates/register.html` | Added CSRF token field |
| `templates/login.html` | Added CSRF token field |
| `templates/climate.html` | Added CSRF token field |
| `templates/notebook.html` | Added CSRF token field |

---

## 🎯 Next Steps

1. **Deploy now:** Push fixes, watch Vercel build in dashboard
2. **Set SECRET_KEY:** Add strong key to Vercel env vars
3. **Test forms:** Register, login, save notes
4. **Plan database:** Decide on SQLite (ephemeral) vs Postgres (persistent)

---

**Last updated:** August 18, 2026  
**Maintainer:** PK (Burra Venkata Pavan Kalyan)