import os
from datetime import datetime
from decimal import Decimal, InvalidOperation

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///restaurant.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

VALID_RESERVATION_STATUSES = {'Booked', 'Completed', 'Cancelled'}
VALID_ORDER_TYPES = {'Dine-In', 'Takeout', 'Pickup', 'Delivery'}
VALID_ORDER_STATUSES = {'Placed', 'Preparing', 'Ready', 'Completed', 'Cancelled'}


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


def flash_error(message):
    flash(message, 'danger')


def flash_success(message):
    flash(message, 'success')


def normalize_text(value):
    return value.strip() if value else ''


def parse_int(value, field_name, min_value=None):
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError(f'{field_name} must be a valid whole number.')
    if min_value is not None and parsed < min_value:
        raise ValueError(f'{field_name} must be at least {min_value}.')
    return parsed


def parse_price(value, field_name='Price'):
    try:
        amount = Decimal(str(value).strip())
    except (InvalidOperation, AttributeError):
        raise ValueError(f'{field_name} must be a valid number.')
    if amount <= 0:
        raise ValueError(f'{field_name} must be greater than 0.')
    return amount.quantize(Decimal('0.01'))


def parse_datetime_local(value, field_name='Date and time'):
    try:
        return datetime.strptime(str(value).strip(), '%Y-%m-%dT%H:%M')
    except (TypeError, ValueError):
        raise ValueError(f'{field_name} is invalid. Please use a valid date and time.')


def validate_customer_fields(name, email, phone, existing_customer=None):
    name = normalize_text(name)
    email = normalize_text(email).lower()
    phone = normalize_text(phone)

    if not name:
        raise ValueError('Customer name is required.')
    if len(name) > 120:
        raise ValueError('Customer name must be 120 characters or less.')
    if not email or '@' not in email or '.' not in email.split('@')[-1]:
        raise ValueError('Please enter a valid email address.')
    if len(email) > 120:
        raise ValueError('Email must be 120 characters or less.')
    if not phone:
        raise ValueError('Phone number is required.')
    if len(phone) > 30:
        raise ValueError('Phone number must be 30 characters or less.')

    existing_email = Customer.query.filter(func.lower(Customer.email) == email)
    if existing_customer:
        existing_email = existing_email.filter(Customer.customer_id != existing_customer.customer_id)
    if existing_email.first():
        raise ValueError('That email address is already being used by another customer.')

    return name, email, phone


def validate_menu_fields(food_name, category, price, is_edit=False):
    food_name = normalize_text(food_name)
    category = normalize_text(category)
    price = parse_price(price)

    if not is_edit:
        if not food_name:
            raise ValueError('Food name is required.')
        if len(food_name) > 120:
            raise ValueError('Food name must be 120 characters or less.')
        if MenuItem.query.get(food_name):
            raise ValueError('A menu item with that name already exists.')

    if not category:
        raise ValueError('Category is required.')
    if len(category) > 60:
        raise ValueError('Category must be 60 characters or less.')

    return food_name, category, price


def validate_table_fields(capacity, table_type):
    capacity = parse_int(capacity, 'Capacity', min_value=1)
    table_type = normalize_text(table_type)
    if not table_type:
        raise ValueError('Table type is required.')
    if len(table_type) > 50:
        raise ValueError('Table type must be 50 characters or less.')
    return capacity, table_type


def validate_reservation_fields(customer_id, table_id, reservation_time, party_size, status):
    customer_id = parse_int(customer_id, 'Customer', min_value=1)
    table_id = parse_int(table_id, 'Table', min_value=1)
    reservation_time = parse_datetime_local(reservation_time, 'Reservation time')
    party_size = parse_int(party_size, 'Party size', min_value=1)
    status = normalize_text(status)

    customer = Customer.query.get(customer_id)
    if not customer:
        raise ValueError('Selected customer does not exist.')

    table = RestaurantTable.query.get(table_id)
    if not table:
        raise ValueError('Selected table does not exist.')

    if party_size > table.capacity:
        raise ValueError(f'Party size cannot exceed the selected table capacity of {table.capacity}.')
    if status not in VALID_RESERVATION_STATUSES:
        raise ValueError('Please choose a valid reservation status.')

    return customer_id, table_id, reservation_time, party_size, status


