from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Jogador(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	nome = db.Column(db.String(100), nullable=False)
	email = db.Column(db.String(100), unique=True, nullable=False)
	idade = db.Column(db.String(10))
	telefone = db.Column(db.String(15))
	senha = db.Column(db.String(50))

class Evento(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	nome = db.Column(db.String(100), nullable=False)
	jogo = db.Column(db.String(100), nullable=False)
	data = db.Column(db.String(10))
	limite_jogadores = db.Column(db.Integer)
	faixa_etaria = db.Column(db.String(20))
	local = db.Column(db.String(100))
