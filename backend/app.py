from flask import Flask, request, jsonify
from flask_cors import CORS
from models import *
from sqlalchemy import text
from datetime import datetime

app = Flask(__name__)
# work on different URL
CORS(app)

listings = []
listing_id_counter = 1

# commonly used response jsonfy result

# default as non-data and operation succesfully, with 200 as operate sucessful
def success_response(data=None, msg="operate successfully"):
    return jsonify({"success": True, "data": data or [], "msg": msg}), 200

# failed due to server errors, but it depends on several situations
def fail_response(msg="operate failed", code=400):
    return jsonify({"success": False, "msg": msg}), code


# -------------------------
# Implementations of methods that used to live in models.py
# These implementations use the session and model classes imported from models.py
# and are attached to the classes so existing route code can keep calling them.
# -------------------------

# Student.login
def _student_login(self, password):
    try:
        res = password == self.password
        print("Res is:", res)
        if res:
            exist = session.query(Inbox).filter_by(student_id=self.id).first()
            if not exist:
                new_inbox = Inbox(student_id=self.id)
                session.add(new_inbox)
                session.commit()
        return res
    except Exception as e:
        session.rollback()
        print("error in login:", e)
        return False

Student.login = _student_login


# Student.reportListing -> return saved listings (rows from savedList)
def _student_reportListing(self):
    try:
        sql = text("SELECT * FROM savedList WHERE student_id = :id")
        res = session.execute(sql, {"id": self.id})
        return [dict(row) for row in res.mappings()]
    except Exception as e:
        print("reportListing error:", e)
        return []

Student.reportListing = _student_reportListing


# Student.deleteListing
def _student_deleteListing(self, listing_id):
    try:
        # make sure product exist and belongs to student
        listing = session.execute(
            text("SELECT 1 FROM listing WHERE id = :list_id AND seller = :seller_id"),
            {"list_id": listing_id, "seller_id": self.id}
        ).scalar()
        if not listing:
            print("goods doesn't exist or not belongs to you")
            return False

        # delete listing, savedList and listing_tag entries
        session.execute(
            text("DELETE FROM listing WHERE id = :list_id"),
            {"list_id": listing_id}
        )
        session.execute(
            text("DELETE FROM savedList WHERE product_id = :list_id"),
            {"list_id": listing_id}
        )
        session.execute(
            text("DELETE FROM listing_tag WHERE listing_id = :list_id"),
            {"list_id": listing_id}
        )
        session.commit()
        print("successfully delete product")
        return True
    except Exception as e:
        session.rollback()
        print("failed to delete product:", e)
        return False

Student.deleteListing = _student_deleteListing


# Student.tagListing
def _student_tagListing(self, listing_id, tags):
    try:
        # make sure product belongs to student
        listing_exists = session.execute(
            text("SELECT 1 FROM listing WHERE id = :list_id AND seller = :seller_id"),
            {"list_id": listing_id, "seller_id": self.id}
        ).scalar()
        if not listing_exists:
            print("goods doesn't exist or not belongs to you")
            return False

        # delete current relations
        session.execute(
            text("DELETE FROM listing_tag WHERE listing_id = :list_id"),
            {"list_id": listing_id}
        )
        session.flush()

        for tag_name in tags:
            # check whether tag exist
            tag = session.query(Tag).filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                session.add(tag)
                session.flush()  # ensure tag.id is populated

            # check whether relation exists
            listing_tag = session.query(ListingTag).filter_by(
                listing_id=listing_id, tag_id=tag.id
            ).first()
            if not listing_tag:
                listing_tag = ListingTag(listing_id=listing_id, tag_id=tag.id)
                session.add(listing_tag)

        session.commit()
        print("succesfully tag it")
        return True
    except Exception as e:
        session.rollback()
        print("failed to tag it:", e)
        return False

Student.tagListing = _student_tagListing


# Student.saveListing
def _student_saveListing(self, product_id):
    try:
        # verify product exist and not owned by student
        product_exists = session.execute(
            text("SELECT 1 FROM listing WHERE id = :prod_id and seller != :student_id"),
            {"prod_id": product_id, "student_id": self.id}
        ).scalar()
        if not product_exists:
            print("product doesn't exist")
            return False

        # verify not saved repeatedly
        exists = session.execute(
            text("SELECT 1 FROM savedList WHERE student_id = :stu_id AND product_id = :prod_id"),
            {"stu_id": self.id, "prod_id": product_id}
        ).scalar()
        if exists:
            print("you've already saved it")
            return False

        # insert into saved list
        session.execute(
            text("INSERT INTO savedList (student_id, product_id) VALUES (:stu_id, :prod_id)"),
            {"stu_id": self.id, "prod_id": product_id}
        )
        session.commit()
        print("successfully saved it")
        return True
    except Exception as e:
        session.rollback()
        print("failed to save it:", e)
        return False

