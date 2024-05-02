from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Pennsylvania2004!@localhost/fp170'
db = SQLAlchemy(app)

# Define User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    ssn = db.Column(db.String(9), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    account_number = db.Column(db.String(12), unique=True)
    balance = db.Column(db.Float, default=0)
    approved = db.Column(db.Boolean, default=False)

# Define Transaction model
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))

@app.route('/')
def index():
    return render_template('base.html')

# Admin route to view and approve user accounts
@app.route('/admin')
def admin():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    if session['admin_id'] != 1:  # Assuming admin ID is 1
        return redirect(url_for('admin_login'))
    users = User.query.filter_by(approved=False).all()
    return render_template('admin.html', users=users)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Validate admin credentials
        admin = User.query.filter_by(username=username, password=password, id=1).first()
        if admin:
            session['admin_id'] = admin.id
            return redirect(url_for('admin'))
        else:
            return render_template('admin_login.html', error='Invalid username or password')
    return render_template('admin_login.html')

# Route for user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Extract user data from form
        # Create a new user object and add it to the database
        # Generate a unique account number
        # Redirect to login page with a success message
        pass
    return render_template('register.html')

# Route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Validate user credentials
        # If valid, store user ID in session and redirect to user homepage
        pass
    return render_template('login.html')

# Route for user homepage
@app.route('/homepage')
def homepage():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    return render_template('homepage.html', user=user)

# Route for adding money to the account
@app.route('/add_money', methods=['POST'])
def add_money():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # Process payment information and update user balance
    return redirect(url_for('homepage'))

# Route for sending money to another user
@app.route('/send_money', methods=['POST'])
def send_money():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # Process transaction information and update sender and recipient balances
    return redirect(url_for('homepage'))

# Route for viewing bank statements
@app.route('/bank_statement')
def bank_statement():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # Retrieve transaction history for the user
    return render_template('bank_statement.html')

if __name__ == '__main__':
    app.run(debug=True)
