from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from tempfile import mkdtemp
from datetime import datetime 
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'  # SQLite URI
db = SQLAlchemy(app)


class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    first_name = db.Column(db.String(30))
    last_name = db.Column(db.String(30))

class Product(db.Model):
    product_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255))
    carts = db.relationship('Cart', backref='product', lazy=True)

class Order(db.Model):
    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    order_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    status = db.Column(db.String(50))

class OrderItem(db.Model):
    order_item_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.order_id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False)
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)

class Cart(db.Model):
    cart_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False)
    quantity = db.Column(db.Integer)
    date_added = db.Column(db.DateTime, default=db.func.current_timestamp())

class Category(db.Model):
    category_id = db.Column(db.Integer,nullable=False )
    categoty_name = db.Column(db.String(50), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False)

    __table_args__ = (
        db.PrimaryKeyConstraint('category_id', 'product_id'),
    )

    
#not needed ig?
class Review(db.Model):
    review_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False)
    rating = db.Column(db.Integer)
    comment = db.Column(db.Text)
    date = db.Column(db.DateTime, default=db.func.current_timestamp())

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

Session(app)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    user_id = session.get('user_id')
    if user_id :
        sample_user = User.query.filter_by(user_id=user_id).first()
        return render_template('index.html', username=sample_user.username)

    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # You should perform actual authentication here
        # For testing purposes, let's check against a sample user
        sample_user = User.query.filter_by(username=username, password_hash=password).first()

        if sample_user:
            # Store the user's ID in the session
            session['user_id'] = sample_user.user_id
            print(sample_user.username)
            return render_template('index.html', username=sample_user.username)  # Redirect to the home page after successful login
        else:
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        first_name = request.form['first_name']
        last_name = request.form['last_name']

        # Create a new user
        new_user = User(username=username, password_hash=password, email=email, first_name=first_name, last_name=last_name)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/products/<int:category_id>', methods=['GET'])
def product_list(category_id):
    print(category_id)
    products = Product.query.all()
    return render_template('products.html', products=products)

@app.route('/product/<int:product_id>', methods=['GET'])
def show_product_details(product_id):
    product = Product.query.get(product_id)

    if product:
        # Pass product details to the template
        return render_template('product_details.html', product=product)
    else:
        return render_template('product_details.html')


@app.route('/add_to_cart/<int:product_id>')
@login_required
def add_to_cart(product_id):

    user_id = session.get('user_id')
    print(user_id)
    product_id=int(product_id)

    # Check if the product is already in the user's cart
    existing_cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()

    if existing_cart_item:
        existing_cart_item.quantity += 1
    else:
        new_cart_item = Cart(user_id=user_id, product_id=product_id, quantity=1)
        db.session.add(new_cart_item)

    db.session.commit()

    return redirect('/cart')

@app.route('/cart', methods=['GET'])
@login_required
def cart():
    # Retrieve the user ID from the session
    user_id = session.get('user_id')

   
    # Fetch the user's cart details from the database
    cart_items = Cart.query.filter_by(user_id=user_id).all()

    # Create a list of cart items with details
    cart_details = [
        {
            'cart_id': item.cart_id,
            'product_id': item.product_id,
            'quantity': item.quantity,
            'date_added': item.date_added.strftime('%Y-%m-%d %H:%M:%S'),
            'product_details': {
                'name': item.product.name,
                'price': item.product.price,
                'image_url':item.product.image_url
            }
        }
        for item in cart_items
    ]

    # Calculate the total price of items in the cart
    total_price = sum(item['product_details']['price'] * item['quantity'] for item in cart_details)

    # Render the carts.html template with cart details
    return render_template('cart.html', cart_items=cart_details, total_price=total_price)

    

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
