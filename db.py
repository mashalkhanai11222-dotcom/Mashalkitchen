import os
import sqlite3
import datetime
import random
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash

# Global database status tracker
DB_STATUS = {
    'engine': 'Checking...',
    'is_mysql': False,
    'database': Config.DB_NAME,
    'host': Config.DB_HOST,
    'port': Config.DB_PORT
}

# ----------------- SQLite Dict Cursor Adapter -----------------
class SQLiteDictCursor:
    """Provides a PyMySQL DictCursor-compatible interface for SQLite."""
    def __init__(self, sqlite_conn):
        self.conn = sqlite_conn
        self.cursor = sqlite_conn.cursor()
        self.lastrowid = None
        self.rowcount = 0

    def execute(self, query, params=None):
        # Convert MySQL %s parameter placeholders to SQLite ? placeholders
        clean_query = query.replace('%s', '?')
        # Handle MySQL specific syntax differences if any
        clean_query = clean_query.replace('AUTO_INCREMENT', 'AUTOINCREMENT')
        clean_query = clean_query.replace('TINYINT(1)', 'INTEGER')
        
        if params is None:
            self.cursor.execute(clean_query)
        else:
            if isinstance(params, (list, tuple)):
                self.cursor.execute(clean_query, params)
            else:
                self.cursor.execute(clean_query, (params,))
        self.lastrowid = self.cursor.lastrowid
        self.rowcount = self.cursor.rowcount
        return self

    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    def fetchall(self):
        rows = self.cursor.fetchall()
        return [dict(r) for r in rows]

    def close(self):
        self.cursor.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

class SQLiteConnectionWrapper:
    """Wraps an SQLite connection to behave like a PyMySQL connection."""
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.isolation_level = None  # Autocommit mode

    def cursor(self):
        return SQLiteDictCursor(self.conn)

    def close(self):
        self.conn.close()

# ----------------- Database Connection Factory -----------------
def get_db_connection():
    """
    Connects to MySQL if accessible.
    If MySQL is not running or unreachable, seamlessly falls back to local SQLite mirror
    so that page loads NEVER fail with an unhandled 500 error.
    """
    global DB_STATUS
    # Try MySQL first
    try:
        import pymysql
        from pymysql.cursors import DictCursor
        conn = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            cursorclass=DictCursor,
            autocommit=True,
            connect_timeout=2
        )
        DB_STATUS['engine'] = f"MySQL: {Config.DB_NAME}"
        DB_STATUS['is_mysql'] = True
        return conn
    except Exception as mysql_err:
        # MySQL unavailable - fall back to SQLite mirror
        db_path = os.path.join(os.path.dirname(__file__), 'mashalkitchen.db')
        DB_STATUS['engine'] = "SQLite Mirror (Local)"
        DB_STATUS['is_mysql'] = False
        return SQLiteConnectionWrapper(db_path)

def get_db_status():
    """Returns current database connection status."""
    return DB_STATUS

