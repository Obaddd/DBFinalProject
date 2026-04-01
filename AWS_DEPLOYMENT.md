# AWS Deployment Guide

## 1) Launch infrastructure
- Create an **Amazon RDS MySQL** database named `restaurant_app`.
- Create one **EC2 Ubuntu** instance for the Flask app.
- In the EC2 security group, allow:
  - SSH (22) from your IP
  - HTTP (80) from anywhere
  - HTTPS (443) from anywhere if you later add SSL
- In the RDS security group, allow MySQL (3306) **only from the EC2 security group**.

## 2) Connect to EC2
```bash
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

## 3) Install packages
```bash
sudo apt update
sudo apt install -y python3-pip python3-venv nginx git
```

## 4) Upload your project
Option A: clone from GitHub
```bash
git clone YOUR_GITHUB_REPO_URL restaurant_app
cd restaurant_app
```

Option B: upload the zip from your computer using SCP
```bash
scp -i your-key.pem restaurant_app.zip ubuntu@YOUR_EC2_PUBLIC_IP:/home/ubuntu/
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
unzip restaurant_app.zip -d restaurant_app
cd restaurant_app
```

## 5) Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 6) Set environment variables
```bash
nano .env
```
Paste:
```env
SECRET_KEY=replace-with-a-random-secret
DATABASE_URL=mysql+pymysql://admin:YOUR_DB_PASSWORD@YOUR_RDS_ENDPOINT:3306/restaurant_app
```

Load them:
```bash
export $(grep -v '^#' .env | xargs)
```

## 7) Initialize the database
```bash
source venv/bin/activate
export $(grep -v '^#' .env | xargs)
flask --app app init-db
```

## 8) Test the app
```bash
gunicorn --bind 0.0.0.0:8000 app:app
```
Open `http://YOUR_EC2_PUBLIC_IP:8000`

## 9) Create systemd service
```bash
sudo nano /etc/systemd/system/restaurant_app.service
```
Paste:
```ini
[Unit]
Description=Gunicorn for restaurant Flask app
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/restaurant_app
EnvironmentFile=/home/ubuntu/restaurant_app/.env
ExecStart=/home/ubuntu/restaurant_app/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 app:app

[Install]
WantedBy=multi-user.target
```

Then run:
```bash
sudo systemctl daemon-reload
sudo systemctl start restaurant_app
sudo systemctl enable restaurant_app
sudo systemctl status restaurant_app
```

## 10) Configure Nginx
```bash
sudo nano /etc/nginx/sites-available/restaurant_app
```
Paste:
```nginx
server {
    listen 80;
    server_name _;

    location /static {
        alias /home/ubuntu/restaurant_app/static;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable it:
```bash
sudo ln -s /etc/nginx/sites-available/restaurant_app /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

Now your site should work at:
```text
http://YOUR_EC2_PUBLIC_IP
```

## 11) What URL to submit
Submit the public EC2 URL or, even better, a domain name pointing to the EC2 instance.

## 12) Good demo flow for your report
1. Add a customer
2. Add a menu item
3. Add a table
4. Create a reservation
5. Create an order with multiple items
6. Update the order status
7. Open Reports to show the JOIN queries
