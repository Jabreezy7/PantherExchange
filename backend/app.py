from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import text
from datetime import datetime

# import db and models
from models import db, Student, Listing, ListingCatalog, Inbox, Message, Tag, ListingTag, SavedList, Order

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///order.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# initialize db and create tables inside app context
db.init_app(app)
with app.app_context():
    db.create_all()

CORS(app)

# (Optional) Keep the small in-memory listing list only if you still need it for compatibility.
# Here we will implement DB-backed listing creation; remove in-memory if you don't need it.
listings = []
listing_id_counter = 1

# if success return data and message
def success_response(data=None, msg="operate successfully"):
    return jsonify({"success": True, "data": data or [], "msg": msg}), 200

# otherwise return msg
def fail_response(msg="operate failed", code=400):
    return jsonify({"success": False, "msg": msg}), code

# ---------------------------
# Core implementations moved to app.py (no methods in models)
# These functions implement the previous behavior/logic.
# ---------------------------

# check the validity of descriptions
def create_listing_core(student_id, title, description, price, address, category="Books", status="Available"):
    try:
        if len(str(title)) > 100:
            return None
        if float(price) < 0:
            return None
        student = Student.query.get(student_id)
        if not student:
            return None
        new_listing = Listing(
            title=title,
            description=description,
            price=price,
            sellerName=student.name,
            seller=student.id,
            address=address,
            category=category,
            status=status,
            datePosted=datetime.utcnow()
        )
        db.session.add(new_listing)
        db.session.commit()
        return new_listing.id
    except:
        db.session.rollback()
        # show error info
        app.logger.exception("create_listing_core failed")
        return None

# remove those related products
def delete_listing_core(student_id, listing_id):
    try:
        exists = db.session.execute(
            text("SELECT 1 FROM listing WHERE id = :list_id AND seller = :seller_id"),
            {"list_id": listing_id, "seller_id": student_id}
        ).scalar()
        if not exists:
            return False
        db.session.execute(text("DELETE FROM listing WHERE id = :list_id"), {"list_id": listing_id})
        db.session.execute(text("DELETE FROM savedList WHERE product_id = :list_id"), {"list_id": listing_id})
        db.session.execute(text("DELETE FROM listing_tag WHERE listing_id = :list_id"), {"list_id": listing_id})
        db.session.commit()
        return True
    except:
        db.session.rollback()
        # shows error info
        app.logger.exception("delete_listing_core failed")
        return False

# select tags
def tag_listing_core(student_id, listing_id, tags):
    try:
        # verify ownership
        listing_exists = db.session.execute(
            text("SELECT 1 FROM listing WHERE id = :list_id AND seller = :seller_id"),
            {"list_id": listing_id, "seller_id": student_id}
        ).scalar()
        if not listing_exists:
            return False

        # delete existing tags
        db.session.execute(text("DELETE FROM listing_tag WHERE listing_id = :list_id"), {"list_id": listing_id})
        db.session.flush()

        for tag_name in tags:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
                db.session.flush()  # get tag.id

            assoc_exists = db.session.execute(
                text("SELECT 1 FROM listing_tag WHERE listing_id = :l AND tag_id = :t"),
                {"l": listing_id, "t": tag.id}
            ).scalar()
            if not assoc_exists:
                db.session.execute(text("INSERT INTO listing_tag (listing_id, tag_id) VALUES (:l, :t)"),
                                   {"l": listing_id, "t": tag.id})

        db.session.commit()
        return True
    except:
        db.session.rollback()
        app.logger.exception("tag_listing_core failed")
        return False

# saved products
def save_listing_core(student_id, product_id):
    try:
        product_exists = db.session.execute(
            text("SELECT 1 FROM listing WHERE id = :prod_id AND seller != :student_id"),
            {"prod_id": product_id, "student_id": student_id}
        ).scalar()
        if not product_exists:
            return False

        exists = db.session.execute(
            text("SELECT 1 FROM savedList WHERE student_id = :stu_id AND product_id = :prod_id"),
            {"stu_id": student_id, "prod_id": product_id}
        ).scalar()
        if exists:
            return False

        saved = SavedList(student_id=student_id, product_id=product_id)
        db.session.add(saved)
        db.session.commit()
        return True
    except:
        db.session.rollback()
        app.logger.exception("save_listing_core failed")
        return False

# mark items that are pruchased
def purchase_item_core(student_id, listing_id, payment_method=None):
    try:
        listing = db.session.execute(
            text("SELECT * FROM listing WHERE id = :list_id AND status = 'Available'"),
            {"list_id": listing_id}
        ).mappings().first()
        if not listing:
            return False

        if listing["seller"] == student_id:
            return False

        order = Order(
            buyer_id=student_id,
            listing_id=listing_id,
            seller_id=listing["seller"],
            price=listing["price"],
            payment_method=payment_method
        )
        db.session.add(order)
        db.session.execute(text("UPDATE listing SET status = 'Sold' WHERE id = :list_id"), {"list_id": listing_id})
        db.session.execute(text("DELETE FROM savedList WHERE product_id = :list_id"), {"list_id": listing_id})
        db.session.commit()
        return True
    except:
        db.session.rollback()
        app.logger.exception("purchase_item_core failed")
        return False

