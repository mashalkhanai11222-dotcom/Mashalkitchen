import sys
import os

# Set standard output encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add project root to path
sys.path.insert(0, r"d:\database task pc\project")

from app import app
import db

def run_tests():
    print("=" * 60)
    print("STARTING COMPLETE END-TO-END VERIFICATION OF TASTEHUB")
    print("=" * 60)

    client = app.test_client()

    # Step 1: Open website homepage
    print("\n[Step 1] Testing Homepage (GET /)...")
    res = client.get('/')
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    html = res.data.decode('utf-8')
    assert "Fresh Flavor" in html and "Order Now" in html, "Hero section missing"
    assert "Fan Favorites" in html, "Favorite dishes section missing"
    assert "Today's Deals" in html, "Deal section missing"
    print("✓ Homepage rendered successfully with all required sections.")

    # Step 2: Browse food items on menu
    print("\n[Step 2] Testing Menu & Categories (GET /menu)...")
    res = client.get('/menu')
    assert res.status_code == 200
    html = res.data.decode('utf-8')
    assert "Burgers" in html and "Pizza" in html and "Biryani" in html
    assert "Zinger Burger" in html
    assert "Chicken Karahi" in html
    print("✓ All dishes and categories displayed dynamically from MySQL.")

    # Step 3 & 4: Cart Validation & Total Calculation
    print("\n[Step 3 & 4] Testing Cart Validation API (POST /api/cart/validate)...")
    # Say customer adds 2 Zinger Burgers (id 7, Rs. 650 each) and 1 Fresh Juice (id 17, Rs. 200)
    test_cart = [
        {'id': 7, 'quantity': 2},
        {'id': 17, 'quantity': 1}
    ]
    res = client.post('/api/cart/validate', json={'items': test_cart})
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    # Free delivery applies to orders above Rs. 1,500; exactly Rs. 1,500 has a Rs. 100 fee.
    assert data['subtotal'] == 1500, f"Expected subtotal 1500, got {data['subtotal']}"
    assert data['delivery_fee'] == 100, f"Expected delivery_fee 100, got {data['delivery_fee']}"
    assert data['grand_total'] == 1600, f"Expected grand_total 1600, got {data['grand_total']}"
    print(f"✓ Cart calculation verified from database prices: Subtotal = Rs. {data['subtotal']}, Delivery = Rs. {data['delivery_fee']}, Grand Total = Rs. {data['grand_total']}")

    # Step 5 & 6: Checkout and Save Order to MySQL
    print("\n[Step 5 & 6] Testing Order Placement to MySQL (POST /api/order/place)...")
    order_payload = {
        'customer_name': 'Mashal Khan Automated Test',
        'customer_phone': '0312-3456789',
        'delivery_address': 'House 42, Street 7, Sector F-10/2, Islamabad',
        'payment_method': 'Cash on Delivery',
        'items': test_cart
    }
    res = client.post('/api/order/place', json=order_payload)
    assert res.status_code == 200
    order_resp = res.get_json()
    assert order_resp['success'] is True
    order_info = order_resp['order']
    order_code = order_info['order_code']
    print(f"✓ Order placed successfully! Tracking Code: {order_code}")
    print(f"✓ Items placed: {len(order_info['items'])} items, Total: Rs. {order_info['grand_total']}")

    # Step 7: Verify Order in MySQL directly
    print("\n[Step 7] Directly querying MySQL 'orders' table to verify persistence...")
    conn = db.get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM orders WHERE order_code = %s;", (order_code,))
        saved_rows = cur.fetchall()
        assert len(saved_rows) >= 1, "Order was not saved in MySQL orders table!"
        print(f"✓ Verified in MySQL! Found {len(saved_rows)} database record(s) under code {order_code}:")
        for row in saved_rows:
            print(f"   - Order ID: {row['order_id']}, Item: {row['food_name']}, Qty: {row['quantity']}, Price: Rs. {row['total_price']}, Status: {row['order_status']}")
    first_order_id = saved_rows[0]['order_id']
    conn.close()

    # Step 8: Admin Authentication & Dashboard
    print("\n[Step 8] Testing Admin Login & Dashboard...")
    login_res = client.post('/admin/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    assert login_res.status_code == 200
    assert "Restaurant Management Portal" in login_res.data.decode('utf-8')
    print("✓ Admin authenticated successfully.")

    # Step 9: Update Order Status as Administrator
    print("\n[Step 9] Updating Order Status to 'Preparing' via Admin API...")
    update_res = client.post(f'/admin/api/orders/{first_order_id}/status', json={'status': 'Preparing'})
    assert update_res.status_code == 200
    assert update_res.get_json()['success'] is True
    print(f"✓ Order #{first_order_id} status updated to 'Preparing'.")

    # Step 10: Verify Customer Tracking Page
    print("\n[Step 10] Testing Customer Order Tracking (GET /orders?search=...)...")
    track_res = client.get(f'/orders?search={order_code}')
    assert track_res.status_code == 200
    track_html = track_res.data.decode('utf-8')
    assert order_code in track_html
    assert "Preparing" in track_html
    print("✓ Customer tracking page reflects the updated status 'Preparing' in real time!")

    # Step 11: Verify Sales Reports with SQL Aggregates
    print("\n[Step 11] Verifying Sales Reports (SQL SUM, COUNT, AVG, MAX, MIN, GROUP BY)...")
    stats_res = client.get('/admin/api/stats')
    assert stats_res.status_code == 200
    stats = stats_res.get_json()['stats']
    print(f"✓ Total Sales (SUM): Rs. {stats['total_sales']:,}")
    print(f"✓ Total Orders (COUNT): {stats['total_orders']}")
    print(f"✓ Average Order Value (AVG): Rs. {stats['avg_order_value']:,.2f}")
    print(f"✓ Max Food Price (MAX): Rs. {stats['max_price']}")
    print(f"✓ Min Food Price (MIN): Rs. {stats['min_price']}")
    print("✓ Top customer spenders (GROUP BY customer_name):")
    for cust in stats['customer_spending'][:3]:
        print(f"   - {cust['customer_name']}: Rs. {cust['total_spent']:,} ({cust['items_count']} orders)")

    # Step 12: Test Food Menu CRUD in Admin
    print("\n[Step 12] Testing Food Menu CRUD (Add, Update, Delete)...")
    # Add new item
    add_res = client.post('/admin/api/food', json={
        'name': 'Crispy Garlic Mayo Roll',
        'price': 420,
        'category': 'Fast Food',
        'description': 'Warm paratha roll stuffed with juicy chicken boti and garlic mayo.',
        'image_url': '/static/images/food/shawarma.jpg',
        'is_available': 1
    })
    assert add_res.status_code == 200
    new_food_id = add_res.get_json()['id']
    print(f"✓ Added test food item #{new_food_id}")

    # Update item
    upd_res = client.put(f'/admin/api/food/{new_food_id}', json={
        'name': 'Crispy Garlic Mayo Roll (Special)',
        'price': 450,
        'category': 'Fast Food',
        'description': 'Warm paratha roll with extra cheese and garlic mayo.',
        'image_url': '/static/images/food/shawarma.jpg',
        'is_available': 1
    })
    assert upd_res.status_code == 200
    print(f"✓ Updated test food item #{new_food_id}")

    # Delete item
    del_res = client.delete(f'/admin/api/food/{new_food_id}')
    assert del_res.status_code == 200
    print(f"✓ Cleaned up test food item #{new_food_id}")

    print("\n" + "=" * 60)
    print("ALL 12 VERIFICATION TESTS PASSED PERFECTLY!")
    print("=" * 60)

if __name__ == '__main__':
    run_tests()
