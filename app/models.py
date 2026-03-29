from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

USER_STATUSES = ("active", "inactive", "suspended")
PURCHASE_STATUSES = ("pending", "received", "cancelled")
SALE_STATUSES = ("pending", "completed", "cancelled")
CASH_REGISTER_STATUSES = ("open", "closed", "maintenance")
CASH_SESSION_STATUSES = ("open", "closed", "cancelled")

# ================================================================
#-- 2. ESTRUCTURA ORGANIZACIONAL (SEDES)
# ================================================================
class Branch(Base):
    __tablename__ = "branches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    address = Column(Text)
    phone = Column(String(20))
    is_active = Column(Boolean, default=True, nullable=False)
    deleted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # RELACIONES
    users = relationship("User", back_populates="branch")
    inventory = relationship("BranchInventory", back_populates="branch")
    cash_registers = relationship("CashRegister", back_populates="branch")
    sales = relationship("Sale", back_populates="branch")
    purchases = relationship("Purchase", back_populates="branch")

# ================================================================
#-- 3. SEGURIDAD Y ACCESO (IAM / RBAC)
# ================================================================
class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(Text)

    # RELACIONES
    users = relationship("User", back_populates="role")
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles")

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(100), unique=True, nullable=False)

    # RELACIONES
    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")

class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'suspended')",
            name="ck_users_status",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False)
    status = Column(String(20), default="active", nullable=False)
    deleted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # RELACIONES
    role = relationship("Role", back_populates="users")
    branch = relationship("Branch", back_populates="users")
    cash_sessions = relationship("CashSession", back_populates="user")
    sales = relationship("Sale", back_populates="user")
    purchases = relationship("Purchase", back_populates="user")

# ================================================================
#-- 4. INVENTARIO Y COSTOS
# ================================================================
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    deleted_at = Column(DateTime(timezone=True))

    # RELACIONES
    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"))
    is_active = Column(Boolean, default=True, nullable=False)
    deleted_at = Column(DateTime(timezone=True))

    # RELACIONES
    category = relationship("Category", back_populates="products")
    inventory_stocks = relationship("BranchInventory", back_populates="product")
    purchase_items = relationship("PurchaseItem", back_populates="product")
    sale_items = relationship("SaleItem", back_populates="product")

class BranchInventory(Base):
    __tablename__ = "branch_inventory"
    __table_args__ = (
        UniqueConstraint("branch_id", "product_id", name="uq_branch_inventory_branch_product"),
        CheckConstraint("stock >= 0", name="ck_branch_inventory_stock_non_negative"),
        CheckConstraint("min_stock >= 0", name="ck_branch_inventory_min_stock_non_negative"),
        CheckConstraint(
            "last_unit_cost_base >= 0",
            name="ck_branch_inventory_last_unit_cost_non_negative",
        ),
        CheckConstraint(
            "average_unit_cost_base >= 0",
            name="ck_branch_inventory_average_unit_cost_non_negative",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    stock = Column(Numeric(12, 2), default=0, nullable=False)
    min_stock = Column(Numeric(12, 2), default=5, nullable=False)
    last_unit_cost_base = Column(Numeric(18, 2), default=0, nullable=False)
    average_unit_cost_base = Column(Numeric(18, 2), default=0, nullable=False)

    # RELACIONES
    branch = relationship("Branch", back_populates="inventory")
    product = relationship("Product", back_populates="inventory_stocks")

# ================================================================
#-- 5. LOGÍSTICA (COMPRAS Y TRANSFERENCIAS)
# ================================================================
class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    tax_id = Column(String(20), unique=True, nullable=False)
    company_name = Column(String(150), nullable=False)
    contact_name = Column(String(100))
    phone = Column(String(20))
    email = Column(String(100))
    deleted_at = Column(DateTime(timezone=True))

    # RELACIONES
    purchases = relationship("Purchase", back_populates="supplier")

class Purchase(Base):
    __tablename__ = "purchases"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'received', 'cancelled')",
            name="ck_purchases_status",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    total_cost_base = Column(Numeric(18, 2), nullable=False)
    status = Column(String(20), default="received", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # RELACIONES
    supplier = relationship("Supplier", back_populates="purchases")
    branch = relationship("Branch", back_populates="purchases")
    user = relationship("User", back_populates="purchases")
    items = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")

class PurchaseItem(Base):
    __tablename__ = "purchase_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_purchase_items_quantity_positive"),
        CheckConstraint("unit_cost_base >= 0", name="ck_purchase_items_unit_cost_non_negative"),
    )

    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    unit_cost_base = Column(Numeric(18, 2), nullable=False)

    # RELACIONES
    purchase = relationship("Purchase", back_populates="items")
    product = relationship("Product", back_populates="purchase_items")

# ================================================================
#-- 6. VENTAS Y CLIENTES
# ================================================================
class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    tax_id = Column(String(20), unique=True, nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(100))
    deleted_at = Column(DateTime(timezone=True))

    # RELACIONES
    sales = relationship("Sale", back_populates="customer")

