from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, mapped_column


class Base(DeclarativeBase):
    pass


class Customer(Base):
    __tablename__ = "customers"

    customer_id = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_name = mapped_column(String)
    customer_info_id = mapped_column(
        Integer,
        ForeignKey(
            "customer_info.customer_info_id",
            name="customer_info_customer_info_id_fk",
            ondelete="CASCADE",
        ),
    )


class CustomerInfo(Base):
    __tablename__ = "customer_info"

    customer_info_id = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_address = mapped_column(String)
    customer_phone = mapped_column(String)
    customer_email = mapped_column(String)


class Product(Base):
    __tablename__ = "products"

    product_id = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_name = mapped_column(String)


class Order(Base):
    __tablename__ = "orders"

    order_id = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_date = mapped_column(DateTime)
    customer_id = mapped_column(
        Integer,
        ForeignKey("customers.customer_id", ondelete="CASCADE"),
    )


class ProductOrder(Base):
    __tablename__ = "products_orders"

    product_order_id = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id = mapped_column(
        Integer,
        ForeignKey("orders.order_id", ondelete="CASCADE"),
    )
    product_id = mapped_column(
        Integer,
        ForeignKey("orders.order_id", ondelete="CASCADE"),
    )
    price = mapped_column(Integer)
