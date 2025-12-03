from sqlalchemy import *
from sqlalchemy.orm import sessionmaker, relationship
import sqlalchemy
from datetime import datetime

# from app import student_login

# global session
Base = sqlalchemy.orm.declarative_base()
engine = create_engine("sqlite:///order.db")
Session = sessionmaker(bind=engine)
session = Session()

# ---------depend class/tables-------

# tags of goods
class Tag(Base):
    __tablename__ = "tag"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False) 

# table between goods and tags
class ListingTag(Base):

    # on delete makes sure it automatically delete(even though i did it in deletelisitng method)
    __tablename__ = "listing_tag"
    listing_id = Column(
        Integer,
        ForeignKey("listing.id", ondelete="CASCADE"),
        primary_key=True
    )
    tag_id = Column(
        Integer,
        ForeignKey("tag.id", ondelete="CASCADE"),
        primary_key=True
    )

# orders,store transaction history
class Order(Base):

    __tablename__ = "order"
    id = Column(Integer, primary_key=True, autoincrement=True)
    buyer_id = Column(
        Integer,
        ForeignKey("student.id"),
        nullable=False
    )
    listing_id = Column(
        Integer,
        ForeignKey("listing.id"),
        nullable=False
    )
    seller_id = Column(
        Integer,
        ForeignKey("student.id"),
        nullable=False
    )
    # price, payment and order time
    price = Column(Float, nullable=False)
    payment_method = Column(String(256))
    order_time = Column(DateTime, default=datetime.now, nullable=False)

# blocked user(not sure whether to implement it)
class BlockedUser(Base):
    __tablename__ = "blockedUsers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    # auto clean blocked users when it is removed
    student_id = Column(
        Integer,
        ForeignKey("student.id", ondelete="CASCADE"),
        nullable=False
    )
    blocked_id = Column(
        Integer,
        ForeignKey("student.id", ondelete="CASCADE"),
        nullable=False
    )
    block_time = Column(DateTime, default=datetime.now, nullable=False)  
    # we can't block same user multiple times when it is blocked
    __table_args__ = (UniqueConstraint('student_id', 'blocked_id', name='_student_blocked_uc'),)


