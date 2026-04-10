# 🍽️ Restaurant Management Web App  
**Final Project – Database Systems (INFR2810U)**

This is a Flask + MySQL restaurant web application developed as the final project for our Database Systems course.

The application demonstrates a fully functional relational database system integrated with a web interface, supporting full CRUD operations and JOIN-based queries.

---

## 🚀 Features

- Customer CRUD (Create, Read, Update, Delete)
- Menu CRUD
- Table CRUD
- Reservation CRUD
- Order management:
  - Create orders
  - Retrieve orders
  - Update order status
  - Delete orders
- JOIN-based reports:
  - Reservations with customer and table details
  - Customer spending across orders

---

## ⚙️ How It Works

- Flask handles routing and backend logic  
- SQLAlchemy interacts with the MySQL database  
- Data is stored in relational tables  
- JOIN queries combine multiple tables for reporting  
- Bootstrap is used for frontend styling  

---

## 💻 Local Run (SQLite – Quick Test)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt

# Use SQLite (no setup required)
set DATABASE_URL=sqlite:///restaurant.db

flask --app app init-db
python -m flask --app app run
```

Open in browser:
http://127.0.0.1:5000

---

## 🗄️ Running with MySQL (Recommended)

### 1. Create Database
```sql
CREATE DATABASE restaurant_db;
```

### 2. Configure Environment Variable

Create a `.env` file in the project root:

```env
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost/restaurant_db
SECRET_KEY=your_secret_key
```

### 3. Initialize Database
```bash
flask --app app init-db
```

### 4. Run Application
```bash
python -m flask --app app run
```

---

## ☁️ AWS Deployment

- EC2 → Flask app  
- RDS (MySQL) → Database  

Steps:
1. Create MySQL database in RDS  
2. Launch EC2 (Ubuntu recommended)  
3. Clone repo on EC2  
4. Install dependencies  
5. Create `.env` with RDS credentials  
6. Initialize DB:
   flask --app app init-db  
7. Run:
   gunicorn --bind 0.0.0.0:8000 app:app  

---

## 👥 Team Members

- Rafay Khan  
- Sameer Khan  
- Ryan Sarwar  
- Suzanne Biju  
- Obad Al Jabberi  
 