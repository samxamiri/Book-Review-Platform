
from flask import Flask, jsonify, request, render_template, flash, redirect, url_for
from models import db, Book, Review, User
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

app.secret_key = "dfsdfiojsdfoisdjfgoisgnwosd89234hr239sdlsdflk"


db.init_app(app)

# Add this line to initialize Flask-Migrate
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('welcome'))
        else:
            flash('Invalid credentials. Please try again.')
    return render_template('login.html')




@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if the user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose another one.')
            return render_template('register.html')

        # Create a new user instance and set its password
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Successfully registered! Please login.')
        return redirect(url_for('login'))
    return render_template('register.html')



@app.route('/landing')
@login_required
def welcome():
    return render_template('landing.html')


@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/profile')
@login_required
def profile():
    return jsonify(current_user.serialize)





@app.route('/books',methods=['GET']) #maps a URL route to the associated function get_books. route only responds to HTTP GET requests
def get_books():  #function that gets executed when books route is accessed via a GET request.
    books=Book.query.all() #executes the query, fethcing all rows from the 'Book' table and returning them as a list of 'Book' objects.
    return jsonify ([book.serialize for book in books]) #book.serialize converts the object into a dictionary representation, jsonify converts the list of dictionaries into a JSON response that's sent back to client

@app.route('/book', methods=['POST'])
def add_book():
    title = request.json.get('title')
    author = request.json.get('author')
    new_book = Book(title=title, author=author)
    db.session.add(new_book)
    db.session.commit()
    return jsonify(new_book.serialize), 201

@app.route('/book/<int:book_id>/review', methods=['POST'])
def add_review(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({'message': 'Book not found'}), 404
    text = request.json.get('text')
    rating = request.json.get('rating')
    review = Review(text=text, rating=rating, book_id=book_id)
    db.session.add(review)
    db.session.commit()
    return jsonify(review.serialize), 201


if __name__ == '__main__':
    app.run(debug=True)