class Student(Base):
    __tablename__ = "student"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    pittEmail = Column(String(100), unique=True, nullable=False)
    phoneNumber = Column(String(20), nullable=False)
    password = Column(String(256), nullable=False)
    paymentMethod = Column(String(256), nullable=True)
    paymentInformation = Column(Text, nullable=True)

    # 1. checked blocked users
    @property
    def blockedUsers(self):
        sql = text("""
            SELECT bu.blocked_id, s.name as blocked_name, bu.block_time
            FROM blockedUsers bu
            JOIN student s ON bu.blocked_id = s.id
            WHERE bu.student_id = :stu_id
        """)
        res = session.execute(sql, {"stu_id": self.id})
        return [dict(row) for row in res.mappings()]

    # 2. check saved products
    @property
    def savedListing(self):
        # sql=text("select distinct l.* from listing l join savedList sl on l.id = sl.product_id"
        #          " where sl.student_id =:id and l.status='Available' and l.id is not null")
        sql=text("select * from savedList where student_id= :id")
        res = session.execute(sql, {"id": self.id})
        return [dict(row) for row in res.mappings()]

    # login testing, make sure name and password are the same
    def login(self, name, password):
        res= (name==self.name) and (password== self.password)
        print("Res is:",res)
        # create inbox
        if res:
            exist=session.query(Inbox).filter_by(student_id=self.id).first()
            if not exist:
                new_inbox=Inbox(student_id=self.id)
                session.add(new_inbox)
                session.commit()
        return  res

    # return all of the saved list
    def reportListing(self):
        return self.savedListing

    # check student's selling products
    @property
    def sellerlisting(self):
        sql = text("SELECT * FROM listing WHERE seller = :id")
        res = session.execute(sql, {"id": self.id})
        return [dict(row) for row in res.mappings()]

    # 6. create product
    def createListing(self, title, description, price, address, category="Books", status="Available"):
        try:
            # insert products' record
            sql = text("""
                INSERT INTO listing 
                (title, description, price, sellerName, seller, address, category, status, datePosted)
                VALUES (:title, :desc, :price, :seller_name, :seller_id, :addr, :cate, :status, CURRENT_TIMESTAMP)
                RETURNING id 
            """)
            res = session.execute(sql, {
                # product tile, description, price, category, address and status
                # (seller name and seller_id automatically created)
                "title": title,
                "desc": description,
                "price": price,
                "seller_name": self.name,
                "seller_id": self.id,
                "addr": address,
                "cate": category,
                "status": status
            })
            listing_id = res.scalar()
            session.commit()
            print(f"successfully created product：{listing_id}")
            return listing_id
        except Exception as e:
            session.rollback()
            print("failed to create product")
            return None

    # delete product
    def deleteListing(self, listing_id):
        try:
            # make sure product exist
            listing = session.execute(
                text("SELECT 1 FROM listing WHERE id = :list_id AND seller = :seller_id"),
                {"list_id": listing_id, "seller_id": self.id}
            ).scalar()
            if not listing:
                print("goods doesn't exist or not belongs to you")
                return False

            # 2. delete product from listing_tag, listing, savedlist
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
            print("failed to delete product")
            return False

    # give product a tag
    def tagListing(self, listing_id, tags):
        try:
            # make sure product belongs to student
            listing_exists = session.execute(
                text("SELECT 1 FROM listing WHERE id = :list_id AND seller = :seller_id"),
                {"list_id": listing_id, "seller_id": self.id}
            ).scalar()
            if not listing_exists:
                print("goods doesn't exist or not belongs to you")
                return False

            # delete all the current related tags
            session.execute(
                text("DELETE FROM listing_tag WHERE listing_id = :list_id"),
                {"list_id": listing_id}
            )
            session.flush()

        # deal wirh tag
            for tag_name in tags:
                # check whether tag exist
                tag = session.query(Tag).filter_by(name=tag_name).first()
                if not tag:
                    # add tags
                    tag = Tag(name=tag_name)
                    session.add(tag)
                    # get tag
                    session.flush()

                # check whether tag exist
                listing_tag = session.query(ListingTag).filter_by(
                    listing_id=listing_id, tag_id=tag.id
                ).first()
                if not listing_tag:
                    # add correlations
                    listing_tag = ListingTag(listing_id=listing_id, tag_id=tag.id)
                    session.add(listing_tag)

            session.commit()
            print("succesfully tag it")
            return True
        except Exception as e:
            session.rollback()
            print("failed to tag it")
            return False

    # buy product
    def purchaseItem(self, listing_id, payment_method=None):
        try:
            # make sure we can buy the product
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

            # create order
            order = Order(
                buyer_id=self.id,
                listing_id=listing_id,
                seller_id=listing["seller"],
                price=listing["price"],
                payment_method=payment_method or self.paymentMethod
            #     auto generate order time
            )
            session.add(order)

            # update product as sold out
            session.execute(
                text("UPDATE listing SET status = 'Sold' WHERE id = :list_id"),
                {"list_id": listing_id}
            )

            # delete that product
            session.execute(
                text("DELETE FROM savedList WHERE product_id = :list_id"),
                {"list_id": listing_id}
            )

            session.commit()
            print("successfully buy it")
            return True
        except Exception as e:
            session.rollback()
            print("failed to buy it ")
            return False

    # save product
    def saveListing(self, product_id):
        try:
            # verify product exist
            product_exists = session.execute(
                text("SELECT 1 FROM listing WHERE id = :prod_id and seller != :student_id"),
                {"prod_id": product_id,"student_id": self.id}
            ).scalar()
            if not product_exists:
                print("product doesn't exist")
                return False

            # verify not save repeatedly
            exists = session.execute(
                text("SELECT 1 FROM savedList WHERE student_id = :stu_id AND product_id = :prod_id"),
                {"stu_id": self.id, "prod_id": product_id}
            ).scalar()
            if exists:
                print("you've already saved it")
                return False

            # 3. insert into saved list
            session.execute(
                text("INSERT INTO savedList (student_id, product_id) VALUES (:stu_id, :prod_id)"),
                {"stu_id": self.id, "prod_id": product_id}
            )
            session.commit()
            print("successfully saved it")
            return True
        except Exception as e:
            session.rollback()
            print("failed to save it")
            return False