Student.saveListing = _student_saveListing


# Student.purchaseItem
def _student_purchaseItem(self, listing_id, payment_method=None):
    try:
        # make sure listing exists and is Available
        listing = session.execute(
            text("SELECT * FROM listing WHERE id = :list_id AND status = 'Available'"),
            {"list_id": listing_id}
        ).mappings().first()
        if not listing:
            print("product doesn't exist or sold out ")
            return False

        # make sure buyer not seller
        if listing["seller"] == self.id:
            print("you can't buy your own product")
            return False

        # create order (ORM)
        order = Order(
            buyer_id=self.id,
            listing_id=listing_id,
            seller_id=listing["seller"],
            price=listing["price"],
            payment_method=payment_method or self.paymentMethod
        )
        session.add(order)

        # update product as sold out
        session.execute(
            text("UPDATE listing SET status = 'Sold' WHERE id = :list_id"),
            {"list_id": listing_id}
        )

        # delete from savedList
        session.execute(
            text("DELETE FROM savedList WHERE product_id = :list_id"),
            {"list_id": listing_id}
        )

        session.commit()
        print("successfully buy it")
        return True
    except Exception as e:
        session.rollback()
        print("failed to buy it :", e)
        return False

Student.purchaseItem = _student_purchaseItem


# Inbox.sendmessage
def _inbox_sendmessage(self, sender_id, content):
    try:
        # verify sender and receiver exists
        sender_exists = session.execute(
            text("SELECT 1 FROM student WHERE id = :sender_id"),
            {"sender_id": sender_id}
        ).scalar()
        receiver_exists = session.execute(
            text("SELECT 1 FROM student WHERE id = :receiver_id"),
            {"receiver_id": self.student_id}
        ).scalar()

        if not sender_exists:
            print("sender doesn't exist")
            return None
        if not receiver_exists:
            print("reciever doesn't exist")
            return None

        # create message via ORM to get id in sqlite safely
        msg = Message(sender_id=sender_id, receiver_id=self.student_id, content=content, timeStamp=datetime.now())
        session.add(msg)
        session.commit()
        print("successfully send message")
        return msg.id
    except Exception as e:
        session.rollback()
        print("failed send messages:", e)
        return None

Inbox.sendmessage = _inbox_sendmessage


# ListingCatalog.searchByKeyword
def _listingcatalog_searchByKeyword(self):
    sql = text("""
        SELECT * FROM listing 
        WHERE title LIKE :kw OR description LIKE :kw
        ORDER BY datePosted DESC
    """)
    try:
        res = session.execute(sql, {"kw": f"%{self.query}%"})
        return [dict(row) for row in res.mappings()]
    except Exception as e:
        print("searchByKeyword error:", e)
        return []

ListingCatalog.searchByKeyword = _listingcatalog_searchByKeyword


# ListingCatalog.searchByCategory
def _listingcatalog_searchByCategory(self):
    sql = text("""
        SELECT * FROM listing 
        WHERE category = :category
        ORDER BY datePosted DESC
    """)
    try:
        res = session.execute(sql, {"category": self.query})
        return [dict(row) for row in res.mappings()]
    except Exception as e:
        print("searchByCategory error:", e)
        return []

ListingCatalog.searchByCategory = _listingcatalog_searchByCategory


# -------------------------
# End of method implementations
# -------------------------


@app.route("/api/student/register", methods=["POST"])
# studnet register
def student_register():

    # get data in json format
    json_data = request.get_json()

    # required text filed
    required = [ "pittEmail", "phoneNumber", "password"]

    # missing any type of data, return missing required field
    for field in required:
        if field not in json_data or json_data[field]==None: return fail_response("missing required field")

    # make sure pitt student using it
    pitt_email=str(json_data["pittEmail"]).strip().lower()
    # make sure the email has valid length
    if not pitt_email.endswith("@pitt.edu") or len(pitt_email)<=9 or len(pitt_email)>14: return fail_response("invalid email")
    try:
        # auto-configuration json_data to corresponding text field
        student = Student(**json_data)
        # add them into database session
        session.add(student)
        # check data based on database
        session.commit()
        # successfully upload it
        return success_response({"studentId": student.id}, "registerd successfully ")
    except Exception as e:
        # failed, not add to database
        print(e)
        session.rollback()
        # email has already being used
        return fail_response("login failed, email has already exist", 400)

