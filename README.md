# Coaching Saathi

A responsive Django web app for Indian coaching institutes: student records, batches, attendance, fee receipts, Razorpay online collection, staff roles, exams/results, and reporting.

## Stack
- Python 3.12 / Django 5.2
- PostgreSQL on Render; SQLite for local development
- WhiteNoise static files and Gunicorn
- Razorpay Checkout (requires your own API credentials)
- Responsive Bootstrap UI and PWA basics

## Local setup (Windows PowerShell)
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```
Open http://127.0.0.1:8000 and create your owner account using Sign up. To use Razorpay locally, put your **test** key ID and key secret in `.env`. Never commit secrets.

## Render deployment
1. Open https://dashboard.render.com/ and connect GitHub.
2. Create a Blueprint from this repository; review the service and PostgreSQL settings in `render.yaml`.
3. Render reads the build/start commands and applies migrations during startup.
4. In the Render service's Environment section, add `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` only if you want online payments. Begin with Razorpay test keys.
5. Deploy, create an institute owner account, then test the features using non-sensitive sample data.

## Features
- Owner signup/login and institute profile
- Students, batches, daily attendance and CSV export
- Offline fee ledger, unique receipt numbers and printable receipts
- Razorpay order creation, hosted checkout and server-side signature verification
- Staff accounts with Owner, Administrator, Teacher and Accountant access levels
- Exam creation, batch-scoped student lists, result entry, marks validation and percentage
- Date-range reports: fee collection, transaction counts, attendance totals, exam/result counts and average marks; fee CSV export
- PWA manifest/service worker basics, health endpoint, automated checks

## Razorpay setup and safety
Create an account at https://razorpay.com/, activate the relevant payment features, and use test keys first. In Render, set:
- `RAZORPAY_KEY_ID`: key ID
- `RAZORPAY_KEY_SECRET`: secret key (keep private)
- `RAZORPAY_WEBHOOK_SECRET`: a webhook secret you choose when creating the Razorpay webhook

In Razorpay Dashboard, configure a webhook endpoint at `https://YOUR-SERVICE.onrender.com/webhooks/razorpay/` with the same `RAZORPAY_WEBHOOK_SECRET`, and subscribe to `payment.captured`, `payment.failed` and `order.paid`. The application verifies the checkout signature and webhook HMAC on the server before creating a fee receipt. Test success, failure, cancelled checkout, duplicate callbacks and reconciliation before accepting real payments. Payment provider onboarding/approval and transaction fees are separate from this code. Never use live keys in a public repository.

## Role overview
- Owner: all features
- Administrator: staff, institute settings, students, fees, attendance, exams and reports
- Teacher: students, batches, attendance and exams/results
- Accountant: student list, fees/receipts and reports

## Checks
```powershell
python manage.py migrate
python manage.py test
python manage.py check
``

## Production notes
This is an extended MVP, not a fully audited commercial SaaS. Before real student/payment data, run a security review, verify role access with separate accounts, configure database backups and recovery, write privacy/retention policies, and test Razorpay webhooks/reconciliation. The current checkout flow verifies Razorpay's checkout signature; it is not a substitute for a production webhook, refund workflow, dispute handling or accounting reconciliation. Free hosting plans can sleep or change limits.

## Hindi deployment guide
See [docs/DEPLOY_RENDER_HI.md](docs/DEPLOY_RENDER_HI.md).
