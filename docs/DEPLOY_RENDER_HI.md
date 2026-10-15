# Coaching Saathi — Hindi Setup & Render Deployment Guide

यह guide Windows पर project चलाने और Render पर deploy करने के लिए है।

## 1. GitHub repository

Repository: https://github.com/pk8873/COACHING-SAATHI

## 2. अपने Windows PC पर चलाएँ

1. Python 3.12 install करें।
2. GitHub repository को डाउनलोड/clone करें और PowerShell में project folder खोलें।
3. नीचे दिए commands एक-एक करके चलाएँ:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```

Browser में `http://127.0.0.1:8000/` खोलें। नया institute बनाने के लिए **Sign up** करें।

यदि PowerShell virtual environment activate करने से रोके, उसी terminal में यह चलाएँ और फिर activate command दोहराएँ:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## 3. Render पर deploy करें

1. https://dashboard.render.com/ खोलें और GitHub account connect करें।
2. **New + → Blueprint** चुनें।
3. `pk8873/COACHING-SAATHI` repository select करें।
4. Render repository के `render.yaml` से web service और PostgreSQL database बनाने का प्रस्ताव दिखाएगा। प्रस्ताव में service/database settings जाँचें और apply करें।
5. Build पूरा होने तक Render के Events/Logs देखें।
6. Deploy सफल होने के बाद Render द्वारा दिए गए `https://....onrender.com` URL को खोलें।
7. पहले **Sign up** से institute owner account बनाएँ। Django admin की जरूरत हो तो Render Shell में `python manage.py createsuperuser` चलाएँ।

### Deployment check

- `https://YOUR-SERVICE.onrender.com/health/` खोलने पर `{"status": "ok"}` आना चाहिए।
- Sign up, login/logout, student create/edit, batch, attendance, fee receipt, CSV export और settings को जाँचें।
- Render logs में migration या static-file errors न हों।

## 4. App में अभी क्या है?

- Institute owner signup/login
- Dashboard और current-month fee collection summary
- Students: add, edit, search, archive, CSV export
- Batches create/list
- Daily attendance: present, absent, late, approved leave
- Fee payments, unique receipt number और printable receipt
- Institute profile/settings
- Responsive web layout और PWA manifest/service worker basics
- PostgreSQL deployment configuration, static files via WhiteNoise, health endpoint और automated Django tests

## 5. जरूरी सीमाएँ

यह अभी एक **MVP** है—पूरा commercial SaaS नहीं। इसमें payment gateway, WhatsApp automation, subscription billing, staff/teacher roles, exam/results module और advanced reports अभी शामिल नहीं हैं।

- Free hosting पर app sleep हो सकता है और free database की availability/retention की शर्तें बदल सकती हैं। Render dashboard में current limits और backup options देखें।
- असली विद्यार्थियों का data डालने से पहले backup/restore प्रक्रिया जाँचें।
- `SECRET_KEY` को secret रखें; उसे GitHub में commit न करें।
- Production launch से पहले privacy notice, access controls और security review करें।

## 6. Automated checks

GitHub Actions workflow `.github/workflows/django.yml` push पर migrations, tests और `manage.py check` चलाता है। किसी commit की स्थिति देखने के लिए repository के **Actions** tab में जाएँ.
