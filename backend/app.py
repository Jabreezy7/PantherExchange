# Import necessary tools from Flask framework
from flask import Flask, render_template, request, redirect, url_for, session as flask_session, flash
# Import models (like database tables)
from models import *
import os
from datetime import datetime

# Find the base folder of this file
BASEDIR = os.path.abspath(os.path.dirname(__file__))
# Create a Flask app
app = Flask(
    __name__,
    template_folder=os.path.join(BASEDIR, "templates"),  # Where HTML files are stored
)
# Secret key for session (needed for user login)
app.secret_key = "test"


# Home page route
@app.route("/")
def index():
    # Get the product category from the URL (if any)
    category = request.args.get("category")
    # Get products based on category. If no category, get all active products.
    if category:
        listings = session.query(Listing).filter_by(status="active", category=category).all()
    else:
        listings = session.query(Listing).filter_by(status="active").all()

    # Show the home page with products and login status
    return render_template("index.html", listings=listings, logged_in="user_id" in flask_session)


# User registration route (can get form or send form data)
@app.route("/register", methods=["GET", "POST"])
def register():
    # If user submits the registration form
    if request.method == "POST":
        # Get data from the form
        data = {
            "username": request.form.get("username"),
            "email": request.form.get("email"),
            "password": request.form.get("password"),
            "phone": request.form.get("phone")
        }
        # Check if all required fields are filled
        if not all([data["username"], data["email"], data["password"], data["phone"]]):
            return render_template("register.html", error="Please fill in all required fields")
        # Check if email is already used
        if session.query(Student).filter_by(pittEmail=data["email"]).first():
            return render_template("register.html", error="This email has been registered")
        try:
            # Create a new student
            new_student = Student(
                name=data["username"],
                pittEmail=data["email"],
                phoneNumber=data["phone"],
                password=data["password"]
            )
            # Save the new student to database
            session.add(new_student)
            session.commit()  # Save changes
            # Auto create buyer, seller and inbox for the new student
            new_student.register(session)
            # Go to login page with success message
            return redirect(url_for("login", success="Registration successful, please log in"))
        except Exception as e:
            # If error, undo the save
            session.rollback()
            return render_template("register.html", error=f"Registration failed: {str(e)}")
    # Show the registration form (if not submitting data)
    return render_template("register.html")


# User login route (can get form or send form data)
@app.route("/login", methods=["GET", "POST"])
def login():
    # If user submits login data
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        # Find the student with this email
        student = session.query(Student).filter_by(pittEmail=email).first()
        # If no student found
        if not student:
            return render_template("login.html", error="This email is not registered")
        # If password is wrong
        if not student.login(password):
            return render_template("login.html", error="Wrong password")

        # Save user info in session (for login state)
        flask_session["user_id"] = student.id
        flask_session["username"] = student.name
        # Every user can be both buyer and seller
        flask_session["has_buyer_role"] = True
        flask_session["has_seller_role"] = True
        # Go to home page after login
        return redirect(url_for("index"))
    # Get success message from URL (if any)
    success_msg = request.args.get("success")
    # Show login form
    return render_template("login.html", success=success_msg)

@app.route("/message")
def message():
    # 检查登录状态
    if "user_id" not in flask_session:
        return redirect(url_for("login", next="/message"))  # 登录后跳转回消息页

    user_id = flask_session["user_id"]
    student = session.query(Student).get(user_id)
    if not student:
        return redirect(url_for("index"))

    # 获取用户的所有消息
    messages = student.reportListing(session)
    return render_template(
        "message.html",
        messages=messages,
        username=flask_session.get("username")
    )

# Route for selling products (can get form or send form data)
@app.route("/sell", methods=["GET", "POST"])
def sell():
    # If user is not logged in, go to login page
    if "user_id" not in flask_session:
        return redirect(url_for("login"))
    # Get current user's ID
    user_id = flask_session["user_id"]
    # Get current user's info
    student = session.query(Student).get(user_id)
    if not student:
        return render_template("sell.html", error="User information does not exist")

    # If user submits product info
    if request.method == "POST":
        # Get and clean image links (split by comma)
        images = request.form.get("images", "").split(",")
        images = [img.strip() for img in images if img.strip()]
        # Product data from form
        data = {
            "title": request.form.get("title"),
            "description": request.form.get("description"),
            "price": request.form.get("price"),
            "category": request.form.get("category"),
            "address": request.form.get("address"),
            "images": images,
            "seller_name": student.name
        }
        # Create the product listing
        new_listing= student.seller.createListing(session=session, **data)
        if new_listing:
            # Go to the new product's page if success
            return redirect(url_for("listing_detail", listing_id=new_listing.id))
        else:
            # Show error if failed
            return render_template("sell.html",)
    # Show the sell form
    return render_template("sell.html")