# return savedlistings
def report_listing_core(student_id):
    try:
        res = db.session.execute(text("SELECT * FROM savedList WHERE student_id = :id"), {"id": student_id})
        return [dict(row) for row in res.mappings()]
    except:
        app.logger.exception("report_listing_core failed")
        return []

# send message to seller from buyer
def send_message_core(receiver_id, sender_id, content):
    try:
        # .scalar() means returns the value on first row and column
        sender_exists = db.session.execute(text("SELECT 1 FROM student WHERE id = :sender_id"), {"sender_id": sender_id}).scalar()
        receiver_exists = db.session.execute(text("SELECT 1 FROM student WHERE id = :receiver_id"), {"receiver_id": receiver_id}).scalar()
        if not sender_exists or not receiver_exists:
            return None
        msg = Message(sender_id=sender_id, receiver_id=receiver_id, content=content, timeStamp=datetime.utcnow())
        db.session.add(msg)
        db.session.commit()
        return msg.id
    except:
        db.session.rollback()
        app.logger.exception("send_message_core failed")
        return None

# search all the possible items
def search_listings_by_keyword(keyword):
    sql = text("""
        SELECT * FROM listing 
        WHERE title LIKE :kewords OR description LIKE :keywords
        ORDER BY datePosted DESC
    """)
    res = db.session.execute(sql, {"keywords": f"%{keyword}%"})
    return [dict(row) for row in res.mappings()]

def search_listings_by_category(category):
    res = db.session.execute(text("SELECT * FROM listing WHERE category = :category ORDER BY datePosted DESC"), {"category": category})
    return [dict(row) for row in res.mappings()]

def get_seller_listings(seller_id):
    res = db.session.execute(text("SELECT * FROM listing WHERE seller = :id"), {"id": seller_id})
    return [dict(row) for row in res.mappings()]

def get_all_listings(category=None):
    if category and category != "All":
        return search_listings_by_category(category)
    res = db.session.execute(text("SELECT * FROM listing"))
    return [dict(row) for row in res.mappings()]

# ---------------------------
# Routes (call the app.py implementations above)
# ---------------------------

@app.route("/api/student/register", methods=["POST"])
def student_register():
    json_data = request.get_json()
    required = ["pittEmail", "phoneNumber", "password"]
    for field in required:
        if field not in json_data or json_data[field] is None:
            return fail_response("missing required field")

    pitt_email = str(json_data["pittEmail"]).strip().lower()
    if not pitt_email.endswith("@pitt.edu") or len(pitt_email) <= 9 or len(pitt_email) > 14:
        return fail_response("invalid email")
    try:
        student = Student(
            name=json_data["name"],
            pittEmail=pitt_email,
            phoneNumber=json_data["phoneNumber"],
            password=json_data["password"],
            paymentMethod=json_data.get("paymentMethod"),
            paymentInformation=json_data.get("paymentInformation")
        )
        db.session.add(student)
        db.session.commit()
        return success_response({"studentId": student.id}, "registered successfully")
    except Exception as e:
        db.session.rollback()
        app.logger.exception("student_register failed")
        return fail_response("register failed, email has already exist", 409)

@app.route("/api/student/login", methods=["POST"])
def student_login_route():
    json_data = request.get_json()
    if not json_data.get("pittEmail") or not json_data.get("password"):
        return fail_response("email or password can't be null")

    student = Student.query.filter_by(pittEmail=json_data["pittEmail"]).one_or_none()
    if not student or not json_data.get("password") == student.password:
        return fail_response("incorrect email or password")

    # ensure inbox exists (match original behavior)
    inbox = Inbox.query.filter_by(student_id=student.id).first()
    if not inbox:
        inbox = Inbox(student_id=student.id)
        db.session.add(inbox)
        db.session.commit()

    return success_response({
        "studentId": student.id,
        "name": student.name,
        "pittEmail": student.pittEmail
    }, "login successful")

@app.route("/api/listing", methods=["POST"])
def create_listing_route():
    json_data = request.get_json()
    required = ["studentId", "title", "description", "price", "address"]
    for field in required:
        if field not in json_data or json_data[field] is None:
            return fail_response("missing required field")

    listing_id = create_listing_core(
        json_data["studentId"],
        json_data["title"],
        json_data["description"],
        json_data["price"],
        json_data["address"],
        category=json_data.get("category", "Books"),
        status=json_data.get("status", "Available")
    )
    if listing_id:
        return success_response({"listingId": listing_id}, "goods create successfully")
    return fail_response("create listing failed")

