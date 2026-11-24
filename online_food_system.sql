CREATE DATABASE food_order;

USE food_order;

CREATE TABLE food (
    id INT PRIMARY KEY,
    name VARCHAR(50),
    price INT
);

INSERT INTO food VALUES
(1, 'Burger', 450),
(2, 'Pizza', 1200),
(3, 'Biryani', 300),
(4, 'Fries', 200),
(5, 'Shawarma', 250);


SELECT * FROM food;

CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer_name VARCHAR(50),
    food_name VARCHAR(50),
    quantity INT,
    total_price INT
);


INSERT INTO orders VALUES
(2, 'Ali', 'Pizza', 1, 1200),
(3, 'hamza', 'Biryani', 3, 900),
(4, 'haris', 'Fries', 5, 1000),
(5, 'Sara', 'Shawarma', 4, 1000);


SELECT * FROM orders;

SELECT SUM(total_price) AS total_sales
FROM orders;

SELECT customer_name, SUM(total_price) AS total_spent
FROM orders
GROUP BY customer_name;
