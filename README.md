# Coaching Saathi

A responsive, installable Django web app for small Indian coaching institutes. This repository starts with a deployable MVP: institute registration, dashboard, students, batches, attendance, fee ledger, CSV export, and PWA basics.

## Stack
- Python 3.12 / Django 5.2 LTS
- PostgreSQL in production; SQLite locally
- WhiteNoise static files
- Bootstrap 5, Bootstrap Icons, Chart.js (CDN)
- PWA manifest and service worker

## Run locally (Windows PowerShell)
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Open http://127.0.0.1:8000. Registration creates an institute and its owner account. Never use demo credentials in production.

## Render deployment
1. Push this repository to GitHub and choose **New Web Service** in Render.
2. Connect this repository. Render can use the included `render.yaml` Blueprint.
3. Create the PostgreSQL database and set `DATABASE_URL` from Render's internal database URL.
4. Set `SECRET_KEY` to a long random secret, `DEBUG=false`, and `ALLOWED_HOSTS` to your Render hostname (or use the provided settings defaults).
5. Deploy. The build command installs dependencies and runs collectstatic; the start command runs migrations and Gunicorn.
6. Create an admin account in the Render Shell with `python manage.py createsuperuser`.

## Important limitations
This is an MVP, not yet a full commercial SaaS. It has institute-level ownership isolation for the included records, but no integrated payment gateway, automated WhatsApp API, subscription billing, email delivery, or advanced staff-role management. Configure backups and privacy/legal policies before storing real student data. Review security and run tests before production launch.

## Tests
```powershell
python manage.py test
python manage.py check --deploy
```


## Hindi guide

Windows पर local setup और Render deployment के लिए [Hindi setup guide](docs/DEPLOY_RENDER_HI.md) देखें.