class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'completed', 'cancelled')",
            name="ck_sales_status",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"))
    total_amount_base = Column(Numeric(18, 2), nullable=False)
    status = Column(String(20), default="completed", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # RELACIONES
    branch = relationship("Branch", back_populates="sales")
    user = relationship("User", back_populates="sales")
    customer = relationship("Customer", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="sale")

class SaleItem(Base):
    __tablename__ = "sale_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_sale_items_quantity_positive"),
        CheckConstraint("unit_price_base >= 0", name="ck_sale_items_unit_price_non_negative"),
        CheckConstraint(
            "unit_cost_at_sale_base >= 0",
            name="ck_sale_items_unit_cost_at_sale_non_negative",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    unit_price_base = Column(Numeric(18, 2), nullable=False)
    unit_cost_at_sale_base = Column(Numeric(18, 2), nullable=False)

    # RELACIONES
    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")

# ================================================================
#-- 7. TESORERÍA Y MULTIDIVISA
# ================================================================
class Currency(Base):
    __tablename__ = "currencies"
    __table_args__ = (
        Index(
            "uq_currencies_single_default",
            "is_default",
            unique=True,
            postgresql_where=text("is_default = true"),
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False)
    symbol = Column(String(5))
    is_default = Column(Boolean, default=False, nullable=False)

    # RELACIONES
    exchange_rates = relationship("ExchangeRate", back_populates="currency")
    payments = relationship("Payment", back_populates="currency")


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    code = Column(String(30), nullable=False, unique=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # RELACIONES
    payments = relationship("Payment", back_populates="payment_method")

class ExchangeRate(Base):
    __tablename__ = "exchange_rates"
    __table_args__ = (
        CheckConstraint("rate_value > 0", name="ck_exchange_rates_rate_positive"),
    )

    id = Column(Integer, primary_key=True, index=True)
    currency_id = Column(Integer, ForeignKey("currencies.id", ondelete="CASCADE"), nullable=False)
    rate_value = Column(Numeric(18, 4), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # RELACIONES
    currency = relationship("Currency", back_populates="exchange_rates")
    payments = relationship("Payment", back_populates="exchange_rate")

class CashRegister(Base):
    __tablename__ = "cash_registers"
    __table_args__ = (
        UniqueConstraint("branch_id", "name", name="uq_cash_registers_branch_name"),
        CheckConstraint(
            "status IN ('open', 'closed', 'maintenance')",
            name="ck_cash_registers_status",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), nullable=False)
    status = Column(String(20), default="closed", nullable=False)

    # RELACIONES
    branch = relationship("Branch", back_populates="cash_registers")
    sessions = relationship("CashSession", back_populates="cash_register")

class CashSession(Base):
    __tablename__ = "cash_sessions"
    __table_args__ = (
        CheckConstraint("opening_balance >= 0", name="ck_cash_sessions_opening_balance_non_negative"),
        CheckConstraint(
            "closing_balance_real IS NULL OR closing_balance_real >= 0",
            name="ck_cash_sessions_closing_balance_non_negative",
        ),
        CheckConstraint(
            "status IN ('open', 'closed', 'cancelled')",
            name="ck_cash_sessions_status",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    cash_register_id = Column(Integer, ForeignKey("cash_registers.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    opening_balance = Column(Numeric(18, 2), default=0, nullable=False)
    closing_balance_real = Column(Numeric(18, 2))
    status = Column(String(20), default="open", nullable=False)
    opened_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True))

    # RELACIONES
    cash_register = relationship("CashRegister", back_populates="sessions")
    user = relationship("User", back_populates="cash_sessions")
    payments = relationship("Payment", back_populates="cash_session")

class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount_native >= 0", name="ck_payments_amount_native_non_negative"),
        CheckConstraint("amount_base >= 0", name="ck_payments_amount_base_non_negative"),
    )

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    cash_session_id = Column(Integer, ForeignKey("cash_sessions.id", ondelete="RESTRICT"), nullable=False)
    payment_method_id = Column(Integer, ForeignKey("payment_methods.id", ondelete="RESTRICT"), nullable=False)
    currency_id = Column(Integer, ForeignKey("currencies.id", ondelete="RESTRICT"), nullable=False)
    exchange_rate_id = Column(Integer, ForeignKey("exchange_rates.id", ondelete="SET NULL"))
    amount_native = Column(Numeric(18, 2), nullable=False)
    amount_base = Column(Numeric(18, 2), nullable=False)
    reference_number = Column(String(100))

    # RELACIONES
    sale = relationship("Sale", back_populates="payments")
    cash_session = relationship("CashSession", back_populates="payments")
    payment_method = relationship("PaymentMethod", back_populates="payments")
    currency = relationship("Currency", back_populates="payments")
    exchange_rate = relationship("ExchangeRate", back_populates="payments")