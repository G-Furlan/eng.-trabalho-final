from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# Modelo do Jogador (sem mudanças)
class Jogador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False) 
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    telefone = db.Column(db.String(20))
    idade = db.Column(db.Integer)

# Modelo do Organizador (sem mudanças)
class Organizador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False) 
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    telefone = db.Column(db.String(20))
    idade = db.Column(db.Integer)

# Modelo do Evento (sem mudanças)
class Evento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    jogo = db.Column(db.String(100))
    data = db.Column(db.Date, nullable=True) 
    limite_jogadores = db.Column(db.Integer)
    faixa_etaria = db.Column(db.String(50))
    local = db.Column(db.String(100))
    status = db.Column(db.String(50), nullable=False, default='Ativo')
    organizador_id = db.Column(db.Integer, db.ForeignKey('organizador.id'), nullable=False)
    organizador = db.relationship('Organizador', backref=db.backref('eventos', lazy=True))

# ------------------------------------
# --- MUDANÇA: NOSSA NOVA TABELA ---
# ------------------------------------
class Inscricao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Link para o Jogador que se inscreveu
    jogador_id = db.Column(db.Integer, db.ForeignKey('jogador.id'), nullable=False)
    # Link para o Evento em que ele se inscreveu
    evento_id = db.Column(db.Integer, db.ForeignKey('evento.id'), nullable=False)
    
    # Relações virtuais (para facilitar as buscas)
    jogador = db.relationship('Jogador', backref=db.backref('inscricoes', lazy=True))
    evento = db.relationship('Evento', backref=db.backref('inscricoes', lazy=True))