# ----------------- Database Schema & Data Initialization -----------------
def init_db():
    """
    Initializes tables, seeds the 17 standard dishes, legacy customer orders,
    and sets up the default administrator account.
    Works transparently on either MySQL or the SQLite mirror.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 1. Food Table
            if DB_STATUS['is_mysql']:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS food (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        price INT NOT NULL,
                        category VARCHAR(50) DEFAULT 'Fast Food',
                        description TEXT,
                        image_url VARCHAR(255) DEFAULT '',
                        is_available TINYINT(1) DEFAULT 1
                    );
                """)
                cur.execute("DESCRIBE food;")
                cols = [r['Field'] for r in cur.fetchall()]
                if 'category' not in cols:
                    cur.execute("ALTER TABLE food ADD COLUMN category VARCHAR(50) DEFAULT 'Fast Food';")
                if 'description' not in cols:
                    cur.execute("ALTER TABLE food ADD COLUMN description TEXT;")
                if 'image_url' not in cols:
                    cur.execute("ALTER TABLE food ADD COLUMN image_url VARCHAR(255) DEFAULT '';")
                if 'is_available' not in cols:
                    cur.execute("ALTER TABLE food ADD COLUMN is_available TINYINT(1) DEFAULT 1;")
            else:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS food (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        price INTEGER NOT NULL,
                        category TEXT DEFAULT 'Fast Food',
                        description TEXT,
                        image_url TEXT DEFAULT '',
                        is_available INTEGER DEFAULT 1
                    );
                """)

            # 2. Orders Table
            if DB_STATUS['is_mysql']:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS orders (
                        order_id INT AUTO_INCREMENT PRIMARY KEY,
                        customer_name VARCHAR(100),
                        food_name VARCHAR(100),
                        quantity INT,
                        total_price INT,
                        order_code VARCHAR(50) DEFAULT '',
                        customer_phone VARCHAR(50) DEFAULT '',
                        delivery_address TEXT,
                        order_status VARCHAR(50) DEFAULT 'Pending',
                        payment_method VARCHAR(50) DEFAULT 'Cash on Delivery',
                        order_date DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cur.execute("DESCRIBE orders;")
                o_cols = [r['Field'] for r in cur.fetchall()]
                if 'order_code' not in o_cols:
                    cur.execute("ALTER TABLE orders ADD COLUMN order_code VARCHAR(50) DEFAULT '';")
                if 'customer_phone' not in o_cols:
                    cur.execute("ALTER TABLE orders ADD COLUMN customer_phone VARCHAR(50) DEFAULT '';")
                if 'delivery_address' not in o_cols:
                    cur.execute("ALTER TABLE orders ADD COLUMN delivery_address TEXT;")
                if 'order_status' not in o_cols:
                    cur.execute("ALTER TABLE orders ADD COLUMN order_status VARCHAR(50) DEFAULT 'Pending';")
                if 'payment_method' not in o_cols:
                    cur.execute("ALTER TABLE orders ADD COLUMN payment_method VARCHAR(50) DEFAULT 'Cash on Delivery';")
                if 'order_date' not in o_cols:
                    cur.execute("ALTER TABLE orders ADD COLUMN order_date DATETIME DEFAULT CURRENT_TIMESTAMP;")
                if 'order_notes' not in o_cols:
                    cur.execute("ALTER TABLE orders ADD COLUMN order_notes TEXT;")
                if 'delivery_fee' not in o_cols:
                    cur.execute("ALTER TABLE orders ADD COLUMN delivery_fee INT NOT NULL DEFAULT 0;")
            else:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS orders (
                        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        customer_name TEXT,
                        food_name TEXT,
                        quantity INTEGER,
                        total_price INTEGER,
                        order_code TEXT DEFAULT '',
                        customer_phone TEXT DEFAULT '',
                        delivery_address TEXT,
                        order_status TEXT DEFAULT 'Pending',
                        payment_method TEXT DEFAULT 'Cash on Delivery',
                        order_notes TEXT,
                        delivery_fee INTEGER NOT NULL DEFAULT 0,
                        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cur.execute("PRAGMA table_info(orders);")
                order_columns = [row['name'] for row in cur.fetchall()]
                if 'order_notes' not in order_columns:
                    cur.execute("ALTER TABLE orders ADD COLUMN order_notes TEXT;")
                if 'delivery_fee' not in order_columns:
                    cur.execute("ALTER TABLE orders ADD COLUMN delivery_fee INTEGER NOT NULL DEFAULT 0;")

            # 3. Admin Users Table
            if DB_STATUS['is_mysql']:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS admin_users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        full_name VARCHAR(100),
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                """)
            else:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS admin_users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        full_name TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

            if DB_STATUS['is_mysql']:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS contact_messages (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        customer_name VARCHAR(100) NOT NULL,
                        email VARCHAR(254) NOT NULL,
                        phone VARCHAR(50) NOT NULL,
                        message TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS customer_reviews (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        order_code VARCHAR(50) NOT NULL UNIQUE,
                        customer_name VARCHAR(100) NOT NULL,
                        rating TINYINT NOT NULL,
                        review_text TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                """)
            else:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS contact_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        customer_name TEXT NOT NULL,
                        email TEXT NOT NULL,
                        phone TEXT NOT NULL,
                        message TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS customer_reviews (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        order_code TEXT NOT NULL UNIQUE,
                        customer_name TEXT NOT NULL,
                        rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                        review_text TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

            # Seed Admin User if missing
            cur.execute("SELECT id FROM admin_users WHERE username = %s;", (Config.ADMIN_USERNAME,))
            if not cur.fetchone():
                admin_hash = generate_password_hash(Config.ADMIN_PASSWORD)
                cur.execute("""
                    INSERT INTO admin_users (username, password_hash, full_name)
                    VALUES (%s, %s, %s);
                """, (Config.ADMIN_USERNAME, admin_hash, 'Restaurant Administrator'))

            # 4. Standard menu with expanded variety and no Pepsi-brand beverage listing
            items_to_seed = [
                (1, 'Burger', 450, 'Burgers', 'Handcrafted beef patty grilled to perfection with cheddar, fresh lettuce, and house sauce in a warm brioche bun.', '/static/images/food/burger.jpg'),
                (2, 'Pizza', 1200, 'Pizza', 'Authentic Italian-style hand-stretched crust topped with rich herb tomato marinara and bubbly mozzarella.', '/static/images/food/pizza.jpg'),
                (3, 'Biryani', 300, 'Biryani', 'Traditional royal aromatic basmati rice layered with fragrant whole spices, saffron, and tender potatoes.', '/static/images/food/biryani.jpg'),
                (4, 'Fries', 200, 'Fast Food', 'Crispy golden potato fries seasoned with peri-peri salt, served with zesty garlic mayo dip.', '/static/images/food/fries.jpg'),
                (5, 'Shawarma', 250, 'Fast Food', 'Spiced roasted chicken shavings wrapped in warm toasted pita with creamy tahini and tangy pickles.', '/static/images/food/shawarma.jpg'),
                (6, 'Chicken Burger', 550, 'Burgers', 'Crispy tender chicken breast fillet with iceberg lettuce, melted cheese, and creamy mayo.', '/static/images/food/chicken-burger.jpg'),
                (7, 'Zinger Burger', 650, 'Burgers', 'Signature double-crunch spicy chicken fillet with fiery jalapeno sauce, cheddar, and crisp lettuce.', '/static/images/food/zinger-burger.jpg'),
                (8, 'Cheese Pizza', 1500, 'Pizza', 'Extra loaded four-cheese blend with mozzarella, parmesan, gouda, and cheddar on herb garlic crust.', '/static/images/food/cheese-pizza.jpg'),
                (9, 'Chicken Pizza', 1400, 'Pizza', 'Topped with spiced tandoori chicken chunks, sweet bell peppers, red onions, olives, and mozzarella.', '/static/images/food/chicken-pizza.jpg'),
                (10, 'Chicken Biryani', 350, 'Biryani', 'Aromatic long-grain basmati rice cooked with succulent chicken cuts, golden fried onions, and mint.', '/static/images/food/chicken-biryani.jpg'),
                (11, 'Beef Biryani', 450, 'Biryani', 'Slow-braised tender beef cubes layered with spicy saffron rice, cardamom, and caramelized onions.', '/static/images/food/beef-biryani.jpg'),
                (12, 'Chicken Karahi', 1800, 'BBQ', 'Traditional wok-cooked desi chicken with fresh vine tomatoes, ginger juliennes, green chilies, and roasted cumin.', '/static/images/food/chicken-karahi.jpg'),
                (13, 'Chicken Tikka', 400, 'BBQ', 'Charcoal-grilled juicy chicken quarter marinated overnight in spiced yogurt, lemon, and tandoori masala.', '/static/images/food/chicken-tikka.jpg'),
                (14, 'Sandwich', 300, 'Fast Food', 'Fresh toasted artisan bread stuffed with shredded chicken spread, crisp cucumbers, tomatoes, and egg salad.', '/static/images/food/sandwich.jpg'),
                (15, 'Club Sandwich', 450, 'Fast Food', 'Triple-decker toasted sandwich with smoked chicken, fried egg, cheese, crunchy lettuce, and dijonnaise.', '/static/images/food/club-sandwich.jpg'),
                (16, 'Soft Drink', 100, 'Drinks', 'Chilled refreshing soda served well chilled for a crisp, fizzy finish to your meal.', '/static/images/food/cold-drink.jpg'),
                (17, 'Fresh Juice', 200, 'Drinks', 'Freshly pressed 100% pure seasonal fruit juice (Orange, Apple, Mango) with no added sugar.', '/static/images/food/fresh-juice.jpg'),
                (18, 'Mango Shake', 220, 'Drinks', 'Creamy chilled mango shake blended with real fruit pulp and a dash of cream.', '/static/images/food/fresh-juice.jpg'),
                (19, 'Lassi', 180, 'Drinks', 'Traditional yogurt drink blended with mint and a hint of roasted cumin for a cool finish.', '/static/images/food/fresh-juice.jpg'),
                (20, 'Chicken Roll', 350, 'Fast Food', 'Juicy chicken tikka wrapped in soft paratha with crunchy salad and creamy garlic sauce.', '/static/images/food/shawarma.jpg'),
                (21, 'Seekh Kebab', 500, 'BBQ', 'Charcoal-grilled minced kebabs served with onions, green chutney, and warm naan.', '/static/images/food/chicken-tikka.jpg'),
                (22, 'Paneer Tikka', 450, 'BBQ', 'Smoky grilled paneer cubes packed with spices, peppers, and a hint of lemon.', '/static/images/food/chicken-tikka.jpg'),
                (23, 'Naan Chana', 280, 'Fast Food', 'Freshly baked naan paired with rich spiced chickpea curry for a hearty snack.', '/static/images/food/biryani.jpg')
            ]

            for item_id, name, price, category, desc, img in items_to_seed:
                cur.execute("SELECT id, name FROM food WHERE id = %s;", (item_id,))
                existing_by_id = cur.fetchone()
                if existing_by_id:
                    cur.execute("""
                        UPDATE food
                        SET name = %s,
                            price = %s,
                            category = %s,
                            description = %s,
                            image_url = %s,
                            is_available = 1
                        WHERE id = %s;
                    """, (name, price, category, desc, img, item_id))
                    continue

                cur.execute("SELECT id FROM food WHERE LOWER(name) = LOWER(%s) LIMIT 1;", (name,))
                existing_by_name = cur.fetchone()
                if existing_by_name:
                    cur.execute("""
                        UPDATE food
                        SET price = %s,
                            category = %s,
                            description = %s,
                            image_url = %s,
                            is_available = 1
                        WHERE id = %s;
                    """, (price, category, desc, img, existing_by_name['id']))
                else:
                    cur.execute("""
                        INSERT INTO food (id, name, price, category, description, image_url, is_available)
                        VALUES (%s, %s, %s, %s, %s, %s, 1);
                    """, (item_id, name, price, category, desc, img))

            # 5. Seed Legacy Preserved Customer Orders if table is empty
            cur.execute("SELECT COUNT(*) AS cnt FROM orders;")
            order_count = cur.fetchone()['cnt']
            if order_count == 0:
                legacy_orders = [
                    (1, 'Mashal', 'Burger', 2, 900, 'ORD-260101-101', '0312-3456789', 'Main Bazar, Chota Lahor, Swabi', 'Delivered', 'Cash on Delivery', '2026-10-15 13:45:00'),
                    (2, 'Ali', 'Pizza', 1, 1200, 'ORD-260101-102', '0300-1234567', 'College Road, Chota Lahor, Swabi', 'Delivered', 'Cash on Delivery', '2026-10-16 19:20:00'),
                    (3, 'hamza', 'Biryani', 3, 900, 'ORD-260101-103', '0333-9876543', 'Near Civil Hospital, Chota Lahor, Swabi', 'Delivered', 'JazzCash', '2026-10-17 14:10:00'),
                    (4, 'haris', 'Fries', 5, 1000, 'ORD-260101-104', '0345-5551234', 'Swabi Road, Chota Lahor', 'Delivered', 'Cash on Delivery', '2026-10-18 16:30:00'),
                    (5, 'Sara', 'Shawarma', 4, 1000, 'ORD-260101-105', '0315-7778899', 'Gulberg Colony, Chota Lahor, Swabi', 'Delivered', 'EasyPaisa', '2026-10-19 20:05:00')
                ]
                for o in legacy_orders:
                    cur.execute("""
                        INSERT INTO orders 
                        (order_id, customer_name, food_name, quantity, total_price, order_code, 
                         customer_phone, delivery_address, order_status, payment_method, order_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """, o)
    finally:
        conn.close()

# ----------------- Food Menu Operations -----------------
def get_all_food(category=None, search=None, only_available=True):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            query = "SELECT * FROM food WHERE 1=1"
            params = []
            if only_available:
                query += " AND is_available = 1"
            if category and category != 'All':
                query += " AND category = %s"
                params.append(category)
            if search:
                query += " AND (name LIKE %s OR description LIKE %s)"
                term = f"%{search}%"
                params.extend([term, term])
            query += " ORDER BY category, name"
            cur.execute(query, params)
            return cur.fetchall()
    finally:
        conn.close()

def get_food_by_id(food_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM food WHERE id = %s;", (food_id,))
            return cur.fetchone()
    finally:
        conn.close()

def add_food(name, price, category, description, image_url):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM food WHERE LOWER(name) = LOWER(%s) LIMIT 1;", (name,))
            if cur.fetchone():
                raise ValueError("A food item with this name already exists.")
            cur.execute("""
                INSERT INTO food (name, price, category, description, image_url, is_available)
                VALUES (%s, %s, %s, %s, %s, 1);
            """, (name, price, category, description, image_url))
            return cur.lastrowid
    finally:
        conn.close()

def update_food(food_id, name, price, category, description, image_url, is_available=1):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM food WHERE LOWER(name) = LOWER(%s) AND id != %s LIMIT 1;",
                (name, food_id)
            )
            if cur.fetchone():
                raise ValueError("A food item with this name already exists.")
            cur.execute("""
                UPDATE food 
                SET name = %s, price = %s, category = %s, description = %s, 
                    image_url = %s, is_available = %s
                WHERE id = %s;
            """, (name, price, category, description, image_url, is_available, food_id))
            return cur.rowcount > 0
    finally:
        conn.close()

def delete_food(food_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM food WHERE id = %s;", (food_id,))
            return cur.rowcount > 0
    finally:
        conn.close()

def get_food_categories():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT category, COUNT(*) AS food_count,
                       SUM(CASE WHEN is_available = 1 THEN 1 ELSE 0 END) AS available_count
                FROM food
                GROUP BY category
                ORDER BY category;
            """)
            return cur.fetchall()
    finally:
        conn.close()

def rename_food_category(old_name, new_name):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS count FROM food WHERE category = %s;", (old_name,))
            if not cur.fetchone()['count']:
                return False
            cur.execute("UPDATE food SET category = %s WHERE category = %s;", (new_name, old_name))
            return cur.rowcount > 0
    finally:
        conn.close()

# ----------------- Customer Orders Operations -----------------
def place_order(customer_name, customer_phone, delivery_address, payment_method, cart_items, order_notes=''):
    """
    Saves new order items into MySQL/SQLite 'orders' table.
    Authoritative verification: totals are calculated using actual food prices in database.
    """
    if not cart_items:
        raise ValueError("Shopping cart is empty.")

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            timestamp = datetime.datetime.now().strftime("%y%m%d%H%M")
            random_digits = random.randint(100, 999)
            order_code = f"ORD-{timestamp}-{random_digits}"
            order_date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            validated_items = []
            subtotal = 0
            for item in cart_items:
                if not isinstance(item, dict):
                    raise ValueError("Invalid cart item.")
                food_id = item.get('id')
                quantity = item.get('quantity', 1)
                if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1 or quantity > 99:
                    raise ValueError("Each item quantity must be between 1 and 99.")

                cur.execute("SELECT id, name, price, is_available FROM food WHERE id = %s;", (food_id,))
                db_food = cur.fetchone()
                if not db_food or not db_food['is_available']:
                    raise ValueError("A selected food item is no longer available.")
                item_total = int(db_food['price']) * quantity
                subtotal += item_total
                validated_items.append((db_food, quantity, item_total))

            if not validated_items:
                raise ValueError("Shopping cart is empty.")

            delivery_fee = 0 if subtotal > 1500 else 100
            grand_total = subtotal + delivery_fee
            placed_records = []

            for index, (db_food, quantity, item_total) in enumerate(validated_items):
                cur.execute("""
                    INSERT INTO orders 
                    (customer_name, food_name, quantity, total_price, order_code, 
                     customer_phone, delivery_address, order_status, payment_method, order_date,
                     order_notes, delivery_fee)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, (
                    customer_name,
                    db_food['name'],
                    quantity,
                    item_total,
                    order_code,
                    customer_phone,
                    delivery_address,
                    'Pending',
                    payment_method or 'Cash on Delivery',
                    order_date_str,
                    order_notes,
                    delivery_fee if index == 0 else 0
                ))
                placed_records.append({
                    'order_id': cur.lastrowid,
                    'food_name': db_food['name'],
                    'unit_price': db_food['price'],
                    'quantity': quantity,
                    'total_price': item_total
                })

            return {
                'order_code': order_code,
                'customer_name': customer_name,
                'customer_phone': customer_phone,
                'delivery_address': delivery_address,
                'payment_method': payment_method,
                'items': placed_records,
                'subtotal': subtotal,
                'delivery_fee': delivery_fee,
                'grand_total': grand_total,
                'order_date': order_date_str,
                'status': 'Pending'
            }
    finally:
        conn.close()

def get_popular_food(limit=6):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT f.*
                FROM food f
                LEFT JOIN (
                    SELECT food_name, SUM(quantity) AS sold
                    FROM orders
                    GROUP BY food_name
                ) sales ON sales.food_name = f.name
                WHERE f.is_available = 1
                ORDER BY COALESCE(sales.sold, 0) DESC, f.name
                LIMIT %s;
            """, (limit,))
            return cur.fetchall()
    finally:
        conn.close()

def save_contact_message(customer_name, email, phone, message):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO contact_messages (customer_name, email, phone, message)
                VALUES (%s, %s, %s, %s);
            """, (customer_name, email, phone, message))
            return cur.lastrowid
    finally:
        conn.close()

def get_recent_reviews(limit=6):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT customer_name, rating, review_text, created_at
                FROM customer_reviews
                ORDER BY id DESC
                LIMIT %s;
            """, (limit,))
            return cur.fetchall()
    finally:
        conn.close()

def add_customer_review(order_code, customer_phone, rating, review_text):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT customer_name
                FROM orders
                WHERE order_code = %s AND customer_phone = %s AND order_status = 'Delivered'
                LIMIT 1;
            """, (order_code, customer_phone))
            order = cur.fetchone()
            if not order:
                raise ValueError("A delivered order matching that reference and phone number was not found.")

            cur.execute("SELECT id FROM customer_reviews WHERE order_code = %s;", (order_code,))
            if cur.fetchone():
                raise ValueError("A review has already been submitted for this order.")

            cur.execute("""
                INSERT INTO customer_reviews (order_code, customer_name, rating, review_text)
                VALUES (%s, %s, %s, %s);
            """, (order_code, order['customer_name'], rating, review_text))
            return cur.lastrowid
    finally:
        conn.close()

def get_orders(search=None, status=None, limit=100):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            query = "SELECT * FROM orders WHERE 1=1"
            params = []
            if status and status != 'All':
                query += " AND order_status = %s"
                params.append(status)
            if search:
                query += " AND (customer_name LIKE %s OR food_name LIKE %s OR order_code LIKE %s OR customer_phone LIKE %s)"
                term = f"%{search}%"
                params.extend([term, term, term, term])
            query += " ORDER BY order_id DESC LIMIT %s"
            params.append(limit)
            cur.execute(query, params)
            return cur.fetchall()
    finally:
        conn.close()

def get_customer_orders(search_query):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            query = """
                SELECT * FROM orders 
                WHERE order_code = %s OR customer_phone = %s OR customer_name LIKE %s 
                ORDER BY order_id DESC;
            """
            term = f"%{search_query}%"
            cur.execute(query, (search_query, search_query, term))
            return cur.fetchall()
    finally:
        conn.close()

def delete_order(order_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT order_code FROM orders WHERE order_id = %s;", (order_id,))
            order = cur.fetchone()
            if not order:
                return None
            if order['order_code']:
                cur.execute("DELETE FROM orders WHERE order_code = %s;", (order['order_code'],))
            else:
                cur.execute("DELETE FROM orders WHERE order_id = %s;", (order_id,))
            return {'order_id': order_id, 'order_code': order['order_code'] or ''}
    finally:
        conn.close()

def update_order_status(order_id, new_status):
    valid_statuses = ['Pending', 'Confirmed', 'Preparing', 'Out for Delivery', 'Delivered', 'Cancelled']
    if new_status not in valid_statuses:
        raise ValueError(f"Invalid status '{new_status}'")

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT order_code FROM orders WHERE order_id = %s;", (order_id,))
            order = cur.fetchone()
            if not order:
                return False
            if order['order_code']:
                cur.execute("UPDATE orders SET order_status = %s WHERE order_code = %s;", (new_status, order['order_code']))
            else:
                cur.execute("UPDATE orders SET order_status = %s WHERE order_id = %s;", (new_status, order_id))
            return cur.rowcount > 0
    finally:
        conn.close()

# ----------------- SQL Aggregate Analytics & Reports -----------------
def get_sales_analytics():
    """
    Executes standard SQL aggregate queries:
    - SUM(total_price) AS total_sales
    - COUNT(*) AS total_orders
    - AVG(total_price) AS avg_order_value
    - MAX(price) & MIN(price)
    - GROUP BY customer_name for customer spending analysis
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 1. Total sales (SUM)
            cur.execute("SELECT COALESCE(SUM(total_price + delivery_fee), 0) AS total_sales FROM orders;")
            total_sales = cur.fetchone()['total_sales'] or 0

            # 2. Total orders; modern multi-item orders share an order code.
            cur.execute("SELECT COUNT(*) AS total_order_items FROM orders;")
            total_order_items = cur.fetchone()['total_order_items'] or 0

            cur.execute("""
                SELECT COUNT(DISTINCT NULLIF(order_code, '')) AS coded_orders,
                       SUM(CASE WHEN order_code IS NULL OR order_code = '' THEN 1 ELSE 0 END) AS legacy_orders
                FROM orders;
            """)
            order_counts = cur.fetchone()
            total_orders = int(order_counts['coded_orders'] or 0) + int(order_counts['legacy_orders'] or 0)

            # 3. Average full order value rather than average line-item value.
            cur.execute("""
                SELECT COALESCE(AVG(order_total), 0) AS avg_order_value
                FROM (
                    SELECT SUM(total_price + delivery_fee) AS order_total
                    FROM orders
                    GROUP BY CASE
                        WHEN order_code IS NULL OR order_code = '' THEN CAST(order_id AS CHAR)
                        ELSE order_code
                    END
                ) AS order_totals;
            """)
            avg_order_value = round(float(cur.fetchone()['avg_order_value'] or 0), 2)

            # 4. Highest and lowest price (MAX & MIN)
            cur.execute("SELECT MAX(price) AS max_price, MIN(price) AS min_price FROM food;")
            extrema = cur.fetchone()
            max_price = extrema['max_price'] or 0
            min_price = extrema['min_price'] or 0

            # 5. Customer-wise spending (GROUP BY customer_name)
            cur.execute("""
                SELECT customer_name, SUM(total_price) AS total_spent, COUNT(*) AS items_count
                FROM orders
                GROUP BY customer_name
                ORDER BY total_spent DESC;
            """)
            raw_spending = cur.fetchall()
            customer_spending = [
                {
                    'customer_name': r['customer_name'] or 'Guest',
                    'total_spent': int(r['total_spent'] or 0),
                    'items_count': int(r['items_count'] or 0)
                } for r in raw_spending
            ]

            # 6. Top selling items (GROUP BY food_name)
            cur.execute("""
                SELECT food_name, SUM(quantity) AS total_quantity, SUM(total_price) AS total_revenue
                FROM orders
                GROUP BY food_name
                ORDER BY total_quantity DESC
                LIMIT 10;
            """)
            raw_popular = cur.fetchall()
            popular_items = [
                {
                    'food_name': r['food_name'] or 'Dish',
                    'total_quantity': int(r['total_quantity'] or 0),
                    'total_revenue': int(r['total_revenue'] or 0)
                } for r in raw_popular
            ]

            # 7. Order status breakdown
            cur.execute("""
                SELECT COALESCE(order_status, 'Delivered') AS status,
                       COUNT(DISTINCT CASE
                           WHEN order_code IS NULL OR order_code = '' THEN CAST(order_id AS CHAR)
                           ELSE order_code
                       END) AS count
                FROM orders
                GROUP BY order_status;
            """)
            status_breakdown = cur.fetchall()

            # 8. Category revenue breakdown
            cur.execute("""
                SELECT COALESCE(f.category, 'Fast Food') AS category, SUM(o.total_price) AS revenue
                FROM orders o
                LEFT JOIN food f ON o.food_name = f.name
                GROUP BY f.category
                ORDER BY revenue DESC;
            """)
            raw_cat = cur.fetchall()
            category_breakdown = [
                {
                    'category': r['category'] or 'Fast Food',
                    'revenue': int(r['revenue'] or 0)
                } for r in raw_cat
            ]

            # 9. Additional metric counts: Pending & Delivered orders
            cur.execute("""
                SELECT COUNT(DISTINCT CASE
                    WHEN order_code IS NULL OR order_code = '' THEN CAST(order_id AS CHAR)
                    ELSE order_code
                END) AS cnt
                FROM orders WHERE order_status = 'Pending';
            """)
            pending_orders = cur.fetchone()['cnt'] or 0

            cur.execute("""
                SELECT COUNT(DISTINCT CASE
                    WHEN order_code IS NULL OR order_code = '' THEN CAST(order_id AS CHAR)
                    ELSE order_code
                END) AS cnt
                FROM orders WHERE order_status = 'Delivered';
            """)
            delivered_orders = cur.fetchone()['cnt'] or 0

            cur.execute("SELECT COUNT(*) AS cnt FROM food;")
            total_food_items = cur.fetchone()['cnt'] or 0
            cur.execute("""
                SELECT COUNT(DISTINCT CASE
                    WHEN customer_phone IS NULL OR customer_phone = '' THEN LOWER(customer_name)
                    ELSE customer_phone
                END) AS cnt
                FROM orders;
            """)
            total_customers = cur.fetchone()['cnt'] or 0

            cutoff = (datetime.date.today() - datetime.timedelta(days=365)).isoformat()
            cur.execute("""
                SELECT DATE(order_date) AS sale_day,
                       SUM(total_price + delivery_fee) AS sales
                FROM orders
                WHERE order_date >= %s
                GROUP BY DATE(order_date)
                ORDER BY sale_day;
            """, (cutoff,))
            sales_by_day = {}
            for row in cur.fetchall():
                raw_day = row['sale_day']
                if isinstance(raw_day, datetime.datetime):
                    sale_day = raw_day.date()
                elif isinstance(raw_day, datetime.date):
                    sale_day = raw_day
                else:
                    try:
                        sale_day = datetime.datetime.strptime(str(raw_day)[:10], '%Y-%m-%d').date()
                    except (TypeError, ValueError):
                        continue
                sales_by_day[sale_day] = int(row['sales'] or 0)

            today = datetime.date.today()
            daily_points = []
            for offset in range(6, -1, -1):
                day = today - datetime.timedelta(days=offset)
                daily_points.append({
                    'label': day.strftime('%b %d'),
                    'sales': sales_by_day.get(day, 0)
                })

            weekly_points = []
            current_week = today - datetime.timedelta(days=today.weekday())
            for offset in range(11, -1, -1):
                week_start = current_week - datetime.timedelta(weeks=offset)
                week_end = week_start + datetime.timedelta(days=6)
                weekly_points.append({
                    'label': week_start.strftime('%b %d'),
                    'sales': sum(
                        value for day, value in sales_by_day.items()
                        if week_start <= day <= week_end
                    )
                })

            monthly_points = []
            for offset in range(11, -1, -1):
                month_index = today.year * 12 + today.month - 1 - offset
                year, month_zero = divmod(month_index, 12)
                month = month_zero + 1
                monthly_points.append({
                    'label': datetime.date(year, month, 1).strftime('%b %Y'),
                    'sales': sum(
                        value for day, value in sales_by_day.items()
                        if day.year == year and day.month == month
                    )
                })

            return {
                'total_sales': int(total_sales),
                'total_orders': int(total_orders),
                'total_order_items': int(total_order_items),
                'avg_order_value': float(avg_order_value),
                'max_price': int(max_price),
                'min_price': int(min_price),
                'pending_orders': int(pending_orders),
                'delivered_orders': int(delivered_orders),
                'total_food_items': int(total_food_items),
                'total_customers': int(total_customers),
                'customer_spending': customer_spending,
                'popular_items': popular_items,
                'status_breakdown': status_breakdown,
                'category_breakdown': category_breakdown,
                'sales_trends': {
                    'daily': daily_points,
                    'weekly': weekly_points,
                    'monthly': monthly_points
                }
            }
    finally:
        conn.close()

# ----------------- Administrator Authentication -----------------
def authenticate_admin(username, password):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM admin_users WHERE username = %s;", (username,))
            user = cur.fetchone()
            if user and check_password_hash(user['password_hash'], password):
                return user
            # Fallback direct check against Config
            if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
                return {'id': 1, 'username': Config.ADMIN_USERNAME, 'full_name': 'Restaurant Administrator'}
            return None
    finally:
        conn.close()
