from flask_sqlalchemy import SQLAlchemy

# Inicializa a extensão do banco de dados
db = SQLAlchemy()

# Modelo do Jogador (atualizado)
class Jogador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Vamos usar 'nome' para salvar o 'nickname'
    nome = db.Column(db.String(100), unique=True, nullable=False) 
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False) # String maior para o hash
    telefone = db.Column(db.String(20))
    idade = db.Column(db.Integer)

    def __repr__(self):
        return f'<Jogador {self.nome}>'

# --- NOSSO NOVO MODELO ---
# Modelo do Organizador
class Organizador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Também usa 'nome' para salvar o 'nickname'
    nome = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False) # String maior para o hash
    telefone = db.Column(db.String(20))
    idade = db.Column(db.Integer)

    def __repr__(self):
        return f'<Organizador {self.nome}>'

# Modelo do Evento (como estava antes)
class Evento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    jogo = db.Column(db.String(100))
    data = db.Column(db.String(50)) # Mantido como string por enquanto
    limite_jogadores = db.Column(db.Integer)
    faixa_etaria = db.Column(db.String(50))
    local = db.Column(db.String(100))

    def __repr__(self):
        return f'<Evento {self.nome}>'