# force listing_id be integer
@app.route("/listing/<int:listing_id>")
def listing_detail(listing_id):
    # Get the product by ID
    listing = session.query(Listing).get(listing_id)
    if not listing:
        return "Product does not exist", 404  # Error if product not found

    # Check user login state
    logged_in = "user_id" in flask_session
    user_id = flask_session.get("user_id")
    # Check if current user is the seller of this product
    is_seller = logged_in and (listing.seller_id == user_id)
    # Check if user saved this product
    is_saved = False

    # If user is logged in, check saved products
    if logged_in:
        student = session.query(Student).get(user_id)
        for item in student.savedListings:
            print(item.id," ",listing_id)
            if item.id==listing_id:
                is_saved=True
                break

    # Show product detail page with all info
    return render_template(
        "listing_detail.html",
        listing=listing,
        logged_in=logged_in,
        is_seller=is_seller,
        is_saved=is_saved
    )


# Route for buying a product
@app.route("/purchase/<listing_id>", methods=["POST"])
def purchase(listing_id):
    # If not logged in, go to login
    if "user_id" not in flask_session:
        return redirect(url_for("login"))
    user_id = flask_session["user_id"]
    student = session.query(Student).get(user_id)
    listing = session.query(Listing).get(listing_id)
    # Check if product can be bought
    if not listing or listing.status != "active":
        return render_template("listing_detail.html", listing=listing, error="Product cannot be purchased")

    # Try to purchase the product
    success = student.buyer.purchaseItem(listing, session=session)
    if success:
        # Show success page if purchase works
        return render_template("purchase_success.html", listing=listing)
    else:
        # Show error if purchase fails
        return render_template("listing_detail.html", listing=listing, error="failed")

# Route for saving a product (to favorites)
@app.route("/save/<listing_id>")
def save_listing(listing_id):
    # If not logged in, go to login
    if "user_id" not in flask_session:
        return redirect(url_for("login"))

    user_id = flask_session["user_id"]
    student = session.query(Student).get(user_id)
    listing = session.query(Listing).get(listing_id)

    if not listing:
        return redirect(url_for("index"))

    # Make sure the user has a buyer role (create if not)
    if not student.buyer:
        try:
            student.buyer = Buyer(id=user_id)
            session.commit()
            flask_session["has_buyer_role"] = True
        except Exception as e:
            session.rollback()
            return render_template("listing_detail.html", listing=listing, error=f"Failed to create buyer role: {str(e)}")

    # Save or unsave the product
    student.buyer.saveListing(listing, session=session)

    return redirect(url_for("listing_detail", listing_id=listing_id))


# Route for user's own products and saved products
@app.route("/my_listings")
def my_listings():
    # If not logged in, go to login
    if "user_id" not in flask_session:
        return redirect(url_for("login"))

    user_id = flask_session["user_id"]
    data = {
        "seller_listings": [],  # Products user is selling
        "saved_listings": [],   # Products user saved
        "bought_listings": [],  # Products user bought
    }

    student = session.query(Student).get(user_id)
    # Get products the user is selling (if they have seller role)
    if flask_session.get("has_seller_role"):
        data["seller_listings"] = session.query(Listing).filter_by(seller_id=user_id).all()

    # Get products the user saved (if they have buyer role)
    if flask_session.get("has_buyer_role"):
        for item in student.savedListings:
            if item.status=="active":
                data["saved_listings"].append(item);

    data["bought_listings"] = session.query(Listing).filter_by(buyer_id=user_id).all()

    # Show the page with user's products
    return render_template("my_listings.html", **data)


# Route for deleting a product listing
@app.route("/delete_listing/<listing_id>")
def delete_listing(listing_id):
    # Check if user is logged in and has seller role
    if "user_id" not in flask_session or not flask_session.get("has_seller_role"):
        return redirect(url_for("login"))

    user_id = flask_session["user_id"]
    seller = session.query(Seller).get(user_id)
    # Try to delete the product
    success= seller.deleteListing(listing_id, session=session)
    return redirect(url_for("my_listings"))

@app.route("/my_messages")
def my_messages():
    if "user_id" not in flask_session:
        return redirect(url_for("login"))
    # get login user
    user = session.query(Student).get(flask_session["user_id"])
    # get message
    messages = user.reportListing(session)
    # to frontend
    return render_template("my_messages.html", msg=messages)


# Route for logging out
@app.route("/logout")
def logout():
    # Clear all session data (end login state)
    flask_session.clear()
    return redirect(url_for("index"))  # Go to home page after logout

if __name__ == "__main__":
    app.run(debug=True, port=5000)