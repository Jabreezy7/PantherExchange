from flask import Flask, request, jsonify
from flask_cors import CORS
from models import *

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





@app.route("/api/student/register", methods=["POST"])
# studnet register
def student_register():

    # get data in json format
    json_data = request.get_json()

    # required text filed
    required = ["name", "pittEmail", "phoneNumber", "password"]

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
        return fail_response("login failed, email has already exist", 409)

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
    print(student.name)

    # get student email and the following password
    if not student or not student.login(json_data["name"],json_data["password"]):
        return fail_response("incorrect email or name or password ")

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

#     # missing any type of data, return missing required field
#     for field in required:
#         if field not in json_data or json_data[field]==None: return fail_response("missing required field")

#     student = session.query(Student).get(json_data["studentId"])
#     if not student:
#         return fail_response("student not exist")

#     # make sure title and price in valid range
#     title=json_data["title"]
#     if len(str(title))>100: return fail_response("too long title, please make it shorter")
#     price=json_data["price"]
#     if int(price)<0: return fail_response("price should be a positive number")

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

