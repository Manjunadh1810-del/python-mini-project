# Deployment Guide — SmartRecruit AI

This project is deployment-ready for any platform that runs a standard Django + Gunicorn app
with a Postgres database. Below are full steps for **Render** (free tier, recommended - easiest
for a student project) and brief notes for **Railway** and **PythonAnywhere** as alternatives.

## What's already set up for deployment

- `Procfile` — tells the host how to start the app (`gunicorn config.wsgi:application`)
- `whitenoise` — serves static files directly from Django, no separate static file host needed
- `dj-database-url` — reads a single `DATABASE_URL` env var (what every PaaS Postgres add-on provides) instead of separate host/port/user/password vars
- Production security settings (HTTPS redirect, secure cookies, HSTS) auto-enable when `DEBUG=False`
- `/healthz/` — a plain-text health check endpoint some platforms use to verify the app is alive
- `.env.example` — every environment variable the app reads, with comments

## Environment variables to set on your host

| Variable | Example | Notes |
|---|---|---|
| `DEBUG` | `False` | **Must** be `False` in production |
| `SECRET_KEY` | *(long random string)* | Generate one: `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `ALLOWED_HOSTS` | `smartrecruit-ai.onrender.com` | Comma-separated, no `https://` |
| `CSRF_TRUSTED_ORIGINS` | `https://smartrecruit-ai.onrender.com` | Comma-separated, **with** `https://` |
| `DATABASE_URL` | *(provided automatically by Render/Railway Postgres add-ons)* | Overrides all other DB_* vars |
| `GEMINI_API_KEY` | *(optional)* | Only needed if you wire in the Gemini API later |

## Deploying on Render (recommended)

1. Push this project to a GitHub repository.
2. On [render.com](https://render.com), click **New → PostgreSQL** — create a free Postgres database. Copy its **Internal Database URL**.
3. Click **New → Web Service**, connect your GitHub repo.
4. Settings:
   - **Build Command:** `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Start Command:** `gunicorn config.wsgi:application`
5. Add environment variables (from the table above) in the **Environment** tab, including `DATABASE_URL` from step 2.
6. Deploy. Once live, open the **Shell** tab (or use Render's one-off job feature) and run:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```
7. Visit your `.onrender.com` URL.

**Note on Render's free tier:** the free web service spins down after inactivity and the free Postgres database is deleted after 90 days unless upgraded — fine for a portfolio demo, just be aware before a live interview/viva.

## Deploying on Railway (alternative)

Railway auto-detects the `Procfile`. Steps are nearly identical to Render:
1. New Project → Deploy from GitHub repo.
2. Add a PostgreSQL plugin (Railway sets `DATABASE_URL` automatically).
3. Set the remaining environment variables in the service's **Variables** tab.
4. Railway runs the build automatically; use the **Deploy Logs** shell or a one-off command to run `python manage.py migrate` and `createsuperuser`.

## Deploying on PythonAnywhere (alternative, no Docker/Procfile)

PythonAnywhere's free tier uses WSGI configuration through its dashboard rather than a `Procfile`:
1. Upload your code (via git clone in a Bash console) into your PythonAnywhere account.
2. Create a virtualenv, `pip install -r requirements.txt`.
3. In the **Web** tab, point the WSGI file to `config.wsgi.application` and set the same environment variables via `os.environ` inside the generated `wsgi.py` wrapper, or a `.env` file loaded by `python-decouple` (already supported).
4. PythonAnywhere's free tier only supports SQLite or MySQL (not Postgres) — set `DATABASE_ENGINE=sqlite` (default) or configure MySQL manually; `DATABASE_URL` isn't needed here.
5. Static files: PythonAnywhere serves static files through its own dashboard mapping (`/static/` → `staticfiles/`) rather than WhiteNoise — run `collectstatic` and map the URL in the **Web** tab's "Static files" section.

## Known limitation: media file persistence

Render, Railway, and most PaaS free tiers use an **ephemeral filesystem** — uploaded resumes and profile pictures in `media/` will be lost on every redeploy or restart. For a portfolio/demo project this is an acceptable, documented limitation. If persistent uploads matter for your use case, the standard fix is swapping `MEDIA` storage to a cloud provider (e.g. `django-storages` + AWS S3, or Cloudinary) — noted here as a natural "Future Enhancement" for your README rather than implemented, to keep local development simple and dependency-light.

## Pre-deployment checklist

- [ ] `DEBUG=False` set in production environment
- [ ] Real, random `SECRET_KEY` generated (not the default dev one)
- [ ] `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` match your actual domain
- [ ] `python manage.py check --deploy` run locally with production-like env vars — should show no warnings besides ones you've deliberately accepted
- [ ] `python manage.py collectstatic --noinput` runs without errors
- [ ] `python manage.py test` — all tests pass before deploying
- [ ] Superuser created on the production database after first deploy
- [ ] `.env` is **not** committed to git (confirmed via `.gitignore`)
