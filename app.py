import os
from datetime import datetime
from decimal import Decimal

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///restaurant.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Customer(db.Model):
    __tablename__ = 'customers'
    customer_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(30), nullable=False)

    reservations = db.relationship('Reservation', backref='customer', cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='customer', cascade='all, delete-orphan')


class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    food_name = db.Column(db.String(120), primary_key=True)
    category = db.Column(db.String(60), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    is_available = db.Column(db.Boolean, default=True, nullable=False)

    order_items = db.relationship('OrderItem', backref='menu_item', cascade='all, delete-orphan')


class RestaurantTable(db.Model):
    __tablename__ = 'restaurant_tables'
    table_id = db.Column(db.Integer, primary_key=True)
    capacity = db.Column(db.Integer, nullable=False)
    table_type = db.Column(db.String(50), nullable=False)

    reservations = db.relationship('Reservation', backref='table', cascade='all, delete-orphan')


class Reservation(db.Model):
    __tablename__ = 'reservations'
    reservation_id = db.Column(db.Integer, primary_key=True)
    reservation_time = db.Column(db.DateTime, nullable=False)
    party_size = db.Column(db.Integer, nullable=False)
    table_id = db.Column(db.Integer, db.ForeignKey('restaurant_tables.table_id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.customer_id'), nullable=False)
    status = db.Column(db.String(30), default='Booked', nullable=False)


class Order(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.Integer, primary_key=True)
    cost = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    order_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.customer_id'), nullable=False)
    order_type = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(30), default='Placed', nullable=False)

    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan')


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    order_item_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    food_name = db.Column(db.String(120), db.ForeignKey('menu_items.food_name'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)


def seed_data():
    if Customer.query.first():
        return

    customers = [
        Customer(name='Obad Al Jabberi', email='obad@example.com', phone='555-0101'),
        Customer(name='Rafay Khan', email='rafay@example.com', phone='555-0102'),
    ]
    menu_items = [
        MenuItem(food_name='Margherita Pizza', category='Main', price=Decimal('14.99')),
        MenuItem(food_name='Chicken Burger', category='Main', price=Decimal('12.49')),
        MenuItem(food_name='Caesar Salad', category='Starter', price=Decimal('9.99')),
        MenuItem(food_name='Tiramisu', category='Dessert', price=Decimal('6.50')),
    ]
    tables = [
        RestaurantTable(capacity=2, table_type='Indoor'),
        RestaurantTable(capacity=4, table_type='Indoor'),
        RestaurantTable(capacity=6, table_type='Patio'),
    ]

    db.session.add_all(customers + menu_items + tables)
    db.session.commit()

    reservation = Reservation(
        reservation_time=datetime(2026, 4, 10, 19, 0),
        party_size=4,
        table_id=2,
        customer_id=1,
        status='Booked',
    )
    order = Order(
        customer_id=1,
        order_type='Pickup',
        status='Preparing',
        order_time=datetime(2026, 4, 1, 18, 30),
        cost=Decimal('24.98'),
    )
    db.session.add_all([reservation, order])
    db.session.commit()

    items = [
        OrderItem(order_id=order.order_id, food_name='Margherita Pizza', quantity=1, price=Decimal('14.99')),
        OrderItem(order_id=order.order_id, food_name='Tiramisu', quantity=1, price=Decimal('9.99')),
    ]
    db.session.add_all(items)
    db.session.commit()


@app.template_filter('currency')
def currency(value):
    return f"${float(value):,.2f}"


@app.route('/')
def home():
    stats = {
        'customers': Customer.query.count(),
        'menu_items': MenuItem.query.count(),
        'reservations': Reservation.query.count(),
        'orders': Order.query.count(),
    }
    recent_orders = (
        db.session.query(Order, Customer.name)
        .join(Customer, Order.customer_id == Customer.customer_id)
        .order_by(Order.order_time.desc())
        .limit(5)
        .all()
    )
    return render_template('home.html', stats=stats, recent_orders=recent_orders)


@app.route('/customers')
def customers():
    customer_list = Customer.query.order_by(Customer.customer_id.desc()).all()
    return render_template('customers.html', customers=customer_list)


@app.route('/customers/add', methods=['POST'])
def add_customer():
    customer = Customer(
        name=request.form['name'],
        email=request.form['email'],
        phone=request.form['phone'],
    )
    db.session.add(customer)
    db.session.commit()
    flash('Customer added successfully.')
    return redirect(url_for('customers'))


@app.route('/customers/<int:customer_id>/edit', methods=['POST'])
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    customer.name = request.form['name']
    customer.email = request.form['email']
    customer.phone = request.form['phone']
    db.session.commit()
    flash('Customer updated successfully.')
    return redirect(url_for('customers'))


@app.route('/customers/<int:customer_id>/delete', methods=['POST'])
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    flash('Customer deleted successfully.')
    return redirect(url_for('customers'))


@app.route('/menu')
def menu():
    items = MenuItem.query.order_by(MenuItem.category, MenuItem.food_name).all()
    return render_template('menu.html', items=items)


@app.route('/menu/add', methods=['POST'])
def add_menu_item():
    item = MenuItem(
        food_name=request.form['food_name'],
        category=request.form['category'],
        price=Decimal(request.form['price']),
        is_available='is_available' in request.form,
    )
    db.session.add(item)
    db.session.commit()
    flash('Menu item added successfully.')
    return redirect(url_for('menu'))


@app.route('/menu/<string:food_name>/edit', methods=['POST'])
def edit_menu_item(food_name):
    item = MenuItem.query.get_or_404(food_name)
    item.category = request.form['category']
    item.price = Decimal(request.form['price'])
    item.is_available = 'is_available' in request.form
    db.session.commit()
    flash('Menu item updated successfully.')
    return redirect(url_for('menu'))


@app.route('/menu/<string:food_name>/delete', methods=['POST'])
def delete_menu_item(food_name):
    item = MenuItem.query.get_or_404(food_name)
    db.session.delete(item)
    db.session.commit()
    flash('Menu item deleted successfully.')
    return redirect(url_for('menu'))


@app.route('/tables')
def tables():
    all_tables = RestaurantTable.query.order_by(RestaurantTable.table_id).all()
    return render_template('tables.html', tables=all_tables)


@app.route('/tables/add', methods=['POST'])
def add_table():
    table = RestaurantTable(
        capacity=int(request.form['capacity']),
        table_type=request.form['table_type'],
    )
    db.session.add(table)
    db.session.commit()
    flash('Table added successfully.')
    return redirect(url_for('tables'))


@app.route('/tables/<int:table_id>/edit', methods=['POST'])
def edit_table(table_id):
    table = RestaurantTable.query.get_or_404(table_id)
    table.capacity = int(request.form['capacity'])
    table.table_type = request.form['table_type']
    db.session.commit()
    flash('Table updated successfully.')
    return redirect(url_for('tables'))


@app.route('/tables/<int:table_id>/delete', methods=['POST'])
def delete_table(table_id):
    table = RestaurantTable.query.get_or_404(table_id)
    db.session.delete(table)
    db.session.commit()
    flash('Table deleted successfully.')
    return redirect(url_for('tables'))


@app.route('/reservations')
def reservations():
    reservation_rows = (
        db.session.query(Reservation, Customer.name, RestaurantTable.table_type, RestaurantTable.capacity)
        .join(Customer, Reservation.customer_id == Customer.customer_id)
        .join(RestaurantTable, Reservation.table_id == RestaurantTable.table_id)
        .order_by(Reservation.reservation_time.asc())
        .all()
    )
    customers = Customer.query.order_by(Customer.name).all()
    tables = RestaurantTable.query.order_by(RestaurantTable.table_id).all()
    return render_template('reservations.html', reservation_rows=reservation_rows, customers=customers, tables=tables)


@app.route('/reservations/add', methods=['POST'])
def add_reservation():
    reservation = Reservation(
        customer_id=int(request.form['customer_id']),
        table_id=int(request.form['table_id']),
        reservation_time=datetime.strptime(request.form['reservation_time'], '%Y-%m-%dT%H:%M'),
        party_size=int(request.form['party_size']),
        status=request.form['status'],
    )
    db.session.add(reservation)
    db.session.commit()
    flash('Reservation added successfully.')
    return redirect(url_for('reservations'))


@app.route('/reservations/<int:reservation_id>/edit', methods=['POST'])
def edit_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    reservation.customer_id = int(request.form['customer_id'])
    reservation.table_id = int(request.form['table_id'])
    reservation.reservation_time = datetime.strptime(request.form['reservation_time'], '%Y-%m-%dT%H:%M')
    reservation.party_size = int(request.form['party_size'])
    reservation.status = request.form['status']
    db.session.commit()
    flash('Reservation updated successfully.')
    return redirect(url_for('reservations'))


@app.route('/reservations/<int:reservation_id>/delete', methods=['POST'])
def delete_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    db.session.delete(reservation)
    db.session.commit()
    flash('Reservation deleted successfully.')
    return redirect(url_for('reservations'))


@app.route('/orders')
def orders():
    order_rows = (
        db.session.query(Order, Customer.name, func.count(OrderItem.order_item_id).label('item_count'))
        .join(Customer, Order.customer_id == Customer.customer_id)
        .outerjoin(OrderItem, Order.order_id == OrderItem.order_id)
        .group_by(Order.order_id, Customer.name)
        .order_by(Order.order_time.desc())
        .all()
    )
    customers = Customer.query.order_by(Customer.name).all()
    menu_items = MenuItem.query.filter_by(is_available=True).order_by(MenuItem.food_name).all()
    return render_template('orders.html', order_rows=order_rows, customers=customers, menu_items=menu_items)


@app.route('/orders/add', methods=['POST'])
def add_order():
    customer_id = int(request.form['customer_id'])
    order_type = request.form['order_type']
    status = request.form['status']
    food_names = request.form.getlist('food_name')
    quantities = request.form.getlist('quantity')

    order = Order(customer_id=customer_id, order_type=order_type, status=status, order_time=datetime.utcnow(), cost=0)
    db.session.add(order)
    db.session.flush()

    total = Decimal('0.00')
    for food_name, quantity_str in zip(food_names, quantities):
        if not food_name or not quantity_str:
            continue
        quantity = int(quantity_str)
        if quantity <= 0:
            continue
        item = MenuItem.query.get(food_name)
        line_price = Decimal(item.price) * quantity
        total += line_price
        db.session.add(OrderItem(order_id=order.order_id, food_name=food_name, quantity=quantity, price=Decimal(item.price)))

    order.cost = total
    db.session.commit()
    flash('Order created successfully.')
    return redirect(url_for('orders'))


@app.route('/orders/<int:order_id>/status', methods=['POST'])
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    order.status = request.form['status']
    db.session.commit()
    flash('Order status updated successfully.')
    return redirect(url_for('orders'))


@app.route('/orders/<int:order_id>/delete', methods=['POST'])
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    flash('Order deleted successfully.')
    return redirect(url_for('orders'))


@app.route('/orders/<int:order_id>')
def order_details(order_id):
    order = Order.query.get_or_404(order_id)
    details = (
        db.session.query(OrderItem, MenuItem.category)
        .join(MenuItem, OrderItem.food_name == MenuItem.food_name)
        .filter(OrderItem.order_id == order_id)
        .all()
    )
    return render_template('order_details.html', order=order, details=details)


@app.route('/reports')
def reports():
    reservation_report = (
        db.session.query(Reservation, Customer.name, RestaurantTable.table_id)
        .join(Customer, Reservation.customer_id == Customer.customer_id)
        .join(RestaurantTable, Reservation.table_id == RestaurantTable.table_id)
        .order_by(Reservation.reservation_time.asc())
        .all()
    )
    spending_report = (
        db.session.query(Customer.name, func.coalesce(func.sum(Order.cost), 0).label('total_spent'))
        .outerjoin(Order, Customer.customer_id == Order.customer_id)
        .group_by(Customer.name)
        .order_by(func.coalesce(func.sum(Order.cost), 0).desc())
        .all()
    )
    return render_template('reports.html', reservation_report=reservation_report, spending_report=spending_report)


@app.cli.command('init-db')
def init_db_command():
    db.drop_all()
    db.create_all()
    seed_data()
    print('Database initialized with seed data.')


with app.app_context():
    db.create_all()
    seed_data()


if __name__ == '__main__':
    app.run(debug=True)
