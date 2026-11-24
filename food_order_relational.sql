CREATE DATABASE food_order;

USE food_order;

-- 1. Create Food Table
CREATE TABLE food (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    price INT NOT NULL CHECK (price > 0)
);

-- 2. Insert Food Records
INSERT INTO food (name, price) VALUES
('Burger', 450),
('Pizza', 1200),
('Biryani', 300),
('Fries', 200),
('Shawarma', 250);

-- 3. Create Orders Table
CREATE TABLE orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_name VARCHAR(50) NOT NULL,
    food_id INT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),

    FOREIGN KEY (food_id) REFERENCES food(id)
);

-- 4. Insert Orders
INSERT INTO orders (customer_name, food_id, quantity) VALUES
('Ali', 2, 1),
('Hamza', 3, 3),
('Haris', 4, 5),
('Sara', 5, 4);

-- 5. Display Food
SELECT * FROM food;

-- 6. Display Orders with Food Details
SELECT
    orders.order_id,
    orders.customer_name,
    food.name AS food_name,
    food.price,
    orders.quantity,
    (food.price * orders.quantity) AS total_price
FROM orders
JOIN food ON orders.food_id = food.id;

-- 7. Calculate Total Sales
SELECT SUM(food.price * orders.quantity) AS total_sales
FROM orders
JOIN food ON orders.food_id = food.id;

-- 8. Total Spending of Each Customer
SELECT
    orders.customer_name,
    SUM(food.price * orders.quantity) AS total_spent
FROM orders
JOIN food ON orders.food_id = food.id
GROUP BY orders.customer_name;

-- 9. Find Most Expensive Food
SELECT * FROM food
ORDER BY price DESC
LIMIT 1;

-- 10. Find Cheapest Food
SELECT * FROM food
ORDER BY price ASC
LIMIT 1;

-- 11. Update Food Price
UPDATE food
SET price = 500
WHERE name = 'Burger';

-- 12. Delete an Order
DELETE FROM orders
WHERE order_id = 4;

-- 13. Count Total Orders
SELECT COUNT(*) AS total_orders
FROM orders;

-- 14. Find Customers Who Spent More Than 1000
SELECT
    customer_name,
    SUM(food.price * orders.quantity) AS total_spent
FROM orders
JOIN food ON orders.food_id = food.id
GROUP BY customer_name
HAVING total_spent > 1000;

SELECT * FROM orders;