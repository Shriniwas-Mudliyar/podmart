from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Counter, Histogram
from datetime import datetime
import requests
import os
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'postgresql://podmart:podmart123@order-db:5432/orderdb'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
metrics = PrometheusMetrics(app)
metrics.info('order_service_info', 'Order Service Info', version='1.0.0')

orders_total = Counter('orders_total', 'Total number of orders placed')
order_value = Histogram('order_value_dollars', 'Order value in dollars',
                        buckets=[10, 50, 100, 500, 1000])

PRODUCT_SERVICE_URL = os.getenv('PRODUCT_SERVICE_URL', 'http://product-service:5001')

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'quantity': self.quantity,
            'total_price': self.total_price,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'order-service'})

@app.route('/orders', methods=['GET'])
def get_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return jsonify([o.to_dict() for o in orders])

@app.route('/orders/<int:id>', methods=['GET'])
def get_order(id):
    order = Order.query.get_or_404(id)
    return jsonify(order.to_dict())

@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    try:
        response = requests.get(
            f"{PRODUCT_SERVICE_URL}/products/{data['product_id']}",
            timeout=5
        )
        product = response.json()
    except Exception:
        return jsonify({'error': 'Product service unavailable'}), 503

    total = product['price'] * data['quantity']
    order = Order(
        product_id=product['id'],
        product_name=product['name'],
        quantity=data['quantity'],
        total_price=total,
        status='pending'
    )
    db.session.add(order)
    db.session.commit()
    orders_total.inc()
    order_value.observe(total)
    return jsonify(order.to_dict()), 201

@app.route('/orders/<int:id>/status', methods=['PUT'])
def update_status(id):
    order = Order.query.get_or_404(id)
    data = request.get_json()
    order.status = data['status']
    db.session.commit()
    return jsonify(order.to_dict())

@app.route('/orders/count')
def count_orders():
    count = Order.query.count()
    return jsonify({'count': count})

def init_db():
    retries = 10
    while retries:
        try:
            with app.app_context():
                db.create_all()
            print("=== Order DB tables created ===")
            break
        except Exception as e:
            retries -= 1
            print(f"=== DB not ready, retrying... {e} ===")
            time.sleep(3)

init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)