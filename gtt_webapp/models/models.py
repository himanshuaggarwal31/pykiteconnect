from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class GTTOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tradingsymbol = db.Column(db.String(20), nullable=False)
    exchange = db.Column(db.String(10), nullable=False)
    trigger_type = db.Column(db.String(20), nullable=False)
    trigger_values = db.Column(db.String(100), nullable=False)  # Stored as comma-separated values
    last_price = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(20), default='active')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'tradingsymbol': self.tradingsymbol,
            'exchange': self.exchange,
            'trigger_type': self.trigger_type,
            'trigger_values': self.trigger_values,
            'last_price': self.last_price,
            'transaction_type': self.transaction_type,
            'quantity': self.quantity,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class NiftyMcap(db.Model):
    __tablename__ = 'nifty_mcap'
    
    symbol = db.Column(db.String(20), primary_key=True)
    company_name = db.Column(db.String(200), nullable=False)
    mcap_lakhs = db.Column(db.Numeric(20), nullable=True)
    nifty_rank = db.Column(db.Integer, nullable=True)
    him_rating = db.Column(db.String(500), nullable=True)
    rating_date = db.Column(db.Date, nullable=True)

    def to_dict(self):
        return {
            'symbol': self.symbol,
            'company_name': self.company_name,
            'mcap_lakhs': float(self.mcap_lakhs) if self.mcap_lakhs else None,
            'nifty_rank': self.nifty_rank,
            'him_rating': self.him_rating,
            'rating_date': self.rating_date.isoformat() if self.rating_date else None
        }

class StockData(db.Model):
    __tablename__ = 'stock_data'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    symbol = db.Column(db.String(20), nullable=False, index=True)
    date1 = db.Column(db.Date, nullable=False, index=True)
    last_price = db.Column(db.Numeric(10, 2))
    open_price = db.Column(db.Numeric(10, 2))
    high_price = db.Column(db.Numeric(10, 2))
    low_price = db.Column(db.Numeric(10, 2))
    volume = db.Column(db.BigInteger)
    
    # Create composite index for better query performance
    __table_args__ = (
        db.Index('idx_symbol_date', 'symbol', 'date1'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'date1': self.date1.isoformat() if self.date1 else None,
            'last_price': float(self.last_price) if self.last_price else None,
            'open_price': float(self.open_price) if self.open_price else None,
            'high_price': float(self.high_price) if self.high_price else None,
            'low_price': float(self.low_price) if self.low_price else None,
            'volume': self.volume
        }
