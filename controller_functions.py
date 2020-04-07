from flask import render_template, redirect, request, flash, session
from models import User, Post, Product, OrderItem, Order
from config import bcrypt, db, app, stripe_keys
from werkzeug.utils import secure_filename
import stripe
import os

import re
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')


def index():
    return render_template("index.html", users=User.query.all())

def register():
    errors = []

    if len(request.form['first_name']) < 2:
        errors.append("First name must be at least 2 characters")
        valid = False

    if len(request.form['last_name']) < 2:
        errors.append("Last name must be at least 2 characters")
        valid = False

    if not EMAIL_REGEX.match(request.form['email']):
        errors.append("Email must be valid")
        valid = False

    if len(request.form['password']) < 8:
        errors.append("Password must be at least 8 characters")
        valid = False

    user_check = User.query.filter_by(email=request.form["email"]).first()
    if user_check is not None:
        errors.append("Email is in use")
    
    if request.form['password'] != request.form['confirm']:
        errors.append("Passwords must match")
        valid = False

    if errors:
        for e in errors:
            flash(e)
    else:
        hashed = bcrypt.generate_password_hash(request.form["password"])
        new_user = None
        file = request.files['pic']
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        new_user = User(
            first_name = request.form["first_name"],
            last_name = request.form["last_name"],
            pic = filepath,
            email = request.form["email"],
            password = hashed
        )
        db.session.add(new_user)
        db.session.commit()
        session["user_id"] = new_user.id
        return redirect("/products")

    return redirect("/")

def login():
    errors = []

    user_attempt = User.query.filter_by(email=request.form["email"]).first()
    
    if not user_attempt:
        flash("Email/Password Incorrect")
        return redirect("/")

    if not bcrypt.check_password_hash(user_attempt.password, request.form["password"]):
        flash("Email/Password Incorrect")
        return redirect("/")

    session["user_id"] = user_attempt.id
    return redirect('/products')

def logout():
    session.clear()
    return redirect("/")

    if not "user_id" in session:
        return redirect("/")


def products():
    if "user_id" not in session:
        return redirect("/")
    return render_template(
        "products.html", 
        user=User.query.get(session["user_id"]), 
        products=Product.query.all(),
        active_cart=("active" if "curr_order" in session else "inactive")
    )

def orders():
    print(request.form)
    if "user_id" not in session:
        return redirect("/")
    order = None
    if not "curr_order" in session:
        order = Order(user_id=session["user_id"])
        db.session.add(order)
        db.session.commit()
        session["curr_order"] = order.id
    else:
        order = Order.query.get(session["curr_order"])

    for item in request.form:
        item_id = int(item.split("_")[0])
        new_item = OrderItem(product_id=item_id, order_id=order.id, qty=request.form[item])
        db.session.add(new_item)
        db.session.commit()

    return redirect("/orders/confirmation")

def confirmation():
    if "user_id" not in session or "curr_order" not in session:
        return redirect("/")
    
    order = Order.query.get(session["curr_order"])
    return render_template("confirm.html", order=order, key=stripe_keys["publishable_key"])
    
def place_transaction():
    user = User.query.get(session["user_id"])
    order = Order.query.get(session["curr_order"])
    customer = stripe.Customer.create(
        email = user.email,
        source = request.form['stripeToken']
    )
    stripe.Charge.create(
        customer = customer.id,
        amount = int(order.total_price() * 100),
        currency = 'usd',
        description = 'POSTerized Charge'
    )
    del session["curr_order"]
    
    flash("Thank you for your payment")
    return redirect("/products")

def cancel_order():
    order = Order.query.get(session["curr_order"])
    db.session.delete(order)
    db.session.commit()
    del session["curr_order"]
    return redirect("/products")
