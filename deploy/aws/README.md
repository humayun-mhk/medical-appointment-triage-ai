# AWS Deployment Guide

Target architecture:

```text
React frontend       -> AWS Amplify Hosting
FastAPI backend      -> EC2 Ubuntu t3.small
PostgreSQL database  -> Neon PostgreSQL
Email service        -> Brevo API
```

For GitHub Actions deployment after the first EC2 setup, see `deploy/aws/GITHUB_ACTIONS.md`.

Use a domain/subdomain for the API, for example `api.yourdomain.com`. Amplify serves the frontend over HTTPS, so the browser should call an HTTPS API, not a plain EC2 HTTP URL.

## 1. Launch EC2

Recommended instance:

- AMI: Ubuntu Server LTS
- Instance type: `t3.small`
- Storage: 20 GB gp3
- Public IP: Elastic IP recommended
- Security group inbound:
  - SSH `22` from your IP only
  - HTTP `80` from anywhere
  - HTTPS `443` from anywhere
  - Do not expose backend port `8000`

Create/download a key pair. AWS requires the private key to connect by SSH.

## 2. Point DNS

Create an `A` record:

```text
api.yourdomain.com -> your EC2 Elastic IP
```

Wait for DNS propagation before running Certbot.

## 3. Connect to EC2

From your local terminal:

```bash
ssh -i path/to/key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

Install OS packages:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3-venv python3-pip nginx git certbot python3-certbot-nginx
```

## 4. Upload or Clone Project

Option A, clone from GitHub:

```bash
cd /home/ubuntu
git clone https://github.com/YOUR_USERNAME/healthcare-appointment-system.git
cd healthcare-appointment-system
```

Option B, upload from local machine:

```bash
scp -i path/to/key.pem -r healthcare-appointment-system ubuntu@YOUR_EC2_PUBLIC_IP:/home/ubuntu/
```

## 5. Configure Backend

```bash
cd /home/ubuntu/healthcare-appointment-system/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Create the backend `.env`:

```bash
cp ../deploy/aws/backend.env.production.example .env
nano .env
```

Required values:

```env
ENVIRONMENT=production
DATABASE_URL=your-neon-postgres-url-with-sslmode-require
JWT_SECRET_KEY=generate-a-strong-secret
CORS_ORIGINS=https://your-amplify-domain.amplifyapp.com,https://your-frontend-domain.com
FRONTEND_URL=https://your-amplify-domain.amplifyapp.com
EMAIL_PROVIDER=brevo
BREVO_API_KEY=your-brevo-api-key
SMTP_FROM_EMAIL=your-verified-brevo-sender@example.com
SMTP_FROM_NAME=Healthcare Appointments
```

Generate a JWT secret:

```bash
openssl rand -hex 32
```

Run migrations and seed data:

```bash
alembic upgrade head
python -m app.db.seed
```

Test locally on EC2:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another SSH tab:

```bash
curl http://127.0.0.1:8000/
```

Stop the test server with `Ctrl+C`.

## 6. Install Systemd Service

From project root:

```bash
cd /home/ubuntu/healthcare-appointment-system
sudo cp deploy/aws/healthcare-api.service.example /etc/systemd/system/healthcare-api.service
sudo systemctl daemon-reload
sudo systemctl enable --now healthcare-api
sudo systemctl status healthcare-api
```

Logs:

```bash
journalctl -u healthcare-api -f
```

## 7. Configure Nginx

```bash
sudo cp deploy/aws/nginx-healthcare-api.conf.example /etc/nginx/sites-available/healthcare-api
sudo nano /etc/nginx/sites-available/healthcare-api
```

Replace:

```text
api.yourdomain.com
```

with your real API domain.

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/healthcare-api /etc/nginx/sites-enabled/healthcare-api
sudo nginx -t
sudo systemctl reload nginx
```

Check HTTP:

```bash
curl http://api.yourdomain.com/
```

## 8. Enable HTTPS

```bash
sudo certbot --nginx -d api.yourdomain.com
```

Check HTTPS:

```bash
curl https://api.yourdomain.com/
```

## 9. Deploy Frontend on AWS Amplify

Push the project to GitHub.

In AWS Amplify:

1. Open Amplify Hosting.
2. Create a new app.
3. Connect your GitHub repository and branch.
4. Amplify will use `amplify.yml`.
5. Add environment variable:

```env
VITE_API_BASE_URL=https://api.yourdomain.com
```

Deploy the app.

After Amplify gives you a frontend URL, update EC2 backend `.env`:

```env
CORS_ORIGINS=https://your-amplify-domain.amplifyapp.com
FRONTEND_URL=https://your-amplify-domain.amplifyapp.com
```

Restart backend:

```bash
sudo systemctl restart healthcare-api
```

## 10. Production Checks

Backend:

```bash
curl https://api.yourdomain.com/
curl https://api.yourdomain.com/specialties
```

Frontend:

- Register a patient.
- Log in.
- Create profile.
- View doctors.
- Book appointment.
- Confirm Brevo transactional email log shows the email.

## Useful Commands

Restart API:

```bash
sudo systemctl restart healthcare-api
```

View API logs:

```bash
journalctl -u healthcare-api -f
```

Pull updates:

```bash
cd /home/ubuntu/healthcare-appointment-system
git pull
cd backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart healthcare-api
```

## Notes

- Keep `BREVO_API_KEY`, `DATABASE_URL`, `JWT_SECRET_KEY`, and `OPENAI_API_KEY` only on the backend server.
- Do not put backend secrets in Amplify frontend variables.
- If Neon connections ever show stale connection errors, set `DB_POOL_PRE_PING=true` and restart the backend.
- Keep SSH restricted to your own IP.
