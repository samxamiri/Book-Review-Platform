
from flask import Flask, jsonify, request, render_template, flash, redirect, url_for
from models import db, Book, Review, User
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
GOOGLE_BOOKS_API_URL = 'https://www.googleapis.com/books/v1/volumes'
app.secret_key = "dfsdfiojsdfoisdjfgoisgnwosd89234hr239sdlsdflk"

def search_books(query, max_results=10):
    params = {
        'q': query,
        'maxResults': max_results
    }
    response = requests.get(GOOGLE_BOOKS_API_URL, params=params)
    if response.status_code != 200:
        return []
    
    results = response.json().get('items', [])
    books = []
    seen_books = set()  # A set to keep track of books we've already added based on title and author

    for item in results:
        volume_info = item.get('volumeInfo', {})
        title = volume_info.get('title', '')
        author = ', '.join(volume_info.get('authors', []))
        
        # Generate a unique identifier for this book based on its title and author
        book_id = title + "|" + author

        # If we've not seen this book before, add it to our results
        if book_id not in seen_books:
            book_data = {
                'title': title,
                'author': author,
                'description': volume_info.get('description', ''),
                # Add more fields as needed
            }
            books.append(book_data)
            seen_books.add(book_id)  # Mark this book as seen

    return books


def fetch_book_details_from_google(book_id):
    response = requests.get(f"{GOOGLE_BOOKS_API_URL}/{book_id}")
    if response.status_code != 200:
        return None
    volume_info = response.json().get('volumeInfo', {})
    book_data = {
        'title': volume_info.get('title'),
        'author': ', '.join(volume_info.get('authors', [])),
        'description': volume_info.get('description', ''),
        'cover_image': volume_info.get('imageLinks', {}).get('thumbnail', ''),  # Extracting the cover image URL
        # Add more fields as needed
    }
    return book_data


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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))


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



@app.route('/welcome')
@login_required
def welcome():
    return render_template('welcome.html')


@app.route('/')
def landing():
    return render_template('landing.html')


@app.route('/review')
@login_required
def review():
    return render_template('review.html')

@app.route('/profile')
@login_required
def user_profile():
    return render_template('profile.html')


@app.route('/profile/<int:user_id>')
def profile_by_id(user_id):
    user = User.query.get(user_id)
    if not user:
        return "User not found", 404
    reviews = Review.query.filter_by(user_id=user.id).all()
    read_books = {review.book for review in reviews}
    return render_template('profile.html', user=user, read_books=read_books, reviews=reviews)






#retrieves all books from database
@app.route('/books',methods=['GET']) #maps a URL route to the associated function get_books. route only responds to HTTP GET requests
def get_books():  #function that gets executed when books route is accessed via a GET request.
    books=Book.query.all() #executes the query, fethcing all rows from the 'Book' table and returning them as a list of 'Book' objects.
    return jsonify ([book.serialize for book in books]) #book.serialize converts the object into a dictionary representation, jsonify converts the list of dictionaries into a JSON response that's sent back to client

#Adds a new book to database
@app.route('/book', methods=['POST'])
def add_book():
    title = request.json.get('title')
    author = request.json.get('author')
    new_book = Book(title=title, author=author)
    db.session.add(new_book)
    db.session.commit()
    return jsonify(new_book.serialize), 201

@app.route('/save_book', methods=['POST'])
def save_book():
    google_book_id = request.form.get('google_book_id')
    book_details = fetch_book_details_from_google(google_book_id)

    if not book_details:
        flash('Error fetching book details from Google Books.')
        return redirect(url_for('review'))

    existing_book = Book.query.filter_by(google_book_id=google_book_id).first()
    if existing_book:
        flash('Book already exists in the database.')
        return redirect(url_for('review'))

    new_book = Book(
        title=book_details['title'], 
        author=book_details['author'],
        google_book_id=google_book_id,
        cover_image=book_details['cover_image']  # Add the cover image attribute here
    )
    # Add other details as necessary
    db.session.add(new_book)
    db.session.commit()

    flash('Book added successfully!')
    return redirect(url_for('review'))





@app.route('/book/<int:book_id>/review', methods=['POST'])
def add_review(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({'message': 'Book not found'}), 404
    text = request.json.get('text')
    rating = request.json.get('rating')
    review = Review(text=text, rating=rating, user_id=current_user.id, book_id=book_id)
    db.session.add(review)
    db.session.commit()
    return jsonify(review.serialize), 201

@app.route('/search_books', methods=['POST'])
def search_books_route():
    query = request.form.get('query', '')

    # If the search query is empty, return an empty result
    if not query:
        return jsonify([])

    # Using Google Books API to fetch books
    base_url = "https://www.googleapis.com/books/v1/volumes"
    payload = {
        'q': query,
        'maxResults': 10,
        'printType': 'books'
    }

    response = requests.get(base_url, params=payload)
    data = response.json()
    items = data.get('items', [])

    books = []
    for item in items:
        volume_info = item.get('volumeInfo', {})
        title = volume_info.get('title', '')
        authors = volume_info.get('authors', ['Unknown Author'])

        # Let's get only the books that have title and at least one author mentioned
        if title and authors:
            books.append({
                'title': title,
                'authors': authors
            })

    # Deduplication logic
    unique_books = {}
    for book in books:
        title = book.get('title', 'Unknown Title')
        authors = book.get('authors', ['Unknown Author'])  # Default to list with 'Unknown Author'
        
        identifier = (title, tuple(authors))  # Convert authors list to tuple for hashing
        unique_books[identifier] = book  # Storing the book with the unique identifier

    return jsonify(list(unique_books.values()))

@app.route('/submitReview', methods=['POST'])
@login_required
def submit_review():
    data = request.get_json()

    review_content = data.get('review')
    google_book_id_from_request = data.get('google_book_id').strip()

    # Check if book exists in the database by google_book_id
    book = Book.query.filter_by(google_book_id=google_book_id_from_request).first()

    # If the book doesn't exist in the database, fetch its details from Google Books and then create a new entry
    if not book:
        book_details = fetch_book_details_from_google(google_book_id_from_request)
        if not book_details:
            return jsonify({"success": False, "message": "Error fetching book details from Google Books."})

        book = Book(
            title=book_details['title'], 
            author=book_details['author'],
            google_book_id=google_book_id_from_request,
            cover_image=book_details['cover_image']  # Add the cover image attribute here
        )
        db.session.add(book)
        db.session.flush()  # To get the id of the newly created book

    # Create a new review
    review = Review(content=review_content, user_id=current_user.id, book_id=book.id)
    db.session.add(review)
    db.session.commit()

    return jsonify({"success": True, "message": "Review successfully added!"})



@app.route('/getReviews')
@login_required
def get_user_reviews():
    reviews = Review.query.filter_by(user_id=current_user.id).all()
    
    reviews_data = [{
    "id": review.id, 
    "cover": review.book.cover_image if review.book.cover_image else "path_to_default_image.jpg"
} for review in reviews]

    return jsonify({"reviews": reviews_data})

@app.route('/deleteReview', methods=['POST'])
def delete_review():
    review_id = request.json.get('id')
    print(review_id)

    if remove_review(review_id):
        return jsonify(success=True)
    else:
        return jsonify(success=False, error="Error removing review"), 400
    
def remove_review(review_id):
    review = Review.query.get(review_id)  # assuming your model name is Review
    if review:
        db.session.delete(review)
        db.session.commit()
        return True
    return False







if __name__ == '__main__':
    app.run(debug=True)
