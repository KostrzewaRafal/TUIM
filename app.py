from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import paypalrestsdk
from paypalrestsdk import Payment




app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "postgresql://postgres:admin@localhost:5432/postgres"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SQLALCHEMY_POOL_SIZE'] = 50
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 50
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 1
app.config['SQLALCHEMY_POOL_RECYCLE'] = 10

db = SQLAlchemy(app)

migrate = Migrate(app, db)

# Importowanie modeli
from models import Użytkownik, Książka, Wypożyczenie


#----------------------------------------------------------------------------------------------------------------------


# Konfiguracja PayPal SDK
paypalrestsdk.configure({
    "mode": "sandbox",  # Użyj "live" w produkcji
    "client_id": "ARoHlvsSBoH90U07deqAU_WHK_UvPU3L04tzftdhdZjPeXx4007Ciwqo0fX0E58QMcbEc8MzH9pK6d-b",
    "client_secret": "ENPto8cR60V2Ou0eZSYsWyhTtBOn0tfvRThkJr_bF6LTnBgvcXeJCmZ2juM-XFlEXoqJ9LyCCTkGY2iV"
})

@app.route("/paypal/topup", methods=["POST"])
def paypal_topup():
    data = request.json
    amount = data.get("amount")
    user_id = data.get("user_id")

    payment = Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "transactions": [{
            "amount": {
                "total": str(amount),
                "currency": "USD"
            },
            "description": f"Doładowanie konta dla użytkownika {user_id}"
        }],
        "redirect_urls": {
            "return_url": "http://localhost:5000/payment/execute",
            "cancel_url": "http://localhost:5000/payment/cancel"
        }
    })

    if payment.create():
        return jsonify({"paymentID": payment.id})
    else:
        return jsonify({"error": payment.error}), 400

@app.route("/payment/execute", methods=["POST"])
def execute_payment():
    payment_id = request.json.get("paymentID")
    payer_id = request.json.get("payerID")

    payment = Payment.find(payment_id)

    if payment.execute({"payer_id": payer_id}):
        # Zaktualizuj stan konta użytkownika w bazie danych
        user_id = request.json.get("user_id")
        amount = float(payment.transactions[0].amount.total)
        user = Użytkownik.query.get(user_id)
        user.stan_konta += amount
        db.session.commit()
        return jsonify({"message": "Payment executed successfully"}), 200
    else:
        return jsonify({"error": payment.error}), 400


#---------------------------------------------------------------------------------------------------------------------------
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
    
@app.route("/register", methods=["POST"])
def register_user():
    data = request.json
    email = data.get("email")
    existing_user = Użytkownik.query.filter_by(email=email).first()
    
    if existing_user:
        return jsonify({"message": "User already exists!"}), 200

    new_user = Użytkownik(
        imie=data.get("imie"),
        nazwisko=data.get("nazwisko"),
        email=email,
        haslo=data.get("haslo"),
        stan_konta=0
        
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User created!"}), 201


# Użytkownicy endpoints
@app.route("/test", methods=["GET"])
def test():
    book = db.session.query(Książka).get(11)
    print(book.liczba_dostepnych_kopii)
    setattr(book, 'liczba_dostepnych_kopii', book.liczba_dostepnych_kopii + 1)
    db.session.commit()
    print(book.liczba_dostepnych_kopii)
    return jsonify({"message": "dodano ksiązke test+1"}), 200

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

@app.route("/rentals", methods=["GET"])
def get_rentals():
    user_id = request.args.get("userId")
    rentals = Wypożyczenie.query.filter_by(id_uzytkownika=user_id).all()
    rental_list = []
    for rental in rentals:
        book = Książka.query.get(rental.id_ksiazki)
        rental_data = {
            "id": rental.id_wypozyczenia,
            "tytul": book.tytul,
            "data_wypozyczenia": rental.data_wypozyczenia.strftime("%Y-%m-%d"),
            "data_zwrotu": rental.data_zwrotu.strftime("%Y-%m-%d"),
        }
        rental_list.append(rental_data)
    return jsonify(rental_list), 200

@app.route("/rentals", methods=["POST"])
def create_rental():
    data = request.json
    rental_date = datetime.strptime(data.get("data_wypozyczenia"), "%Y-%m-%d")
    datazwrotu = rental_date + timedelta(weeks=1)
    # Sprawdzamy, czy użytkownik próbuje wypożyczyć więcej książek niż jest dostępnych kopii
    usr = db.session.query(Użytkownik).get(data.get("id_uzytkownika"))
    print(usr.id_uzytkownika)
    book = db.session.query(Książka).get(data.get("id_ksiazki"))
    if book.liczba_dostepnych_kopii <= 0:
        return jsonify({"message": "Book is not available for rental!"}), 400
    
    if usr.stan_konta <= 0:
        return jsonify({"message": "Brak srodkow!"}), 200

    # Tworzymy nowe wypożyczenie
    new_rental = Wypożyczenie(
        id_ksiazki=data.get("id_ksiazki"),
        id_uzytkownika=data.get("id_uzytkownika"),
        data_wypozyczenia=rental_date,
        data_zwrotu=datazwrotu
    )
    
    # Zmniejszamy liczbę dostępnych kopii książki
    usr.stan_konta -= 1
    book.liczba_dostepnych_kopii -= 1
    db.session.add(new_rental)
    db.session.commit()
    print("Liczba dostępnych kopii po zmianie2:", book.liczba_dostepnych_kopii)
    return jsonify({"message": "Rental created!"}), 201

@app.route("/books", methods=["GET"])
def get_books():
    books = Książka.query.all()
    books_list = []
    for book in books:
        book_data = {
            "id": book.id_ksiazki,
            "tytul": book.tytul,
            "autor": book.autor,
            "kategoria": book.kategoria,
            "liczba_dostepnych_kopii": book.liczba_dostepnych_kopii,
            "rok_wydania": book.rok_wydania,
        }
        books_list.append(book_data)
    return jsonify(books_list), 200



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
            "stan_konta": user.stan_konta
        }
    )









@app.route("/book/<int:id>", methods=["GET"])
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