def validate_order_fields(customer_id, order_type, status, food_names, quantities):
    customer_id = parse_int(customer_id, 'Customer', min_value=1)
    if not Customer.query.get(customer_id):
        raise ValueError('Selected customer does not exist.')

    order_type = normalize_text(order_type)
    status = normalize_text(status)
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError('Please choose a valid order type.')
    if status not in VALID_ORDER_STATUSES:
        raise ValueError('Please choose a valid order status.')

    cleaned_items = []
    for food_name, quantity_str in zip(food_names, quantities):
        food_name = normalize_text(food_name)
        quantity_str = normalize_text(quantity_str)
        if not food_name and not quantity_str:
            continue
        if not food_name:
            raise ValueError('Each order row must include a menu item.')
        quantity = parse_int(quantity_str, 'Quantity', min_value=1)

        item = MenuItem.query.get(food_name)
        if not item:
            raise ValueError(f'Menu item "{food_name}" was not found.')
        if not item.is_available:
            raise ValueError(f'Menu item "{food_name}" is currently unavailable.')

        cleaned_items.append((item, quantity))

    if not cleaned_items:
        raise ValueError('Please add at least one valid order item.')

    return customer_id, order_type, status, cleaned_items


def commit_or_rollback(success_message, redirect_endpoint):
    try:
        db.session.commit()
        flash_success(success_message)
    except IntegrityError:
        db.session.rollback()
        flash_error('That action could not be completed because it would create duplicate or invalid data.')
    except SQLAlchemyError:
        db.session.rollback()
        flash_error('A database error occurred. Please try again.')
    return redirect(url_for(redirect_endpoint))


@app.errorhandler(404)
def not_found(_error):
    flash_error('The page you requested could not be found.')
    return redirect(url_for('home'))


@app.errorhandler(500)
def internal_error(_error):
    db.session.rollback()
    flash_error('Something went wrong on the server. Please try again.')
    return redirect(url_for('home'))


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
    try:
        name, email, phone = validate_customer_fields(
            request.form.get('name'),
            request.form.get('email'),
            request.form.get('phone'),
        )
        db.session.add(Customer(name=name, email=email, phone=phone))
        return commit_or_rollback('Customer added successfully.', 'customers')
    except ValueError as error:
        flash_error(str(error))
        return redirect(url_for('customers'))


@app.route('/customers/<int:customer_id>/edit', methods=['POST'])
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    try:
        customer.name, customer.email, customer.phone = validate_customer_fields(
            request.form.get('name'),
            request.form.get('email'),
            request.form.get('phone'),
            existing_customer=customer,
        )
        return commit_or_rollback('Customer updated successfully.', 'customers')
    except ValueError as error:
        flash_error(str(error))
        return redirect(url_for('customers'))


@app.route('/customers/<int:customer_id>/delete', methods=['POST'])
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    return commit_or_rollback('Customer deleted successfully.', 'customers')


@app.route('/menu')
def menu():
    items = MenuItem.query.order_by(MenuItem.category, MenuItem.food_name).all()
    return render_template('menu.html', items=items)


@app.route('/menu/add', methods=['POST'])
def add_menu_item():
    try:
        food_name, category, price = validate_menu_fields(
            request.form.get('food_name'),
            request.form.get('category'),
            request.form.get('price'),
        )
        item = MenuItem(
            food_name=food_name,
            category=category,
            price=price,
            is_available='is_available' in request.form,
        )
        db.session.add(item)
        return commit_or_rollback('Menu item added successfully.', 'menu')
    except ValueError as error:
        flash_error(str(error))
        return redirect(url_for('menu'))


@app.route('/menu/<string:food_name>/edit', methods=['POST'])
def edit_menu_item(food_name):
    item = MenuItem.query.get_or_404(food_name)
    try:
        _, item.category, item.price = validate_menu_fields(
            item.food_name,
            request.form.get('category'),
            request.form.get('price'),
            is_edit=True,
        )
        item.is_available = 'is_available' in request.form
        return commit_or_rollback('Menu item updated successfully.', 'menu')
    except ValueError as error:
        flash_error(str(error))
        return redirect(url_for('menu'))


@app.route('/menu/<string:food_name>/delete', methods=['POST'])
def delete_menu_item(food_name):
    item = MenuItem.query.get_or_404(food_name)
    db.session.delete(item)
    return commit_or_rollback('Menu item deleted successfully.', 'menu')


