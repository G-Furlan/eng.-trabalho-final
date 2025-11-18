from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Jogador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False) 
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    telefone = db.Column(db.String(20))
    idade = db.Column(db.Integer)

class Organizador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False) 
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    telefone = db.Column(db.String(20))
    idade = db.Column(db.Integer)

class Evento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    jogo = db.Column(db.String(100))
    data = db.Column(db.Date, nullable=True)
    horario = db.Column(db.Time, nullable=True) 
    descricao = db.Column(db.Text, nullable=True) 
    link_externo = db.Column(db.String(200), nullable=True)
    limite_jogadores = db.Column(db.Integer)
    faixa_etaria = db.Column(db.String(50))
    local = db.Column(db.String(100))
    status = db.Column(db.String(50), nullable=False, default='Ativo')
    
    # Controle de Fases
    fase_atual = db.Column(db.String(50), default='Classificatoria') 
    # --- NOVO: Número de vagas para a chave (4, 8, 16...) ---
    vagas_mata_mata = db.Column(db.Integer, default=4) 
    
    organizador_id = db.Column(db.Integer, db.ForeignKey('organizador.id'), nullable=False)
    organizador = db.relationship('Organizador', backref=db.backref('eventos', lazy=True))

class Inscricao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jogador_id = db.Column(db.Integer, db.ForeignKey('jogador.id'), nullable=False)
    evento_id = db.Column(db.Integer, db.ForeignKey('evento.id'), nullable=False)
    pontos = db.Column(db.Integer, default=0)
    status_participacao = db.Column(db.String(50), default='Ativo') 
    jogador = db.relationship('Jogador', backref=db.backref('inscricoes', lazy=True))
    evento = db.relationship('Evento', backref=db.backref('inscricoes', lazy=True))

class Partida(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    evento_id = db.Column(db.Integer, db.ForeignKey('evento.id'), nullable=False)
    
    jogador1_id = db.Column(db.Integer, db.ForeignKey('jogador.id'), nullable=True)
    jogador2_id = db.Column(db.Integer, db.ForeignKey('jogador.id'), nullable=True)
    vencedor_id = db.Column(db.Integer, db.ForeignKey('jogador.id'), nullable=True)
    
    rodada = db.Column(db.String(50)) 
    ordem = db.Column(db.Integer) 
    
    # --- NOVO: Link para a próxima fase ---
    # Se eu ganhar essa partida, vou para qual partida?
    proxima_partida_id = db.Column(db.Integer, db.ForeignKey('partida.id'), nullable=True)
    
    # Relacionamentos
    jogador1 = db.relationship('Jogador', foreign_keys=[jogador1_id])
    jogador2 = db.relationship('Jogador', foreign_keys=[jogador2_id])
    vencedor = db.relationship('Jogador', foreign_keys=[vencedor_id])
    evento = db.relationship('Evento', backref=db.backref('partidas', lazy=True))
    # Permite acessar a partida "pai"
    proxima_partida = db.relationship('Partida', remote_side=[id])