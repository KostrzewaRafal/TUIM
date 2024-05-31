from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Książka(db.Model):
    __tablename__ = "ksiazka"
    __table_args__ = {"schema": "biblioteka"}
    id_ksiazki = db.Column(db.Integer, primary_key=True)
    tytul = db.Column(db.String(60))
    autor = db.Column(db.String(50))
    kategoria = db.Column(db.String(25))
    liczba_dostepnych_kopii = db.Column(db.Integer)
    rok_wydania = db.Column(db.Integer)


class Użytkownik(db.Model):
    __tablename__ = "uzytkownicy"
    __table_args__ = {"schema": "biblioteka"}
    id_uzytkownika = db.Column(db.Integer, primary_key=True)
    imie = db.Column(db.String(15))
    nazwisko = db.Column(db.String(20))
    email = db.Column(db.String(30), unique=True)
    haslo = db.Column(db.String(100))
    stan_konta = db.Column(db.Integer)


class Wypożyczenie(db.Model):
    __tablename__ = "wypozyczenia"
    __table_args__ = {"schema": "biblioteka"}
    id_wypozyczenia = db.Column(db.Integer, primary_key=True)
    id_ksiazki = db.Column(db.Integer, db.ForeignKey("biblioteka.ksiazka.id_ksiazki"))
    id_uzytkownika = db.Column(
        db.Integer, db.ForeignKey("biblioteka.uzytkownicy.id_uzytkownika")
    )
    data_wypozyczenia = db.Column(db.Date)
    data_zwrotu = db.Column(db.Date)

    książka = db.relationship("Książka", backref=db.backref("wypożyczenia", lazy=True))
    użytkownik = db.relationship(
        "Użytkownik", backref=db.backref("wypożyczenia", lazy=True)
    )
