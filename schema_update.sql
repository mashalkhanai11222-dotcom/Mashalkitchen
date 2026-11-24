-- =====================================================================
-- TasteHub Online Food Ordering System - Schema Enhancements
-- Safe, non-destructive migrations preserving existing food & orders data
-- =====================================================================

USE food_order;

-- 1. Enhance 'food' table without dropping existing records
ALTER TABLE food ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE food ADD COLUMN IF NOT EXISTS category VARCHAR(50) DEFAULT 'Fast Food';
ALTER TABLE food ADD COLUMN IF NOT EXISTS image_url VARCHAR(255) DEFAULT '';
ALTER TABLE food ADD COLUMN IF NOT EXISTS is_available TINYINT(1) DEFAULT 1;
ALTER TABLE food MODIFY COLUMN id INT AUTO_INCREMENT;

-- 2. Enhance 'orders' table without dropping existing records
ALTER TABLE orders ADD COLUMN IF NOT EXISTS order_code VARCHAR(30) DEFAULT '';
ALTER TABLE orders ADD COLUMN IF NOT EXISTS customer_phone VARCHAR(20) DEFAULT '';
ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_address TEXT;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS order_status VARCHAR(30) DEFAULT 'Pending';
ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_method VARCHAR(50) DEFAULT 'Cash on Delivery';
ALTER TABLE orders ADD COLUMN IF NOT EXISTS order_date DATETIME DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE orders MODIFY COLUMN order_id INT AUTO_INCREMENT;

-- 3. Dedicated Admin Users Table for Authentication
CREATE TABLE IF NOT EXISTS admin_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 4. Original 5 items preserved:
-- (1, 'Burger', 450)
-- (2, 'Pizza', 1200)
-- (3, 'Biryani', 300)
-- (4, 'Fries', 200)
-- (5, 'Shawarma', 250)

-- 5. New Requested Menu Items:
-- Chicken Burger (Rs. 550)
-- Zinger Burger (Rs. 650)
-- Cheese Pizza (Rs. 1500)
-- Chicken Pizza (Rs. 1400)
-- Chicken Biryani (Rs. 350)
-- Beef Biryani (Rs. 450)
-- Chicken Karahi (Rs. 1800)
-- Chicken Tikka (Rs. 400)
-- Sandwich (Rs. 300)
-- Club Sandwich (Rs. 450)
-- Cold Drink (Rs. 100)
-- Fresh Juice (Rs. 200)
-- 6. Insert new menu items into 'food' table
INSERT INTO food (name, price, description, category, image_url, is_available) VALUES
('Chicken Burger', 550, 'Juicy chicken patty with fresh lettuce and tomato.', 'Fast Food', '', 1),
('Zinger Burger', 650, 'Spicy chicken

-- Verification Queries:
SELECT * FROM food;
SELECT * FROM orders;
SELECT SUM(total_price) AS total_sales FROM orders;
SELECT customer_name, SUM(total_price) AS total_spent FROM orders GROUP BY customer_name;



