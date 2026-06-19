# GitHub Actions Deployment Path

Recommended path for this project:

```text
Create EC2 once manually or with Terraform
Configure Nginx + SSL once
Deploy backend updates through GitHub Actions
Deploy frontend through Vercel
```

Creating the EC2 instance itself through GitHub Actions is possible, but it is not the easiest first step. It needs AWS IAM/OIDC, Terraform, and remote state. For a first production-style deployment, create EC2 once, then use GitHub Actions only for code deploys.

## What You Need

- AWS account
- EC2 Ubuntu `t3.small`
- EC2 key pair
- Elastic IP
- Security group:
  - `22` SSH from your IP
  - `80` HTTP from anywhere
  - `443` HTTPS from anywhere
- Domain DNS:
  - `api.n8nmhk.space -> EC2 Elastic IP`
- Neon PostgreSQL URL
- Brevo API key
- GitHub repository
- Vercel project for frontend

## Step 1. Create EC2

Use AWS Console first:

- AMI: Ubuntu Server LTS
- Type: `t3.small`
- Storage: 20 GB gp3
- Elastic IP: allocate and attach
- Security group: SSH, HTTP, HTTPS

Then connect:

```bash
ssh -i your-key.pem ubuntu@YOUR_EC2_ELASTIC_IP
```

Install packages:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3-venv python3-pip nginx git certbot python3-certbot-nginx rsync
```

## Step 2. First Backend Setup On EC2

Upload or clone the project:

```bash
cd /home/ubuntu
git clone YOUR_GITHUB_REPO_URL healthcare-appointment-system
cd healthcare-appointment-system/backend
```

Create environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp ../deploy/aws/backend.env.production.example .env
nano .env
```

Required production values:

```env
ENVIRONMENT=production
DATABASE_URL=your-neon-url-with-sslmode-require
JWT_SECRET_KEY=your-strong-secret
CORS_ORIGINS=https://n8nmhk.space,https://www.n8nmhk.space,https://YOUR_VERCEL_APP.vercel.app
FRONTEND_URL=https://n8nmhk.space
EMAIL_PROVIDER=brevo
BREVO_API_KEY=your-brevo-api-key
SMTP_FROM_EMAIL=your-verified-brevo-sender
SMTP_FROM_NAME=Healthcare Appointments
```

Run DB setup:

```bash
alembic upgrade head
python -m app.db.seed
```

Install systemd:

```bash
cd /home/ubuntu/healthcare-appointment-system
sudo cp deploy/aws/healthcare-api.service.example /etc/systemd/system/healthcare-api.service
sudo systemctl daemon-reload
sudo systemctl enable --now healthcare-api
sudo systemctl status healthcare-api
```

## Step 3. Nginx And SSL

```bash
sudo cp deploy/aws/nginx-healthcare-api.conf.example /etc/nginx/sites-available/healthcare-api
sudo nano /etc/nginx/sites-available/healthcare-api
```

Change:

```text
api.yourdomain.com
```

to:

```text
api.n8nmhk.space
```

Enable Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/healthcare-api /etc/nginx/sites-enabled/healthcare-api
sudo nginx -t
sudo systemctl reload nginx
```

Add SSL:

```bash
sudo certbot --nginx -d api.n8nmhk.space
```

Test:

```bash
curl https://api.n8nmhk.space/
```

## Step 4. Add GitHub Secrets

In GitHub:

```text
Repo -> Settings -> Secrets and variables -> Actions -> New repository secret
```

Add:

```text
EC2_HOST=YOUR_EC2_ELASTIC_IP_OR_api.n8nmhk.space
EC2_USER=ubuntu
EC2_SSH_KEY=contents of your private .pem key
```

`EC2_SSH_KEY` must include the full private key text, including:

```text
-----BEGIN ... PRIVATE KEY-----
...
-----END ... PRIVATE KEY-----
```

## Step 5. Deploy Backend Through GitHub Actions

Workflow file:

```text
.github/workflows/backend-deploy.yml
```

It runs when you push backend/deploy changes to `main`, or manually from:

```text
GitHub -> Actions -> Deploy Backend to EC2 -> Run workflow
```

The workflow:

- Syncs the repo to EC2 with `rsync`
- Keeps `backend/.env` safe on the server
- Installs Python dependencies
- Runs Alembic migrations
- Restarts `healthcare-api`

## Step 6. Deploy Frontend On Vercel

In Vercel:

```text
Root Directory: frontend
Build Command: npm run build
Output Directory: dist
```

Environment:

```env
VITE_API_BASE_URL=https://api.n8nmhk.space
```

After Vercel gives you a temporary URL, add it to backend CORS while DNS is settling:

```env
CORS_ORIGINS=https://n8nmhk.space,https://www.n8nmhk.space,https://YOUR_VERCEL_APP.vercel.app
```

Then restart EC2 backend:

```bash
sudo systemctl restart healthcare-api
```

## Optional: Create EC2 Through GitHub Actions

This is possible but harder.

Use this only after the manual deployment works:

```text
GitHub Actions
  -> AWS OIDC role
  -> Terraform
  -> S3 backend for Terraform state
  -> EC2 / Security Group / Elastic IP
```

Why it is harder:

- You need an AWS IAM role that trusts GitHub OIDC.
- You need to restrict that role to your repository/branch.
- You need remote Terraform state, usually S3.
- A bad workflow can create duplicate resources or destroy the wrong thing.

For this project, the clean beginner-friendly path is:

```text
Create EC2 once manually
Use GitHub Actions for repeat backend deployments
Use Vercel for frontend deployments
```

