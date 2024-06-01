from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "postgresql://postgres:admin@localhost:5432/postgres"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Importowanie modeli
from models import Użytkownik, Książka, Wypożyczenie


@app.route("/")
def home():
    return "Welcome to the Library API!"

@app.route("/login", methods=["POST"])
def login_user():
    data = request.json
    email = data.get("email")
    haslo = data.get("haslo")
    user = Użytkownik.query.filter_by(email=email).first()
    if user and user.haslo == haslo:
        print("zalogowano")
        print(user.imie)
        return jsonify({"message": "Login successful!"}), 200
    else:
        print("zle haslo/email:")
        print(haslo)
        return jsonify({"message": "Invalid email or password!"}), 200

# Użytkownicy endpoints
@app.route("/users", methods=["POST"])
def create_user():
    data = request.json
    new_user = Użytkownik(
        imie=data.get("imie"),
        nazwisko=data.get("nazwisko"),
        email=data.get("email"),
        haslo=data.get("haslo"),
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User created!"}), 201


@app.route("/users/<string:email>", methods=["GET"])
def get_user(email):
    user = Użytkownik.query.filter_by(email=email).first_or_404()
    print("------")
    print(user.id_uzytkownika,user.imie,user.nazwisko,user.email)
    print("------")
    return jsonify(
        {
            "id": user.id_uzytkownika,
            "imie": user.imie,
            "nazwisko": user.nazwisko,
            "email": user.email,
        }
    )





# Książki endpoints
@app.route("/books", methods=["POST"])
def create_book():
    data = request.json
    new_book = Książka(
        tytul=data.get("tytul"),
        autor=data.get("autor"),
        kategoria=data.get("kategoria"),
        liczba_dostepnych_kopii=data.get("liczba_dostepnych_kopii"),
        rok_wydania=data.get("rok_wydania"),
    )
    db.session.add(new_book)
    db.session.commit()
    return jsonify({"message": "Book created!"}), 201


@app.route("/books/<int:id>", methods=["GET"])
def get_book(id):
    book = Książka.query.get_or_404(id)
    return jsonify(
        {
            "id": book.id_ksiazki,
            "tytul": book.tytul,
            "autor": book.autor,
            "kategoria": book.kategoria,
            "liczba_dostepnych_kopii": book.liczba_dostepnych_kopii,
            "rok_wydania": book.rok_wydania,
        }
    )


# Wypożyczenia endpoints
@app.route("/rentals", methods=["POST"])
def create_rental():
    data = request.json
    new_rental = Wypożyczenie(
        id_ksiazki=data.get("id_ksiazki"),
        id_uzytkownika=data.get("id_uzytkownika"),
        data_wypozyczenia=datetime.strptime(data.get("data_wypozyczenia"), "%Y-%m-%d"),
    )
    db.session.add(new_rental)
    db.session.commit()
    return jsonify({"message": "Rental created!"}), 201


@app.route("/rentals/<int:id>", methods=["GET"])
def get_rental(id):
    rental = Wypożyczenie.query.get_or_404(id)
    return jsonify(
        {
            "id": rental.id_wypozyczenia,
            "id_ksiazki": rental.id_ksiazki,
            "id_uzytkownika": rental.id_uzytkownika,
            "data_wypozyczenia": rental.data_wypozyczenia.strftime("%Y-%m-%d"),
            "data_zwrotu": rental.data_zwrotu.strftime("%Y-%m-%d"),
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
