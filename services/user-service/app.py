from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Counter
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'postgresql://podmart:podmart123@user-db:5432/userdb'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
metrics = PrometheusMetrics(app)
metrics.info('user_service_info', 'User Service Info', version='1.0.0')

registered_users_total = Counter('registered_users_total', 'Total registered users')
login_attempts_total = Counter('login_attempts_total', 'Total login attempts', ['status'])

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'user-service'})

@app.route('/users', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=generate_password_hash(data['password'])
    )
    db.session.add(user)
    db.session.commit()
    registered_users_total.inc()
    return jsonify(user.to_dict()), 201

@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    user = User.query.get_or_404(id)
    return jsonify(user.to_dict())

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and check_password_hash(user.password_hash, data['password']):
        login_attempts_total.labels(status='success').inc()
        return jsonify({'message': 'Login successful', 'user': user.to_dict()})
    login_attempts_total.labels(status='failed').inc()
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/users/count')
def count_users():
    count = User.query.count()
    return jsonify({'count': count})

def init_db():
    retries = 10
    while retries:
        try:
            with app.app_context():
                db.create_all()
            print("=== User DB tables created ===")
            break
        except Exception as e:
            retries -= 1
            print(f"=== DB not ready, retrying... {e} ===")
            time.sleep(3)

init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)