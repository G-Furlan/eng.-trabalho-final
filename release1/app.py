from flask import Flask, render_template, request, redirect, url_for, flash, session
# Importe o 'db' e TODOS os modelos
from models import db, Jogador, Evento, Organizador
# Importe as funções para proteger e checar a senha
from werkzeug.security import generate_password_hash, check_password_hash

# --- Configuração do App ---
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Precisamos de uma "secret_key" para usar 'flash' (mensagens de erro) e 'session'
app.config['SECRET_KEY'] = 'sua-chave-secreta-aqui-pode-ser-qualquer-coisa'

# Inicializa o banco de dados com o app
db.init_app(app)

# Cria o banco de dados (se ele não existir)
with app.app_context():
    db.create_all()

# --- Rotas Principais / Landing Page ---

# A Rota '/' agora é a sua Landing Page
@app.route('/')
def index():
    return render_template('index.html')

# Rota para a página de Login/Cadastro
@app.route('/login')
def login():
    return render_template('login.html')

# --- NOSSA NOVA ROTA DE AUTENTICAÇÃO (LOGIN) ---
@app.route('/login_submit', methods=['POST'])
def login_submit():
    # 1. Pega os dados do form de LOGIN
    nome = request.form.get('nickname_login')
    senha = request.form.get('senha_login')

    # 2. Procura o usuário (em ambas as tabelas)
    usuario = Jogador.query.filter_by(nome=nome).first()
    tipo = 'jogador'

    if not usuario:
        usuario = Organizador.query.filter_by(nome=nome).first()
        tipo = 'organizador'

    # 3. Verifica a senha
    if usuario and check_password_hash(usuario.senha, senha):
        # Se o usuário existe E a senha bate:
        session['user_id'] = usuario.id
        session['user_name'] = usuario.nome
        session['user_type'] = tipo
        flash(f'Login bem-sucedido como {usuario.nome}!', 'info')
        # Redireciona para a lista de eventos (nossa "área logada")
        return redirect(url_for('lista_eventos'))
    else:
        # Se o usuário não existe OU a senha está errada:
        flash('Nickname ou senha inválidos.', 'error')
        return redirect(url_for('login'))

# --- Rota de Logout ---
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_type', None)
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('index'))

# Rota QUE VAI RECEBER os dados do formulário de cadastro (AGORA COMPLETA)
@app.route('/register', methods=['POST'])
def register():
    # 1. Pegar os dados do formulário
    tipo_usuario = request.form.get('tipo_usuario')
    # Mapeando o 'nickname' do form para o 'nome' do banco
    nome = request.form.get('nickname') 
    email = request.form.get('email')
    senha = request.form.get('senha')
    telefone = request.form.get('telefone')
    idade = request.form.get('idade')

    # 2. Validar dados (Verificar se já existem)
    # Checa nas DUAS tabelas
    jogador_existe = Jogador.query.filter_by(nome=nome).first()
    org_existe = Organizador.query.filter_by(nome=nome).first()
    if jogador_existe or org_existe:
        flash("Erro: Esse nickname já está em uso.", "error")
        return redirect(url_for('login'))

    email_jogador_existe = Jogador.query.filter_by(email=email).first()
    email_org_existe = Organizador.query.filter_by(email=email).first()
    if email_jogador_existe or email_org_existe:
        flash("Erro: Esse email já está em uso.", "error")
        return redirect(url_for('login'))

    # 3. Proteger a senha (Hashing)
    # Nunca salve a senha pura!
    hashed_senha = generate_password_hash(senha)

    # 4. Criar o usuário no tipo correto
    try:
        if tipo_usuario == 'jogador':
            novo_usuario = Jogador(
                nome=nome,
                email=email,
                senha=hashed_senha,
                telefone=telefone,
                idade=idade
            )
        elif tipo_usuario == 'organizador':
            novo_usuario = Organizador(
                nome=nome,
                email=email,
                senha=hashed_senha,
                telefone=telefone,
                idade=idade
            )
        else:
            flash("Erro: Tipo de usuário inválido.", "error")
            return redirect(url_for('login'))

        # 5. Salvar no banco
        db.session.add(novo_usuario)
        db.session.commit()

        flash("Usuário criado com sucesso! Faça o login.", "info")
        return redirect(url_for('login'))

    except Exception as e:
        db.session.rollback()
        flash(f"Ocorreu um erro ao criar o usuário: {e}", "error")
        return redirect(url_for('login'))


# -----------------------------
# CRUD Jogadores (Área interna)
# (Rotas originais)
# -----------------------------
@app.route('/jogadores')
def lista_jogadores():
    jogadores = Jogador.query.all()
    # Este template agora é da área interna
    return render_template('jogador.html', jogadores=jogadores)

@app.route('/jogador/novo', methods=['POST'])
def novo_jogador():
    # ATUALIZAÇÃO: Também vamos proteger a senha nesta rota antiga
    # (Embora ela não deva mais ser usada, é bom garantir)
    
    # Mapeando o 'nome' do form para o 'nome' do banco
    nome = request.form.get('nome')
    email = request.form.get('email')
    
    # Validar nickname e email (simplificado aqui)
    if Jogador.query.filter_by(nome=nome).first() or Organizador.query.filter_by(nome=nome).first():
        flash("Nickname já existe", "error")
        return redirect(url_for('lista_jogadores'))
    
    if Jogador.query.filter_by(email=email).first() or Organizador.query.filter_by(email=email).first():
        flash("Email já existe", "error")
        return redirect(url_for('lista_jogadores'))

    # Proteger a senha
    hashed_senha = generate_password_hash(request.form.get('senha'))
    
    jogador = Jogador(
        nome=nome,
        email=email,
        idade=request.form.get('idade'),
        telefone=request.form.get('telefone'),
        senha=hashed_senha # Salva a senha protegida
    )
    db.session.add(jogador)
    db.session.commit()
    return redirect(url_for('lista_jogadores'))

@app.route('/jogador/delete/<int:id>')
def excluir_jogador(id):
    jogador = Jogador.query.filter_by(id=id).first() # Mais seguro usar .first()
    if jogador:
        db.session.delete(jogador)
        db.session.commit()
    return redirect(url_for('lista_jogadores'))

# -----------------------------
# CRUD Eventos (Área interna)
# (Rotas originais)
# -----------------------------
@app.route('/eventos')
def lista_eventos():
    eventos = Evento.query.all()
    # Este template agora é da área interna
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
    evento = Evento.query.filter_by(id=id).first() # Mais seguro usar .first()
    if evento:
        db.session.delete(evento)
        db.session.commit()
    return redirect(url_for('lista_eventos'))

# --- Comando para Rodar o App ---
# (Essa parte estava faltando!)
if __name__ == '__main__':
    app.run(debug=True)