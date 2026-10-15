# Coaching Saathi — Hindi Setup & Render Deployment Guide

## 1. GitHub repository
https://github.com/pk8873/COACHING-SAATHI

## 2. Windows पर local setup
Python 3.12 install करें, repository डाउनलोड/clone करें, project folder में PowerShell खोलें और चलाएँ:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```

Browser में http://127.0.0.1:8000 खोलें और Sign up से institute owner account बनाएँ। Razorpay test mode के लिए `.env` में अपनी test key ID और secret डालें। Secret को GitHub पर कभी push न करें।

## 3. Render पर deploy
1. https://dashboard.render.com/ खोलें और GitHub connect करें।
2. **New + → Blueprint** चुनें।
3. `pk8873/COACHING-SAATHI` चुनें और `render.yaml` की settings review करें।
4. Service environment में online payment चालू करना हो तो `RAZORPAY_KEY_ID` और `RAZORPAY_KEY_SECRET` जोड़ें। शुरुआत test keys से करें।
5. Deploy पूरा होने पर Render URL खोलें और owner signup करें।
6. `/health/` खोलकर health endpoint जाँचें। Render logs में migrations और startup errors देखें।

## 4. Features
- Student, batch, attendance और fee receipt management
- Razorpay Checkout online fee collection और server-side signature verification
- Staff login: Administrator, Teacher, Accountant; role-based access restrictions
- Exams बनाना, batch के students के marks दर्ज करना और percentage निकालना
- Date range के आधार पर collection, attendance और exam reports; fee CSV export
- Responsive layout, PWA basics, PostgreSQL, WhiteNoise और automated tests

## 5. Staff roles
- Owner: सभी features
- Administrator: staff/settings सहित institute management
- Teacher: students, batches, attendance, exams/results
- Accountant: student list, fees/receipts और reports

## 6. Razorpay configuration
Razorpay account बनाएँ और Dashboard से API test keys प्राप्त करें। Render → Service → Environment में:
- `RAZORPAY_KEY_ID`: public key ID
- `RAZORPAY_KEY_SECRET`: private secret

यह application receipt बनाने से पहले server-side payment signature verify करती है। पहले test mode में successful, failed, cancelled और duplicate callback scenarios जाँचें। Live payments के लिए Razorpay account approval, fees, refunds, webhooks, reconciliation और legal/accounting obligations अलग से configure/test करने होंगे।

## 7. Important
यह production-audited commercial SaaS नहीं है। असली student data या live payments से पहले role testing, security review, backup/restore, privacy policy, payment reconciliation और refund workflow लागू करें। Free hosting/database की availability और retention limits बदल सकती हैं।
