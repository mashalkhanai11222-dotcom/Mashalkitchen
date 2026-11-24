import os
import datetime
import re
import csv
import io
from functools import wraps
from urllib.parse import urlparse
from flask import (
    Flask, render_template, request, jsonify, redirect, 
    url_for, session, flash, send_from_directory, Response
)
from werkzeug.utils import secure_filename
from config import Config
import db

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database on startup
with app.app_context():
    try:
        db.init_db()
        print(f"MashalKitchen database online [{db.get_db_status()['engine']}]")
    except Exception as e:
        print("Database initialization notice:", e)

# Global context processor for brand metadata
@app.context_processor
def inject_restaurant_meta():
    return {
        'brand_name': Config.RESTAURANT_NAME,
        'brand_address': Config.RESTAURANT_ADDRESS,
        'brand_city': Config.RESTAURANT_CITY,
        'brand_phone': Config.RESTAURANT_PHONE,
        'brand_phone_raw': Config.RESTAURANT_PHONE_RAW,
        'brand_email': Config.RESTAURANT_EMAIL,
        'brand_hours': Config.RESTAURANT_HOURS,
        'db_status': db.get_db_status()
    }

# ----------------- Admin Auth Decorator -----------------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            if request.is_json:
                return jsonify({'error': 'Unauthorized. Admin login required.'}), 401
            return redirect(url_for('admin_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# ----------------- Customer Frontend Routes -----------------
@app.route('/')
def home():
    all_items = db.get_all_food()
    popular_items = db.get_popular_food()
    featured_items = all_items[:8]
    categories = ['Burgers', 'Pizza', 'Biryani', 'BBQ', 'Fast Food', 'Drinks']
    return render_template(
        'index.html',
        popular_items=popular_items,
        featured_items=featured_items,
        categories=categories,
        reviews=db.get_recent_reviews()
    )

@app.route('/menu')
def menu():
    category = request.args.get('category', 'All')
    search = request.args.get('search', '').strip()
    food_items = db.get_all_food(category=category, search=search)
    categories = ['All', 'Burgers', 'Pizza', 'Biryani', 'BBQ', 'Fast Food', 'Drinks']
    return render_template(
        'menu.html',
        food_items=food_items,
        categories=categories,
        selected_category=category,
        search_query=search
    )

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/orders')
def orders_page():
    search = request.args.get('search', '').strip()
    orders = []
    if search:
        grouped_orders = {}
        for item in db.get_customer_orders(search):
            key = item.get('order_code') or f"legacy-{item['order_id']}"
            if key not in grouped_orders:
                grouped_orders[key] = {
                    'order_code': item.get('order_code'),
                    'order_id': item['order_id'],
                    'customer_name': item.get('customer_name'),
                    'customer_phone': item.get('customer_phone'),
                    'delivery_address': item.get('delivery_address'),
                    'order_status': item.get('order_status'),
                    'payment_method': item.get('payment_method'),
                    'order_date': item.get('order_date'),
                    'order_notes': item.get('order_notes'),
                    'items': [],
                    'subtotal': 0,
                    'delivery_fee': 0
                }
            grouped = grouped_orders[key]
            grouped['items'].append(item)
            grouped['subtotal'] += int(item.get('total_price') or 0)
            grouped['delivery_fee'] += int(item.get('delivery_fee') or 0)
        orders = list(grouped_orders.values())
        for order in orders:
            order['grand_total'] = order['subtotal'] + order['delivery_fee']
    return render_template('orders.html', orders=orders, search_query=search)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/contact', methods=['POST'])
def submit_contact():
    customer_name = request.form.get('customer_name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    message = request.form.get('message', '').strip()

    if not customer_name or len(customer_name) > 100:
        flash('Please enter your name (up to 100 characters).', 'danger')
    elif not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email) or len(email) > 254:
        flash('Please enter a valid email address.', 'danger')
    elif not phone or len(phone) > 50:
        flash('Please enter a valid phone number.', 'danger')
    elif not message or len(message) < 10 or len(message) > 5000:
        flash('Your message must be between 10 and 5,000 characters.', 'danger')
    else:
        try:
            db.save_contact_message(customer_name, email, phone, message)
            flash('Thank you. Your message has been received.', 'success')
        except Exception:
            app.logger.exception('Failed to save contact message')
            flash('We could not save your message. Please try again later.', 'danger')

    return redirect(url_for('contact'))

# ----------------- Customer APIs -----------------
@app.route('/api/food', methods=['GET'])
def api_food():
    category = request.args.get('category')
    search = request.args.get('search')
    items = db.get_all_food(category=category, search=search)
    return jsonify({'success': True, 'items': items})

@app.route('/api/cart/validate', methods=['POST'])
def api_cart_validate():
    """Validates cart items against database prices and returns calculated totals."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'success': False, 'message': 'Invalid cart request.'}), 400
    items = data.get('items', [])
    if not isinstance(items, list) or len(items) > 50:
        return jsonify({'success': False, 'message': 'Cart must contain up to 50 valid items.'}), 400
    validated_items = []
    subtotal = 0

    for item in items:
        if not isinstance(item, dict):
            return jsonify({'success': False, 'message': 'Invalid cart item.'}), 400
        food_id = item.get('id')
        qty = item.get('quantity', 1)
        if isinstance(food_id, bool) or not isinstance(food_id, int):
            return jsonify({'success': False, 'message': 'Invalid food item ID.'}), 400
        if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1 or qty > 99:
            return jsonify({'success': False, 'message': 'Quantity must be between 1 and 99.'}), 400
        food = db.get_food_by_id(food_id)
        if not food or not food['is_available']:
            return jsonify({'success': False, 'message': 'A selected food item is unavailable.'}), 400
        item_total = food['price'] * qty
        subtotal += item_total
        validated_items.append({
            'id': food['id'],
            'name': food['name'],
            'price': food['price'],
            'category': food['category'],
            'image_url': food['image_url'],
            'quantity': qty,
            'total': item_total
        })

    # Free delivery applies to orders above Rs. 1,500.
    delivery_fee = 0 if subtotal > 1500 else 100
    grand_total = subtotal + delivery_fee

    return jsonify({
        'success': True,
        'items': validated_items,
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'grand_total': grand_total
    })

@app.route('/api/order/place', methods=['POST'])
def api_order_place():
    """Receives order details and securely saves them into database."""
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'success': False, 'message': 'Invalid order request.'}), 400
        customer_name = (data.get('customer_name') or '').strip()
        customer_phone = (data.get('customer_phone') or '').strip()
        delivery_address = (data.get('delivery_address') or '').strip()
        payment_method = (data.get('payment_method') or 'Cash on Delivery').strip()
        order_notes = (data.get('order_notes') or '').strip()
        items = data.get('items', [])

        if not customer_name or len(customer_name) > 100:
            return jsonify({'success': False, 'message': 'Customer name is required.'}), 400
        if not customer_phone or len(customer_phone) < 7 or len(customer_phone) > 50:
            return jsonify({'success': False, 'message': 'Please provide a valid contact phone number.'}), 400
        if not delivery_address or len(delivery_address) < 4 or len(delivery_address) > 1000:
            return jsonify({'success': False, 'message': 'Please provide a complete delivery address.'}), 400
        if len(order_notes) > 1000:
            return jsonify({'success': False, 'message': 'Order notes must be 1,000 characters or fewer.'}), 400
        if payment_method not in {'Cash on Delivery', 'JazzCash', 'EasyPaisa'}:
            return jsonify({'success': False, 'message': 'Please select a supported payment method.'}), 400
        if not isinstance(items, list) or not items or len(items) > 50:
            return jsonify({'success': False, 'message': 'Your shopping cart is empty.'}), 400

        # Place order via database layer
        order_result = db.place_order(
            customer_name=customer_name,
            customer_phone=customer_phone,
            delivery_address=delivery_address,
            payment_method=payment_method,
            cart_items=items,
            order_notes=order_notes
        )

        return jsonify({
            'success': True,
            'message': 'Order placed successfully!',
            'order': order_result
        })
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception:
        app.logger.exception('Failed to place customer order')
        return jsonify({'success': False, 'message': 'Unable to place your order right now.'}), 500

@app.route('/api/reviews', methods=['POST'])
def api_submit_review():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'success': False, 'message': 'Invalid review request.'}), 400
    order_code = (data.get('order_code') or '').strip()
    customer_phone = (data.get('customer_phone') or '').strip()
    review_text = (data.get('review_text') or '').strip()
    rating = data.get('rating')

    if not order_code or len(order_code) > 50 or not customer_phone:
        return jsonify({'success': False, 'message': 'Order reference and phone number are required.'}), 400
    if isinstance(rating, bool) or not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({'success': False, 'message': 'Choose a rating from 1 to 5.'}), 400
    if len(review_text) < 10 or len(review_text) > 2000:
        return jsonify({'success': False, 'message': 'Your review must be between 10 and 2,000 characters.'}), 400

    try:
        db.add_customer_review(order_code, customer_phone, rating, review_text)
        return jsonify({'success': True, 'message': 'Thank you for sharing your review.'})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception:
        app.logger.exception('Failed to save customer review')
        return jsonify({'success': False, 'message': 'Unable to save your review right now.'}), 500

@app.route('/api/orders/<path:identifier>', methods=['GET'])
def api_get_order(identifier):
    orders = db.get_customer_orders(identifier.strip())
    return jsonify({'success': True, 'orders': orders})

# ----------------- Admin Authentication Routes -----------------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user = db.authenticate_admin(username, password)
        if user:
            session['admin_logged_in'] = True
            session['admin_username'] = user['username']
            session['admin_name'] = user.get('full_name', 'Administrator')
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/') and not next_page.startswith('//') and not urlparse(next_page).netloc:
                return redirect(next_page)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('You have been securely logged out.', 'info')
    return redirect(url_for('admin_login'))

# ----------------- Admin Dashboard & Operations -----------------
@app.route('/admin')
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    stats = db.get_sales_analytics()
    food_items = db.get_all_food(only_available=False)
    orders = db.get_orders(limit=150)
    db_status = db.get_db_status()
    return render_template(
        'admin/dashboard.html',
        stats=stats,
        food_items=food_items,
        food_categories=db.get_food_categories(),
        orders=orders,
        admin_name=session.get('admin_name', 'Restaurant Administrator'),
        db_status=db_status
    )

@app.route('/admin/api/stats', methods=['GET'])
@admin_required
def admin_api_stats():
    stats = db.get_sales_analytics()
    return jsonify({'success': True, 'stats': stats, 'db_status': db.get_db_status()})

@app.route('/admin/api/orders', methods=['GET'])
@admin_required
def admin_api_orders():
    search = request.args.get('search')
    status = request.args.get('status')
    orders = db.get_orders(search=search, status=status)
    return jsonify({'success': True, 'orders': orders})

@app.route('/admin/api/orders/<int:order_id>/status', methods=['POST'])
@admin_required
def admin_update_order_status(order_id):
    data = request.get_json() or {}
    new_status = data.get('status')
    try:
        success = db.update_order_status(order_id, new_status)
        return jsonify({'success': success, 'message': f'Status updated to {new_status}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/admin/api/orders/<int:order_id>', methods=['DELETE'])
@admin_required
def admin_delete_order(order_id):
    try:
        deletion = db.delete_order(order_id)
        if not deletion:
            return jsonify({'success': False, 'message': 'Order was not found.'}), 404
        return jsonify({
            'success': True,
            'message': 'Order deleted.',
            'order_code': deletion['order_code'],
            'order_id': deletion['order_id']
        })
    except Exception:
        app.logger.exception('Failed to delete order %s', order_id)
        return jsonify({'success': False, 'message': 'Unable to delete the order.'}), 500

@app.route('/admin/reports/orders.csv')
@admin_required
def admin_export_orders():
    orders = db.get_orders(limit=10000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Order ID', 'Order Reference', 'Customer', 'Phone', 'Food', 'Quantity',
                     'Item Total (Rs.)', 'Delivery Fee (Rs.)', 'Status', 'Payment Method', 'Order Date'])
    for order in orders:
        writer.writerow([
            order['order_id'],
            order.get('order_code') or f"ORD-{order['order_id']}",
            order.get('customer_name', ''),
            order.get('customer_phone', ''),
            order.get('food_name', ''),
            order.get('quantity', ''),
            order.get('total_price', ''),
            order.get('delivery_fee', 0),
            order.get('order_status', ''),
            order.get('payment_method', ''),
            order.get('order_date', '')
        ])
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=mashalkitchen-orders.csv'}
    )

@app.route('/admin/api/categories/rename', methods=['POST'])
@admin_required
def admin_rename_category():
    data = request.get_json(silent=True) or {}
    old_name = (data.get('old_name') or '').strip()
    new_name = (data.get('new_name') or '').strip()
    if not old_name or not new_name or len(new_name) > 50:
        return jsonify({'success': False, 'message': 'Enter a category name up to 50 characters.'}), 400
    try:
        updated = db.rename_food_category(old_name, new_name)
        if not updated:
            return jsonify({'success': False, 'message': 'Category was not found or no items were updated.'}), 404
        return jsonify({'success': True, 'message': 'Category updated for its food items.'})
    except Exception:
        app.logger.exception('Failed to rename food category')
        return jsonify({'success': False, 'message': 'Unable to rename the category.'}), 500

@app.route('/admin/api/food', methods=['POST'])
@admin_required
def admin_add_food():
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    price = data.get('price')
    category = (data.get('category') or 'Fast Food').strip()
    description = (data.get('description') or '').strip()
    image_url = (data.get('image_url') or '/static/images/food/burger.jpg').strip()

    if (not name or len(name) > 100 or isinstance(price, bool) or not isinstance(price, int)
            or price <= 0 or len(category) > 50 or len(description) > 2000
            or len(image_url) > 255):
        return jsonify({'success': False, 'message': 'Valid dish name and price are required.'}), 400

    try:
        new_id = db.add_food(name, price, category, description, image_url)
        return jsonify({'success': True, 'message': 'Food item added successfully!', 'id': new_id})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        app.logger.exception('Failed to add food item')
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/food/<int:food_id>', methods=['PUT'])
@admin_required
def admin_update_food(food_id):
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    price = data.get('price')
    category = (data.get('category') or 'Fast Food').strip()
    description = (data.get('description') or '').strip()
    image_url = (data.get('image_url') or '').strip()
    is_available = data.get('is_available', 1)

    if (not name or len(name) > 100 or isinstance(price, bool) or not isinstance(price, int)
            or price <= 0 or len(category) > 50 or len(description) > 2000
            or len(image_url) > 255 or is_available not in (0, 1, False, True)):
        return jsonify({'success': False, 'message': 'Valid dish name and price are required.'}), 400

    try:
        success = db.update_food(food_id, name, price, category, description, image_url, int(is_available))
        return jsonify({'success': success, 'message': 'Food item updated successfully!'})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        app.logger.exception('Failed to update food item')
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/food/<int:food_id>', methods=['DELETE'])
@admin_required
def admin_delete_food(food_id):
    try:
        success = db.delete_food(food_id)
        return jsonify({'success': success, 'message': 'Food item deleted successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/upload', methods=['POST'])
@admin_required
def admin_upload_image():
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'No image file uploaded.'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file.'}), 400

    allowed_exts = {'png', 'jpg', 'jpeg', 'webp'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed_exts:
        return jsonify({'success': False, 'message': 'Invalid file type. Only JPG, PNG, WEBP allowed.'}), 400

    filename = secure_filename(f"food_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    return jsonify({
        'success': True,
        'image_url': f"/static/images/food/{filename}",
        'message': 'Image uploaded successfully!'
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"MashalKitchen active on http://127.0.0.1:{port}")
    app.run(host='127.0.0.1', port=port, debug=False)
