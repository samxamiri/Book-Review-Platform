from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


db = SQLAlchemy()

class User(db.Model, UserMixin):  # Notice the added UserMixin
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    reviews = db.relationship('Review', backref='user', lazy=True)
    is_active = db.Column(db.Boolean, default=True)

    @property
    def is_authenticated(self):
        # Since we have a UserMixin, it provides a default implementation for this.
        # But for clarity, you can return True here because if a user object exists, it's authenticated.
        return True

    @property
    def is_anonymous(self):
        # Default to False for authenticated users.
        return False

    def get_id(self):
        return str(self.id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def serialize(self):
        return {
            "id": self.id,
            "username": self.username,
            "reviews": [review.serialize for review in self.reviews]
        }

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    reviews = db.relationship('Review', backref='book', lazy=True)

    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "reviews": [review.serialize for review in self.reviews]
        }

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)

    def serialize(self):
        return {
            "id": self.id,
            "content": self.content,
            "user_id": self.user_id,
            "book_id": self.book_id
        }