@app.route("/api/listing/batch", methods=["POST"])
def batch_create_listing_route():
    json_data = request.get_json()
    if not isinstance(json_data, list) or len(json_data) == 0:
        return fail_response("please pass data in list format")

    created_ids = []
    for item in json_data:
        required = ["studentId", "title", "description", "price", "address"]
        for field in required:
            if field not in item or item[field] is None:
                return fail_response("missing required field")

        listing_id = create_listing_core(
            item["studentId"],
            item["title"],
            item["description"],
            item["price"],
            item["address"],
            category=item.get("category", "Books")
        )
        created_ids.append(listing_id)
    return success_response({"createdIds": created_ids, "count": len(created_ids)}, "created in batch successfully")

@app.route("/api/listing/<int:listing_id>", methods=["DELETE"])
def delete_listing_route(listing_id):
    json_data = request.get_json()
    student_id = json_data.get("studentId")
    if not student_id:
        return fail_response("no student id")

    success = delete_listing_core(student_id, listing_id)
    return success_response("delete successfully") if success else fail_response("delete failed")

@app.route("/api/listing/tag", methods=["POST"])
def tag_listing_route():
    json_data = request.get_json()
    required = ["studentId", "listingId", "tags"]
    for field in required:
        if field not in json_data or json_data[field] is None:
            return fail_response("missing required field")

    success = tag_listing_core(json_data["studentId"], json_data["listingId"], json_data["tags"])
    return success_response("sucessfully make tags") if success else fail_response("failed to make tags")

@app.route("/api/listing", methods=["GET"])
def get_listings_route():
    try:
        category = request.args.get("category")
        result = get_all_listings(category)
        return success_response({"listings": result, "count": len(result)}, "search successfully")
    except Exception as e:
        app.logger.exception("get_listings_route failed")
        return fail_response("Something aint right")

@app.route("/api/listing/<int:studentId>", methods=["GET"])
def get_listing_studentId(studentId):
    try:
        listings_data = db.session.execute(text("SELECT * FROM listing WHERE seller != :id"), {"id": studentId})
        results = [dict(row) for row in listings_data.mappings()]
        return success_response({"listings": results, "count": len(results)}, "search successfully")
    except Exception as e:
        app.logger.exception("get_listing_studentId failed")
        return fail_response("some errors here")

@app.route("/api/listing/search_key/<keyword>", methods=["GET"])
def search_by_keyword_route(keyword):
    if not keyword:
        return fail_response("lack of keyword")
    results = search_listings_by_keyword(keyword)
    return success_response({"listings": results, "count": len(results)})

@app.route("/api/listing/search_cate/<category>", methods=["GET"])
def search_by_category_route(category):
    if not category:
        return fail_response("lack of category")
    results = search_listings_by_category(category)
    return success_response({"listings": results, "count": len(results)})

@app.route("/api/listing/save", methods=["POST"])
def save_listing_route():
    json_data = request.get_json()
    required = ["studentId", "listingId"]
    for field in required:
        if field not in json_data or json_data[field] is None:
            return fail_response("missing required field")

    success = save_listing_core(json_data["studentId"], json_data["listingId"])
    return success_response("sucessfully saved") if success else fail_response("saved failed")

@app.route("/api/listing/purchase", methods=["POST"])
def purchase_listing_route():
    json_data = request.get_json()
    required = ["studentId", "listingId"]
    for field in required:
        if field not in json_data or json_data[field] is None:
            return fail_response("missing required field")

    success = purchase_item_core(json_data["studentId"], json_data["listingId"], payment_method=json_data.get("paymentMethod"))
    return success_response("successfully buy it ") if success else fail_response("product doesn't exist/sold out/not your product")

@app.route("/api/student/saved-listings/<student_id>", methods=["GET"])
def get_saved_listings(student_id):
    try:
        saved_listings = report_listing_core(student_id)
        return success_response({"savedListings": saved_listings, "count": len(saved_listings)}, "successfully find saving list")
    except Exception as e:
        app.logger.exception("get_saved_listings failed")
        return fail_response("failed to get saved listings")

@app.route("/api/message/send", methods=["POST"])
def send_message_route():
    json_data = request.get_json()
    required = ["senderId", "receiverId", "content"]
    for field in required:
        if field not in json_data or json_data[field] is None:
            return fail_response("missing required field")

    # ensure receiver has an inbox (original behavior)
    inbox = Inbox.query.filter_by(student_id=json_data["receiverId"]).first()
    if not inbox:
        inbox = Inbox(student_id=json_data["receiverId"])
        db.session.add(inbox)
        db.session.commit()

    msg_id = send_message_core(json_data["receiverId"], json_data["senderId"], json_data["content"])
    return success_response({"messageId": msg_id}, "message send successfully") if msg_id else fail_response("message send failed")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