@app.route("/api/student/login", methods=["POST"])
# student login
def student_login():
    # get data
    json_data = request.get_json()
    print(json_data)
    if not json_data.get("pittEmail") or not json_data.get("password"):
        return fail_response("email or password can't be null")

    # sql search, students with unqiue pittEmail, so they are existing or not
    student = session.query(Student).filter_by(pittEmail=json_data["pittEmail"]).one_or_none()

    # get student email and the following password
    if not student or not student.login(json_data["password"]):
        return fail_response("incorrect email or password ")

    return success_response({
        "studentId": student.id,
        "name": student.name,
        "pittEmail": student.pittEmail
    }, "login successful")

# @app.route("/api/listing", methods=["POST"])
# # create goods
# def create_listing():
#     json_data = request.get_json()
#     required = ["studentId", "title", "description", "price", "address"]
#
#     # missing any type of data, return missing required field
#     for field in required:
#         if field not in json_data or json_data[field]==None: return fail_response("missing required field")
#
#     student = session.query(Student).get(json_data["studentId"])
#     if not student:
#         return fail_response("student not exist")
#
#     # make sure title and price in valid range
#     title=json_data["title"]
#     if len(str(title))>100: return fail_response("too long title, please make it shorter")
#     price=json_data["price"]
#     if int(price)<0: return fail_response("price should be a positive number")
#
#     # it includes all the required information, if not exist, within default values
#     try:
#         listing_id = student.createListing(
#             title=title,
#             description=json_data["description"],
#             price=json_data["price"],
#             address=json_data["address"],
#             category=json_data.get("category", "Books"),
#             status=json_data.get("status", "Available")
#         )
#         # succesfully created
#         return success_response({"listingId": listing_id}, "goods create suceesfully")
#     except:
#         # other failure
#         return fail_response("Other exceptions, please check the address/category/status field")

@app.route("/api/listing", methods=["POST"])
def create_listing():
    global listing_id_counter

    try:
        json_data = request.get_json()

        price = float(json_data["price"])

        new_listing = {
            "id": listing_id_counter,
            "title": json_data["title"],
            "description": json_data["description"],
            "price": f"${price}",
            "address": json_data["address"],
            "category": json_data["category"],
            "image": json_data.get("image")
        }

        listings.append(new_listing)
        listing_id_counter += 1

        return success_response({"listingId": new_listing["id"]}, "Finally")

    except:
        return fail_response("Something aint right")


@app.route("/api/listing/batch", methods=["POST"])
# created in batch(may not implemented)
def batch_create_listing():
    json_data = request.get_json()
    if not isinstance(json_data, list) or len(json_data) == 0:
        return fail_response("please pass data in list format")

    created_ids = []
    for item in json_data:
        required = ["studentId", "title", "description", "price", "address"]
        for field in required:
            if field not in json_data or json_data[field]==None: return fail_response("missing required field")

        student = session.query(Student).get(json_data["studentId"])
        if not student:
            return fail_response("student not exist")

        # make sure title and price in valid range
        title=json_data["title"]
        if len(str(title))>100: return fail_response("too long title, please make it shorter")
        price=json_data["price"]
        if int(price)<0: return fail_response("price should be a positive number")

        listing_id = student.createListing(
            title=title,
            description=item["description"],
            price=price,
            address=item["address"],
            category=item.get("category", "Books")
        )
        created_ids.append(listing_id)

    return success_response({
        "createdIds": created_ids,
        "count": len(created_ids)
    }, "created in bath successfully")

@app.route("/api/listing/<int:listing_id>", methods=["DELETE"])
# delete products
def delete_listing(listing_id):
    json_data = request.get_json()
    student_id = json_data.get("studentId")
    if not student_id:
        return fail_response("no student id")

    # get data based on student_id and product id
    student = session.query(Student).get(student_id)
    if not student:
        return fail_response("student doesn't exist")

    try:
        success = student.deleteListing(listing_id)
        return success_response("delete successfully") if success else fail_response("delete failed")

    # it could be either invalid student id or invalid product_id(but actually it shouldn't exist)
    except Exception as e:
        session.rollback()
        return fail_response(f"delete failed：{str(e)}")

