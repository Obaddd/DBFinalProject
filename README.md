# Restaurant Management Web App

This is a Flask + MySQL restaurant web application based on the project proposal.

## Features
- Customer CRUD
- Menu CRUD
- Table CRUD
- Reservation CRUD
- Order create, retrieve, status update, delete
- JOIN-based reports for reservations and customer spending

## Local Run
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
pip install -r requirements.txt
set DATABASE_URL=sqlite:///restaurant.db
flask --app app init-db
python app.py
```

## MySQL Run
1. Create a MySQL database called `restaurant_app`.
2. Set `DATABASE_URL`.
3. Run:
```bash
flask --app app init-db
python app.py
```

## AWS Deployment Notes
Use one EC2 instance for the Flask app and Amazon RDS MySQL for the database. Run with gunicorn:
```bash
gunicorn --bind 0.0.0.0:8000 app:app
```
Then reverse proxy it with Nginx.
