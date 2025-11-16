from django.dispatch import receiver
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker, relationship
import sqlalchemy
from datetime import *

#generate class base for data
Base=sqlalchemy.orm.declarative_base()

# comes from student table
# blockedUsers record blocker and blocked person; savedListing record starred student
# and corresponding item
# primary key mark the starred situation only exist once
blocked_users = Table(
    'blockedUsers',
    # manage tables
    Base.metadata,
    Column('blocker_id', Integer, ForeignKey('student.id'), primary_key=True),  # 屏蔽者ID（关联Student表）
    Column('blocked_id', Integer, ForeignKey('student.id'), primary_key=True)   # 被屏蔽者ID（关联Student表）
)
saved_listings = Table(
    'savedListings',
    # manage tables
    Base.metadata,
    Column('student_id', Integer, ForeignKey('student.id'), primary_key=True),  # 用户ID（关联Student表）
    Column('listing_id', Integer, ForeignKey('listing.id'), primary_key=True)   # 列表ID（关联Listing表）
)

# message
inbox_messages = Table(
    'inbox_messages',  # 中间表名
    Base.metadata,
    Column('inbox_id', Integer, ForeignKey('inbox.id'), primary_key=True),  # 关联收件箱ID
    Column('message_id', Integer, ForeignKey('message.id'), primary_key=True)  # 关联消息ID
)

# catalog
catalog_listings = Table(
    'catalog_listings',
    Base.metadata,
    Column('catalog_id', Integer, ForeignKey('listing_catalog.id'), primary_key=True),
    Column('listing_id', Integer, ForeignKey('listing.id'), primary_key=True)
)

