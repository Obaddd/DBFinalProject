CREATE TABLE customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    phone VARCHAR(30) NOT NULL
);

CREATE TABLE menu_items (
    food_name VARCHAR(120) PRIMARY KEY,
    category VARCHAR(60) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    is_available BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE restaurant_tables (
    table_id INT AUTO_INCREMENT PRIMARY KEY,
    capacity INT NOT NULL,
    table_type VARCHAR(50) NOT NULL
);

CREATE TABLE reservations (
    reservation_id INT AUTO_INCREMENT PRIMARY KEY,
    reservation_time DATETIME NOT NULL,
    party_size INT NOT NULL,
    table_id INT NOT NULL,
    customer_id INT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'Booked',
    CONSTRAINT fk_reservation_table FOREIGN KEY (table_id) REFERENCES restaurant_tables(table_id),
    CONSTRAINT fk_reservation_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    cost DECIMAL(10,2) NOT NULL DEFAULT 0,
    order_time DATETIME NOT NULL,
    customer_id INT NOT NULL,
    order_type VARCHAR(30) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'Placed',
    CONSTRAINT fk_order_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE order_items (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    food_name VARCHAR(120) NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_order_items_order FOREIGN KEY (order_id) REFERENCES orders(order_id),
    CONSTRAINT fk_order_items_menu FOREIGN KEY (food_name) REFERENCES menu_items(food_name)
);
