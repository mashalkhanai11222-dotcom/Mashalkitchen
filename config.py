import os

def load_env_file(filepath):
    if not os.path.exists(filepath):
        return
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass

env_path = os.path.join(os.path.dirname(__file__), '.env')
load_env_file(env_path)

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or os.urandom(32)
    DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'khanrana')
    DB_NAME = os.getenv('DB_NAME', 'food_order')
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'images', 'food')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload

    # Restaurant Brand & Contact Metadata
    RESTAURANT_NAME = 'MashalKitchen'
    RESTAURANT_ADDRESS = 'Main Bazar, Chota Lahore, Swabi, Khyber Pakhtunkhwa, Pakistan'
    RESTAURANT_CITY = 'Chota Lahore, Swabi'
    RESTAURANT_PHONE = '+92 312 3456789'
    RESTAURANT_PHONE_RAW = '03123456789'
    RESTAURANT_EMAIL = 'orders@mashalkitchen.com'
    RESTAURANT_HOURS = 'Monday – Sunday, 11:00 AM – 01:00 AM'