class Listing(Base):
    __tablename__ ="listing"
    # required data
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    # descriptions about
    description = Column(Text, nullable=False)
    # should be digit
    price = Column(Float, nullable=False)
    sellerName = Column(String(50), nullable=False)
    address = Column(String(100))
    datePosted = Column(DateTime, default=datetime.now())

    # not required
    # there can have mutiple images
    images = Column(JSON, default=[])
    category = Column(String(50), nullable=True)
    status = Column(String(20), default="active")

    # store buyer and seller information
    seller_id = Column(Integer, ForeignKey("sellers.id"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("student.id"), nullable=True)

class Student(Base):
    __tablename__ ="student"
    id=Column(Integer, primary_key=True, autoincrement=True)

    # required data
    name=Column(String(50),nullable=False)
    pittEmail = Column(String(100), unique=True, nullable=False)
    phoneNumber = Column(String(20), nullable=False)
    password = Column(String(256), nullable=False)


    # secondary shows which table is used
    # primaryjoin shows who is blocker; secondaryjoin shows who is blocked
    #   1. .c means visit the collection of column
    blockedUsers=relationship(
        'Student',
        secondary=blocked_users,
        primaryjoin=(blocked_users.c.blocker_id == id),
        secondaryjoin=(blocked_users.c.blocker_id == id)
    )
    savedListings=relationship(
        'Listing',
        secondary=saved_listings,
        primaryjoin=(saved_listings.c.student_id == id),
        secondaryjoin=(saved_listings.c.listing_id == Listing.id),
    )

    # build one to one relationship
    buyer = relationship("Buyer", backref="student", uselist=False)
    seller = relationship("Seller", backref="student", uselist=False)
    inbox = relationship("Inbox", backref="student", uselist=False)

#     not required
    paymentMethod = Column(String(256), nullable=True)
    paymentInformation = Column(String(256), nullable=True)

    def login(self,input_password):
        return self.password==input_password

    def register(self, session):
        # create buyer, seller and inbox
        if not self.buyer:
            self.buyer = Buyer(id=self.id)  # 关联当前学生的id
        if not self.seller:
            self.seller = Seller(id=self.id)  # 关联当前学生的id
        if not self.inbox:
            self.inbox = Inbox(student_id=self.id)  # 关联当前学生的id

        # store to dataset
        session.add_all([self.buyer, self.seller, self.inbox])
        session.commit()

    def reportListing(self,session):
        # check all message order by time
        received_messages = session.query(Message). \
            join(inbox_messages, Message.id == inbox_messages.c.message_id). \
            filter(inbox_messages.c.inbox_id == self.inbox.id). \
            order_by(Message.timeStamp). \
            all()

        # 3. formatting message
        message_list = []
        for msg in received_messages:
            # get sender information
            sender = session.query(Student).get(msg.sender_id)
            sender_name = sender.name if sender else " "

            message_list.append({
                "sender": sender_name,
                "email": sender.pittEmail,
                "phone": sender.phoneNumber,
                "content": msg.content,
                "timestamp": msg.timeStamp.strftime("%Y-%m-%d %H:%M:%S")
            })

        # 4. 返回整理后的消息列表
        return message_list

# extends from student
class Buyer(Base):
    __tablename__ = "buyers"

    id = Column(Integer, ForeignKey("student.id"), primary_key=True)

    def purchaseItem(self,listing,session):
        # check active
        if listing.status != "active":
            return False

        # not allowed to buy itself's item
        if listing.seller_id == self.id:
            return False

        # buy it(sold)
        listing.status = "sold"
        listing.buyer_id = self.id

        message_content=f"{self.student.name} bought your product {listing.title}"
        new_message=Message(sender_id=self.id,receiver_id=listing.seller_id,content=message_content)
        session.add(new_message)

        # add message to seller inbox
        seller = session.query(Student).get(listing.seller_id)
        if seller and seller.inbox:
            seller.inbox.messages.append(new_message)

        session.commit()
        return True

    def saveListing(self,listing,session):
        if listing in self.student.savedListings:
            # not save
            self.student.savedListings.remove(listing)
        else:
            # save
            self.student.savedListings.append(listing)
        session.commit()

class Seller(Base):
    __tablename__ = "sellers"

    id = Column(Integer, ForeignKey("student.id"), primary_key=True)

    def createListing(self, **kwargs):
        required_fields = ["title", "description", "price", "seller_name"]
        for field in required_fields:
            if field not in kwargs or not kwargs[field]:
                return None

        # 2. check price
        try:
            price = float(kwargs["price"])
            if price <= 0:
                return None
        except ValueError:
            return None

        # create goods
        try:
            new_listing = Listing(
                title=kwargs["title"],
                description=kwargs["description"],
                price=price,
                sellerName=kwargs["seller_name"],
                # can be null
                address=kwargs.get("address", ""),
                # auto set time
                datePosted=datetime.now(),
                images=kwargs.get("images", []),
                category=kwargs.get("category", ""),
                # initliaze as active
                status="active",
                seller_id=self.id
            )

            # store to dataset
            session.add(new_listing)
            session.commit()
            return new_listing

        except Exception as e:
            session.rollback()
            return None, f"pulish failed：{str(e)}"

    def deleteListing(self,listing_id,session):
        listing = session.query(Listing).get(listing_id)
        if not listing:
            return False

        # only delete personal item
        if listing.seller_id != self.id:
            return False

        # delete it
        session.delete(listing)
        session.commit()
        return True


    def tagListing(self):
        pass


class Message(Base):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sender_id= Column(Integer, ForeignKey("student.id"), nullable=False)
    receiver_id= Column(Integer, ForeignKey("student.id"), nullable=False)
    content = Column(Text, nullable=False)
    # default current time
    timeStamp = Column(DateTime, default=datetime.now)

class Inbox(Base):
    __tablename__ = "inbox"
    id = Column(Integer, primary_key=True, autoincrement=True)
    # store student's id
    student_id = Column(Integer, ForeignKey("student.id"), unique=True, nullable=False)

    messages = relationship(
        'Message',
        secondary=inbox_messages,  # 显式指定中间表
        primaryjoin=(inbox_messages.c.inbox_id == id),
        secondaryjoin=(inbox_messages.c.message_id == Message.id),
    )

class ListingCatalog(Base):
    __tablename__ = "listing_catalog"
    id = Column(Integer, primary_key=True, autoincrement=True)
    listings = relationship(
        'Listing',
        secondary=catalog_listings,  # 中间表
        primaryjoin=(catalog_listings.c.catalog_id == id),
        secondaryjoin=(catalog_listings.c.listing_id == Listing.id),
    )
    query=Column(String(100), nullable=False)

    def searchByKeyword(self):
        pass
    def searchByCategory(self):
        pass
    def sortBy(self):
        pass

#using sql database
engine = create_engine("sqlite:///order.db")
#generate database
Base.metadata.create_all(engine)

#build dataset factory and finally instantialized an object
Session = sessionmaker(bind=engine)
session = Session()
