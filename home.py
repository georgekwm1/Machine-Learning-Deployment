#!/usr/bin/python3
"""
    Script that starts a Flask web application
"""
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://hamisu:my_password@127.0.0.1/nryde_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Books data model
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Book {self.title} by {self.author}>'

# Get all books
@app.route('/books', strict_slashes=False, methods=["GET"])
def get_books():
    books = Book.query.all()
    return jsonify([{'id': book.id, 'title': book.title, 'author': book.author} for book in books])

# Get a single book by id
@app.route('/books/<int:book_id>', strict_slashes=False, methods=["GET"])
def get_book(book_id):
    book = Book.query.get(book_id)
    if book is None:
        return jsonify({"error": "Book not found"}), 404
    return jsonify({'id': book.id, 'title': book.title, 'author': book.author})

# Post a new book 
@app.route('/books', strict_slashes=False, methods=["POST"])
def create_book():
    data = request.get_json()
    new_book = Book(title=data["title"], author=data["author"])
    db.session.add(new_book)
    db.session.commit()
    return jsonify({'id': new_book.id, 'title': new_book.title, 'author': new_book.author}), 201

# PUT Update a book   
@app.route('/books/<int:book_id>', strict_slashes=False, methods=["PUT"])
def update_book(book_id):
    book = Book.query.get(book_id)
    if book is None:
        return jsonify({"error": "Book not found"}), 404
    data = request.get_json()
    book.title = data.get("title", book.title)
    book.author = data.get("author", book.author)
    db.session.commit()
    return jsonify({'id': book.id, 'title': book.title, 'author': book.author})

# DELETE a book   
@app.route('/books/<int:book_id>', strict_slashes=False, methods=["DELETE"])
def delete_book(book_id):
    book = Book.query.get(book_id)
    if book is None:
        return jsonify({"error": "Book not found"}), 404
    db.session.delete(book)
    db.session.commit()
    return "", 204

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)
