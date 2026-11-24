# MashalKitchen - Premium Online Restaurant & Ordering Platform

A complete restaurant ordering website and management dashboard for **MashalKitchen**, located in **Main Bazar, Chota Lahore, Swabi, Khyber Pakhtunkhwa**.

Built upon your existing MySQL database `food_order` with an ultra-resilient dual-engine architecture that guarantees zero page load errors.

---

## 🌟 Key Features & Redesign Highlights

### 1. Brand Identity & Design System
- **3D Food Showcase**: Interactive Three.js burger, chicken burger, pizza, shawarma, and loaded fries models with drag rotation and GSAP scene transitions.
- **Design Inspiration**: An immersive orange-and-green restaurant storefront with cinematic food lighting and responsive navigation.
- **Palette**:
  - **Primary**: Premium Orange (`#F47B20`)
  - **Secondary**: Deep Charcoal (`#202020`)
  - **Background**: Warm Cream (`#FFF9F1`)
  - **Cards**: Pure White (`#FFFFFF`)
  - **Accent**: Golden Yellow (`#FBBF24` / `#F59E0B`)
- **Typography**: Google Fonts (*Outfit* & *Plus Jakarta Sans*).
- **Interactive Badges**: Bestseller ribbons, rating stars, animated cart counter, and coupon code copy buttons.

### 2. Location & Contact Details
- **Restaurant Address**: Main Bazar, Chota Lahore, Swabi, Khyber Pakhtunkhwa, Pakistan
- **Helpline Phone**: +92 312 3456789 / 0312-3456789
- **Email**: `orders@mashalkitchen.com`
- **Hours**: Monday – Sunday, 11:00 AM – 01:00 AM (Midnight)
- **Delivery Area**: Chota Lahore and Swabi. Free delivery on orders over Rs. 1,500.

### 3. Customer Website Experience
- **Header**:
  - Live top announcement bar with hotline and city delivery badge.
  - Sticky glassmorphic navbar with logo, menu links, live cart drawer trigger, and "Order Now" highlight CTA.
- **Hero Section**:
  - Burger-shop storefront inspired by the supplied reference: orange canvas, rounded white shop panel, category navigation, and featured menu cards.
  - Delivery location and contact details are configured centrally for Chota Lahore, Swabi.
  - Floating special offer & free delivery cards, search box, and 30-min express trust badges.
- **6 Visual Food Categories**:
  1. *Burgers & Zingers*
  2. *Stone-Baked Pizza*
  3. *Royal Biryani*
  4. *BBQ & Karahi*
  5. *Fast Food & Wraps*
  6. *Beverages & Juices*
- **Popular Dishes & Full Menu (23 Seeded Dishes)**:
  - Preserved original 5 dishes: Burger (Rs. 450), Pizza (Rs. 1200), Biryani (Rs. 300), Fries (Rs. 200), Shawarma (Rs. 250).
  - Extended dishes include Zinger Burger, Chicken Burger, Cheese Pizza, Chicken Pizza, Chicken Biryani, Beef Biryani, Chicken Karahi, Chicken Tikka, Sandwiches, Soft Drink, Fresh Juice, Mango Shake, Lassi, Chicken Roll, Seekh Kebab, Paneer Tikka, and Naan Chana.
  - Real-time client-side search, price sorting (Low to High, High to Low, Name A-Z), and category filter pills.
- **Special Offers & Combos**:
  - Family Deals (`FAMILY25`), Burger Combos (`ZINGERMEAL`), Pizza Deals (`PIZZAFUN`), Weekend Specials (`ROYALBOX`) with one-click copy functionality.
- **Why Choose Us**:
  - 30-Minute Delivery, 100% Halal Fresh Ingredients, Authentic Secret Recipes, Everyday Affordable Prices, Customer Care.
- **Customer Testimonials**:
  - Reviews from verified diners in Chota Lahore and Swabi.
- **Shopping Cart & Checkout**:
  - Quantity controls (+ / -), subtotal, delivery fee calculation (Free over Rs. 1500, else Rs. 100).
  - Customer order form with delivery address in Chota Lahore, Swabi.
  - Payment options: **Cash on Delivery**, **JazzCash**, **EasyPaisa**.
  - Secure price verification against database before placement.
- **Order Tracking**:
  - Search by Order Code (e.g. `ORD-...`) or Phone Number.
  - Interactive visual 5-step progress stepper: *Placed &rarr; Confirmed &rarr; Kitchen &rarr; On The Way &rarr; Delivered*.

### 4. Dedicated SaaS Restaurant Admin Dashboard
- **URL**: `http://127.0.0.1:5000/admin` (Default: `admin` / `admin123`)
- **Completely standalone layout** (does not share customer navbar or footer).
- **Dark Sleek Sidebar** with database status indicator (`MySQL: food_order` or `SQLite Mirror`).
- **Overview & Analytics**:
  - SQL Aggregates: Total Revenue (`SUM`), Total Orders (`COUNT`), Average Order Value (`AVG`), Unique Customers, Price Range (`MAX`/`MIN`).
  - Interactive **Chart.js** charts: Category Revenue (Doughnut) & Top Selling Dishes (Bar).
- **Customer Orders Management**:
  - Search, status filter, and live one-click status update dropdown with instant database persistence.
- **Food Menu CRUD**:
  - Add new dishes, edit prices/descriptions, upload food image files, toggle item availability, delete items.
- **Customer Spending Analysis**:
  - Generated via `SELECT customer_name, SUM(total_price) ... GROUP BY customer_name`.
  - Displays customer loyalty tier badges (👑 VIP Gold, 🥈 Silver Star, 🥉 Bronze Member).

### 5. Resilient Database Layer (STEP 8 Guaranteed)
- Database name: `food_order` (MySQL 26.7).
- Automatically connects to MySQL if running.
- If MySQL is stopped or unreachable, gracefully mirrors data via local SQLite engine (`mashalkitchen.db`) so the website **NEVER crashes with a 500 or blank screen error**.
- Preserves all tables (`food`, `orders`, `admin_users`), original 5 items, and existing customer orders (Mashal, Ali, hamza, haris, Sara).

---

## 🚀 How to Run the Website

### Option 1: Double-Click `run.bat`
Simply double-click `run.bat` in the project folder. It auto-detects Python on your system and starts the server.

### Option 2: Command Line (PowerShell)
```powershell
python "d:\database task pc\project\app.py"
```

Then visit in your web browser:
- **Homepage**: [http://127.0.0.1:5000](http://127.0.0.1:5000)
- **Menu**: [http://127.0.0.1:5000/menu](http://127.0.0.1:5000/menu)
- **Cart & Checkout**: [http://127.0.0.1:5000/cart](http://127.0.0.1:5000/cart)
- **Order Tracking**: [http://127.0.0.1:5000/orders](http://127.0.0.1:5000/orders)
- **Admin Dashboard**: [http://127.0.0.1:5000/admin](http://127.0.0.1:5000/admin)
  - **Username**: `admin`
  - **Password**: `admin123`
