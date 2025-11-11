from flask import Flask, render_template, request, redirect, url_for
from models import db, Jogador, Evento

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
	db.create_all()

# Página inicial
# Página inicial
@app.route('/')
def index():
	return render_template('index.html')

# -----------------------------
# CRUD Jogadores
# -----------------------------
@app.route('/jogadores')
def lista_jogadores():
	jogadores = Jogador.query.all()
	return render_template('jogador.html', jogadores=jogadores)

@app.route('/jogador/novo', methods=['POST'])
def novo_jogador():
	jogador = Jogador(
		nome=request.form['nome'],
		email=request.form['email'],
		idade=request.form['idade'],
		telefone=request.form['telefone'],
		senha=request.form['senha']
	)
	db.session.add(jogador)
	db.session.commit()
	return redirect(url_for('lista_jogadores'))

@app.route('/jogador/delete/<int:id>')
def excluir_jogador(id):
	jogador = Jogador.query.get(id)
	db.session.delete(jogador)
	db.session.commit()
	return redirect(url_for('lista_jogadores'))

# -----------------------------
# CRUD Eventos
# -----------------------------
@app.route('/eventos')
def lista_eventos():
	eventos = Evento.query.all()
	return render_template('evento.html', eventos=eventos)

@app.route('/evento/novo', methods=['POST'])
def novo_evento():
	evento = Evento(
		nome=request.form['nome'],
		jogo=request.form['jogo'],
		data=request.form['data'],
		limite_jogadores=request.form['limite_jogadores'],
		faixa_etaria=request.form['faixa_etaria'],
		local=request.form['local']
	)
	db.session.add(evento)
	db.session.commit()
	return redirect(url_for('lista_eventos'))

@app.route('/evento/delete/<int:id>')
def excluir_evento(id):
	evento = Evento.query.get(id)
	db.session.delete(evento)
	db.session.commit()
	return redirect(url_for('lista_eventos'))

if __name__ == '__main__':
	app.run(debug=True)