class Inbox(Base):
    __tablename__ = "inbox"
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("student.id", ondelete="CASCADE"), nullable=False)  # 关联学生ID（每个学生一个收件箱）

    # get all messages
    @property
    def message(self):
        # return all the buyer's message(based on time)
        sql = text("""
            SELECT m.*, s.name as sender_name 
            FROM message m
            JOIN student s ON m.sender_id = s.id
            WHERE m.receiver_id = :stu_id
            ORDER BY m.timeStamp DESC
        """)
        res = session.execute(sql, {"stu_id": self.student_id})
        return [dict(row) for row in res.mappings()]

    # send message when buy products
    def sendmessage(self, sender_id, content):
        try:
            # verify buyer and seller
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

            # insert messages
            sql = text("""
                INSERT INTO message (sender_id, receiver_id, content, timeStamp)
                VALUES (:sender_id, :receiver_id, :content, :current_time)
                RETURNING id
            """)
            res = session.execute(sql, {
                "sender_id": sender_id,
                "receiver_id": self.student_id,
                "content": content,
                "current_time": datetime.now()
            })
            msg_id = res.scalar()
            session.commit()
            print("successfully send message")
            return msg_id
        except Exception as e:
            session.rollback()
            print("failed send messages")
            return None

class Message(Base):
    __tablename__ = "message"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sender_id = Column(Integer, ForeignKey("student.id", ondelete="CASCADE"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("student.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    timeStamp = Column(DateTime, default=datetime.now)

class Listing(Base):
    __tablename__ = "listing"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Float, nullable=False)
    sellerName = Column(String(50), nullable=False)
    address = Column(String(100))
    datePosted = Column(DateTime, default=datetime.now)
    images = Column(JSON, default=[])
    category = Column(String(50), nullable=True)
    status = Column(String(20),default="Available")
    seller = Column(Integer, ForeignKey("student.id"))

class ListingCatalog(Base):
    __tablename__ = "listingCatalog"
    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(String(100), nullable=False)

    # search all products
    @property
    def listings(self):
        sql = text("SELECT * FROM listing")
        res = session.execute(sql)
        return [dict(row) for row in res.mappings()]

    # search by keyword
    def searchByKeyword(self):
        sql = text("""
            SELECT * FROM listing 
            WHERE title LIKE :kw OR description LIKE :kw
            ORDER BY datePosted DESC
        """)

        res = session.execute(sql, {"kw": f"%{self.query}%"})  # use like to do vague search
        return [dict(row) for row in res.mappings()]

    # search by category
    def searchByCategory(self):
        sql = text("""
            SELECT * FROM listing 
            WHERE category = :category
            ORDER BY datePosted DESC
        """)
        res = session.execute(sql, {"category": self.query})
        return [dict(row) for row in res.mappings()]

    # sort by price
    def sortBy(self, sort_type="asc"):
        # default ascending
        if sort_type not in ["asc", "desc"]:
            sort_type = "asc"

        sql = text(f"SELECT * FROM listing ORDER BY price {sort_type}")
        res = session.execute(sql)
        return [dict(row) for row in res.mappings()]

class SavedList(Base):
    __tablename__ = "savedList"
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("student.id", ondelete="CASCADE"))
    product_id = Column(Integer, ForeignKey("listing.id", ondelete="CASCADE"))
    # avoid save repeatedlly(maybe implemented previously)
    __table_args__ = (UniqueConstraint('student_id', 'product_id', name='_student_product_uc'),)

# ---------create all tables-----------------
Base.metadata.create_all(engine)
print("all tables have been generated")