@app.route("/api/listing/tag", methods=["POST"])
# make tags on product
def tag_listing():
    json_data = request.get_json()
    required = ["studentId", "listingId", "tags"]
    for field in required:
        if field not in json_data or json_data[field]==None: return fail_response("missing required field")

    student = session.query(Student).get(json_data["studentId"])
    if not student:
        return fail_response("student not exist")

    try:
        success = student.tagListing(json_data["listingId"], json_data["tags"])
        return success_response("sucessfully make tags") if success else fail_response("failed to make tags")
    except:
        session.rollback()
        return fail_response("failed to create tag")


# @app.route("/api/listing", methods=["GET"])
# # check for all data while no login
# def get_listings():
#     # select all of the data, no matter login or not
#     catalog = ListingCatalog(query="all")
#     listings = catalog.listings
#     return success_response({"listings": listings, "count": len(listings)},"search successfully")

@app.route("/api/listing", methods=["GET"])
def get_listings():
    try:
        category = request.args.get("category")

        if category and category != "All":
            filtered_listings = []
            for listing in listings:
                if listing["category"] == category:
                    filtered_listings.append(listing)

            return success_response(filtered_listings, "Got the listings")

        return success_response(listings, "Listings retrieved successfully")

    except:
        return fail_response("Something aint right")

@app.route("/api/listing/<int:studentId>", methods=["GET"])
# check for all data while login
def get_listing_studentId(studentId):
    sql=text("select * from listing where seller != :id")
    catalog = session.execute(sql,{"id":studentId})
    listings=[dict(row) for row in catalog.mappings()]
    try:
        session.commit()
    except:
        # probably not happened, only when id is invlaid
        fail_response("some errors here")
    return success_response({"listings": listings, "count": len(listings)},"search successfully")



@app.route("/api/listing/search_key/<keyword>", methods=["GET"])
# search by keyword
def search_by_keyword(keyword):
    if not keyword: return fail_response("lack of keyword")

    catalog = ListingCatalog(query=keyword)
    session.add(catalog)
    session.commit()
    results = catalog.searchByKeyword()
    return success_response({"listings": results, "count": len(results)})

@app.route("/api/listing/search_cate/<category>", methods=["GET"])
# search by category
def search_by_category(category):
    if not category: return fail_response("lack of category")

    catalog = ListingCatalog(query=category)
    session.add(catalog)
    session.commit()
    results = catalog.searchByCategory()
    return success_response({"listings": results, "count": len(results)})


@app.route("/api/listing/save", methods=["POST"])
# saved products
def save_listing():
    json_data = request.get_json()
    required = ["studentId", "listingId"]
    for field in required:
        if field not in json_data or json_data[field]==None: return fail_response("missing required field")

    student = session.query(Student).get(json_data["studentId"])
    if not student:
        return fail_response("student not exist")

    success = student.saveListing(json_data["listingId"])
    if success: return success_response("sucessfully saved")
    return fail_response("saved failed")

@app.route("/api/listing/purchase", methods=["POST"])
# buy product
def purchase_listing():
    json_data = request.get_json()
    required = ["studentId", "listingId"]
    for field in required:
        if field not in json_data or json_data[field]==None: return fail_response("missing required field")

    student = session.query(Student).get(json_data["studentId"])
    if not student:
        return fail_response("student not exist")

    success = student.purchaseItem(
        json_data["listingId"],
        payment_method=json_data.get("paymentMethod")
    )
    return success_response("successfully buy it ") if success else fail_response("product doesn't exist/sold out/not your product")

@app.route("/api/student/saved-listings/<student_id>", methods=["GET"])
def get_saved_listings(student_id):
    if not student_id:
        return fail_response("lack of student id")

    student = session.query(Student).get(student_id)
    if not student:
        return fail_response("student doesn't exist")

    # get saved listing
    saved_listings = student.reportListing()
    return success_response({
        "savedListings": saved_listings,
        "count": len(saved_listings)
    }, "successfully find saving list")



@app.route("/api/message/send", methods=["POST"])
def send_message():
    # send message
    json_data = request.get_json()
    required = ["senderId", "receiverId", "content"]
    for field in required:
        if field not in json_data or json_data[field]==None: return fail_response("missing required field")

    # reciever do exist since it is chosen from the goods list
    inbox = session.query(Inbox).filter_by(student_id=json_data["receiverId"]).first()
    if not inbox:
        print("")
        inbox = Inbox(student_id=json_data["receiverId"])
        session.add(inbox)
        session.commit()

    msg_id = inbox.sendmessage(json_data["senderId"], json_data["content"])
    return success_response({"messageId": msg_id}, "message send successfully") if msg_id else fail_response("message send failed")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
