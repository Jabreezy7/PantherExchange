import flask_sqlalchemy
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker, relationship
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy

from app import student_login

# global session
db=SQLAlchemy()
engine = create_engine("sqlite:///order.db")
Session = sessionmaker(bind=engine)
session = Session()

# ---------depend class/tables-------

# tags of goods
class Tag(db.Model):
    __tablename__ = "tag"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=True, default=" ")

# table between goods and tags
class ListingTag(db.Model):

    # on delete makes sure it automatically delete(even though i did it in deletelisitng method)
    __tablename__ = "listing_tag"
    listing_id = db.Column(
        db.Integer,
        db.ForeignKey("listing.id", ondelete="CASCADE"),
        primary_key=True
    )
    tag_id = db.Column(
        db.Integer,
        db.ForeignKey("tag.id", ondelete="CASCADE"),
        primary_key=True
    )

# orders,store transaction history
class Order(db.Model):

    __tablename__ = "order"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    buyer_id = db.Column(
        db.Integer,
        db.ForeignKey("student.id"),
        nullable=False
    )
    listing_id = db.Column(
        db.Integer,
        db.ForeignKey("listing.id"),
        nullable=False
    )
    seller_id = db.Column(
        db.Integer,
        db.ForeignKey("student.id"),
        nullable=False
    )
    # price, payment and order time
    price = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(256))
    order_time = db.Column(db.DateTime, default=db.DateTime.now, nullable=False)

# blocked user(not sure whether to implement it)
class BlockedUser(db.Model):
    __tablename__ = "blockedUsers"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # auto clean blocked users when it is removed
    student_id = db.Column(
        db.Integer,
        db.ForeignKey("student.id", ondelete="CASCADE"),
        nullable=False
    )
    blocked_id = db.Column(
        db.Integer,
        db.ForeignKey("student.id", ondelete="CASCADE"),
        nullable=False
    )
    block_time = db.Column(db.DateTime, default=db.DateTime.now, nullable=False)  
    # we can't block same user multiple times when it is blocked
    __table_args__ = (UniqueConstraint('student_id', 'blocked_id', name='_student_blocked_uc'),)


class Student(db.Model):
    __tablename__ = "student"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=True, default=" ")
    pittEmail = db.Column(db.String(100), unique=True, nullable=False)
    phoneNumber = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(256), nullable=False)
    paymentMethod = db.Column(db.String(256), nullable=True)
    paymentInformation = db.Column(db.Text, nullable=True)


class Inbox(db.Model):
    __tablename__ = "inbox"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id", ondelete="CASCADE"), nullable=False)  # 关联学生ID（每个学生一个收件箱）

class Message(db.Model):
    __tablename__ = "message"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("student.id", ondelete="CASCADE"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("student.id", ondelete="CASCADE"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timeStamp = db.Column(db.DateTime, default=db.DateTime.now)

class Listing(db.Model):
    __tablename__ = "listing"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    sellerName = db.Column(db.String(50), nullable=True, default=" ")
    address = db.Column(db.String(100))
    datePosted = db.Column(db.DateTime, default=db.DateTime.now)
    images = db.Column(db.Json, default=[])
    category = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20),default="Available")
    seller = db.Column(db.Integer, db.ForeignKey("student.id"))

class ListingCatalog(db.Model):
    __tablename__ = "listingCatalog"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    query = db.Column(db.String(100), nullable=False)

class SavedList(db.Model):
    __tablename__ = "savedList"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id", ondelete="CASCADE"))
    product_id = db.Column(db.Integer, db.ForeignKey("listing.id", ondelete="CASCADE"))
    # avoid save repeatedlly(maybe implemented previously)
    __table_args__ = (db.UniqueConstraint('student_id', 'product_id', name='_student_product_uc'),)

# ---------create all tables-----------------
db.Model.metadata.create_all(engine)
print("all tables have been generated")
