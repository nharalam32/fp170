from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://chris:sirhc@172.16.181.82/fp170'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    ssn = db.Column(db.String(9), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Float, default=0)
    approved = db.Column(db.Boolean, default=False)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Notification('{self.message}', '{self.created_at}')"
    

@app.route('/')
def index():
    return render_template('base.html')

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
        
        # Check if the admin user exists in the database
        admin = Admin.query.filter_by(username=username, password=password).first()
        
        if admin:
            # Set the admin_id in the session upon successful login
            session['admin_id'] = admin.id
            return redirect(url_for('admin'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('admin_login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Extract registration form data
        username = request.form['username']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        ssn = request.form['ssn']
        address = request.form['address']
        phone_number = request.form['phone_number']
        password = request.form['password']
        
        # Create a new user with default approved status
        new_user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            ssn=ssn,
            address=address,
            phone_number=phone_number,
            password=password,
            approved=True  # Set default approved status to True
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        session['user_id'] = new_user.id
        
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

# Route for admin to accept users
@app.route('/admin/accept_user/<int:user_id>', methods=['POST'])
def accept_user(user_id):
    if 'admin_id' not in session or session['admin_id'] != 1:
        return redirect(url_for('admin_login'))

    user = User.query.get(user_id)
    if user:
        user.approved = True
        db.session.commit()
        flash(f'User {user.username} has been accepted.', 'success')
    else:
        flash('User not found.', 'error')
    
    return redirect(url_for('admin'))

# Route for admin notifications
@app.route('/admin/notifications')
def admin_notifications():
    if 'admin_id' not in session or session['admin_id'] != 1:
        return redirect(url_for('admin_login'))

    notifications = Notification.query.all()
    return render_template('admin_notifications.html', notifications=notifications)

@app.route('/send_money', methods=['POST'])
def send_money():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Get form data
    recipient_username = request.form['recipient_username']  # Assuming you have a form field for recipient's username
    amount = float(request.form['amount'])

    # Query the recipient based on the username
    recipient = User.query.filter_by(username=recipient_username).first()

    if not recipient:
        flash('Recipient account not found.', 'error')
        return redirect(url_for('dashboard'))

    sender_id = session['user_id']
    sender = User.query.get(sender_id)

    if sender.balance < amount:
        flash('Insufficient balance.', 'error')
        return redirect(url_for('dashboard'))

    sender.balance -= amount
    recipient.balance += amount

    # Add transaction record
    transaction = Transaction(sender_id=sender_id, recipient_id=recipient.id, amount=amount)
    db.session.add(transaction)
    db.session.commit()

    flash('Money sent successfully.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user:
            # If user exists, check if the account is approved
            if user.approved:
                # If approved, authenticate the password
                if user.password == password:
                    # If authenticated, store user ID in session
                    session['user_id'] = user.id
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid username or password', 'error')
            else:
                flash('Your account is still pending approval by the admin', 'warning')
        else:
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id
            flash('Account created successfully. Your account is pending approval by the admin', 'success')
            return redirect(url_for('dashboard'))
    
    return render_template('login.html')

# Route for user dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', user=user)

@app.route('/add_money', methods=['GET', 'POST'])
def add_money():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Extract amount from the form data
        amount = request.form.get('amount')

        # Check if amount is provided and is a valid number
        if amount is None or not amount.isdigit():
            flash('Invalid amount provided', 'error')
            return redirect(url_for('dashboard'))

        # Convert amount to float
        amount = float(amount)

        # Retrieve the user from the database
        user = User.query.get(session['user_id'])

        # Update the user's balance
        user.balance += amount

        # Save the updated user object back to the database
        db.session.commit()

        # Redirect to the dashboard
        return redirect(url_for('dashboard'))

    # Render the add_money.html template for GET request
    return render_template('add_money.html')

# Route to send money from user account


if __name__ == '__main__':
    app.run(debug=True)
