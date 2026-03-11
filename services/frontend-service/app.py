from flask import Flask, render_template, jsonify, request
import requests
import os

app = Flask(__name__)

PRODUCT_SERVICE_URL = os.getenv('PRODUCT_SERVICE_URL', 'http://product-service:5001')
ORDER_SERVICE_URL = os.getenv('ORDER_SERVICE_URL', 'http://order-service:5002')
USER_SERVICE_URL = os.getenv('USER_SERVICE_URL', 'http://user-service:5003')

def check_service(url):
    try:
        r = requests.get(f"{url}/health", timeout=3)
        return 'up' if r.status_code == 200 else 'down'
    except Exception:
        return 'down'

def get_count(url, endpoint):
    try:
        r = requests.get(f"{url}/{endpoint}/count", timeout=3)
        return r.json().get('count', 0)
    except Exception:
        return 0

@app.route('/')
def dashboard():
    services = {
        'product': check_service(PRODUCT_SERVICE_URL),
        'order': check_service(ORDER_SERVICE_URL),
        'user': check_service(USER_SERVICE_URL)
    }
    counts = {
        'products': get_count(PRODUCT_SERVICE_URL, 'products'),
        'orders': get_count(ORDER_SERVICE_URL, 'orders'),
        'users': get_count(USER_SERVICE_URL, 'users')
    }
    try:
        orders = requests.get(f"{ORDER_SERVICE_URL}/orders", timeout=3).json()
        recent_orders = orders[:5]
    except Exception:
        recent_orders = []

    return render_template('index.html',
                           services=services,
                           counts=counts,
                           recent_orders=recent_orders)

@app.route('/products')
def products():
    try:
        data = requests.get(f"{PRODUCT_SERVICE_URL}/products", timeout=3).json()
    except Exception:
        data = []
    return render_template('products.html', products=data)

@app.route('/orders')
def orders():
    try:
        orders = requests.get(f"{ORDER_SERVICE_URL}/orders", timeout=3).json()
        products = requests.get(f"{PRODUCT_SERVICE_URL}/products", timeout=3).json()
    except Exception:
        orders, products = [], []
    return render_template('orders.html', orders=orders, products=products)

@app.route('/users')
def users():
    return render_template('users.html')

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'frontend-service'})

# API proxy routes for frontend JS
@app.route('/api/products', methods=['GET'])
def api_get_products():
    r = requests.get(f"{PRODUCT_SERVICE_URL}/products", timeout=3)
    return jsonify(r.json())

@app.route('/api/products', methods=['POST'])
def api_create_product():
    r = requests.post(f"{PRODUCT_SERVICE_URL}/products", json=request.get_json(), timeout=3)
    return jsonify(r.json()), r.status_code

@app.route('/api/products/<int:id>', methods=['DELETE'])
def api_delete_product(id):
    r = requests.delete(f"{PRODUCT_SERVICE_URL}/products/{id}", timeout=3)
    return jsonify(r.json()), r.status_code

@app.route('/api/orders', methods=['GET'])
def api_get_orders():
    r = requests.get(f"{ORDER_SERVICE_URL}/orders", timeout=3)
    return jsonify(r.json())

@app.route('/api/orders', methods=['POST'])
def api_create_order():
    r = requests.post(f"{ORDER_SERVICE_URL}/orders", json=request.get_json(), timeout=3)
    return jsonify(r.json()), r.status_code

@app.route('/api/users', methods=['POST'])
def api_create_user():
    r = requests.post(f"{USER_SERVICE_URL}/users", json=request.get_json(), timeout=3)
    return jsonify(r.json()), r.status_code

@app.route('/api/login', methods=['POST'])
def api_login():
    r = requests.post(f"{USER_SERVICE_URL}/login", json=request.get_json(), timeout=3)
    return jsonify(r.json()), r.status_code


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