@app.route('/tables')
def tables():
    all_tables = RestaurantTable.query.order_by(RestaurantTable.table_id).all()
    return render_template('tables.html', tables=all_tables)


@app.route('/tables/add', methods=['POST'])
def add_table():
    try:
        capacity, table_type = validate_table_fields(
            request.form.get('capacity'),
            request.form.get('table_type'),
        )
        db.session.add(RestaurantTable(capacity=capacity, table_type=table_type))
        return commit_or_rollback('Table added successfully.', 'tables')
    except ValueError as error:
        flash_error(str(error))
        return redirect(url_for('tables'))


@app.route('/tables/<int:table_id>/edit', methods=['POST'])
def edit_table(table_id):
    table = RestaurantTable.query.get_or_404(table_id)
    try:
        table.capacity, table.table_type = validate_table_fields(
            request.form.get('capacity'),
            request.form.get('table_type'),
        )
        return commit_or_rollback('Table updated successfully.', 'tables')
    except ValueError as error:
        flash_error(str(error))
        return redirect(url_for('tables'))


@app.route('/tables/<int:table_id>/delete', methods=['POST'])
def delete_table(table_id):
    table = RestaurantTable.query.get_or_404(table_id)
    db.session.delete(table)
    return commit_or_rollback('Table deleted successfully.', 'tables')


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
    try:
        customer_id, table_id, reservation_time, party_size, status = validate_reservation_fields(
            request.form.get('customer_id'),
            request.form.get('table_id'),
            request.form.get('reservation_time'),
            request.form.get('party_size'),
            request.form.get('status'),
        )
        db.session.add(Reservation(
            customer_id=customer_id,
            table_id=table_id,
            reservation_time=reservation_time,
            party_size=party_size,
            status=status,
        ))
        return commit_or_rollback('Reservation added successfully.', 'reservations')
    except ValueError as error:
        flash_error(str(error))
        return redirect(url_for('reservations'))


@app.route('/reservations/<int:reservation_id>/edit', methods=['POST'])
def edit_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    try:
        (
            reservation.customer_id,
            reservation.table_id,
            reservation.reservation_time,
            reservation.party_size,
            reservation.status,
        ) = validate_reservation_fields(
            request.form.get('customer_id'),
            request.form.get('table_id'),
            request.form.get('reservation_time'),
            request.form.get('party_size'),
            request.form.get('status'),
        )
        return commit_or_rollback('Reservation updated successfully.', 'reservations')
    except ValueError as error:
        flash_error(str(error))
        return redirect(url_for('reservations'))


@app.route('/reservations/<int:reservation_id>/delete', methods=['POST'])
def delete_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    db.session.delete(reservation)
    return commit_or_rollback('Reservation deleted successfully.', 'reservations')


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
    try:
        customer_id, order_type, status, cleaned_items = validate_order_fields(
            request.form.get('customer_id'),
            request.form.get('order_type'),
            request.form.get('status'),
            request.form.getlist('food_name'),
            request.form.getlist('quantity'),
        )

        order = Order(customer_id=customer_id, order_type=order_type, status=status, order_time=datetime.utcnow(), cost=0)
        db.session.add(order)
        db.session.flush()

        total = Decimal('0.00')
        for item, quantity in cleaned_items:
            line_price = Decimal(item.price) * quantity
            total += line_price
            db.session.add(OrderItem(order_id=order.order_id, food_name=item.food_name, quantity=quantity, price=Decimal(item.price)))

        order.cost = total.quantize(Decimal('0.01'))
        return commit_or_rollback('Order created successfully.', 'orders')
    except ValueError as error:
        db.session.rollback()
        flash_error(str(error))
        return redirect(url_for('orders'))
    except SQLAlchemyError:
        db.session.rollback()
        flash_error('A database error occurred while creating the order. Please try again.')
        return redirect(url_for('orders'))


@app.route('/orders/<int:order_id>/status', methods=['POST'])
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    status = normalize_text(request.form.get('status'))
    if status not in VALID_ORDER_STATUSES:
        flash_error('Please choose a valid order status.')
        return redirect(url_for('orders'))
    order.status = status
    return commit_or_rollback('Order status updated successfully.', 'orders')


@app.route('/orders/<int:order_id>/delete', methods=['POST'])
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    return commit_or_rollback('Order deleted successfully.', 'orders')


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
