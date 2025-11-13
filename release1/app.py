from flask import Flask, render_template, request, redirect, url_for, flash, session
# --- MUDANÇA: Importar o novo model ---
from models import db, Jogador, Evento, Organizador, Inscricao 
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime

# --- Configuração do App (sem mudança) ---
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'sua-chave-secreta-aqui-pode-ser-qualquer-coisa'
db.init_app(app)

with app.app_context():
    db.create_all()

# --- Protetores de Rota (sem mudança) ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Você precisa estar logado para acessar esta página.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def organizador_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_type') != 'organizador':
            flash("Acesso negado. Apenas organizadores podem fazer isso.", "error")
            return redirect(url_for('lista_eventos'))
        return f(*args, **kwargs)
    return decorated_function

# --- Rotas Principais / Login (sem mudança) ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login_submit', methods=['POST'])
def login_submit():
    # ... (sem mudança) ...
    nome = request.form.get('nickname_login')
    senha = request.form.get('senha_login')
    usuario = Jogador.query.filter_by(nome=nome).first()
    tipo = 'jogador'
    if not usuario:
        usuario = Organizador.query.filter_by(nome=nome).first()
        tipo = 'organizador'
    if usuario and check_password_hash(usuario.senha, senha):
        session['user_id'] = usuario.id
        session['user_name'] = usuario.nome
        session['user_type'] = tipo
        flash(f'Login bem-sucedido como {usuario.nome}!', 'info')
        if tipo == 'organizador':
            return redirect(url_for('dashboard')) 
        else:
            return redirect(url_for('lista_eventos')) 
    else:
        flash('Nickname ou senha inválidos.', 'error')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    # ... (sem mudança) ...
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_type', None)
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('index'))

@app.route('/register', methods=['POST'])
def register():
    # ... (sem mudança) ...
    tipo_usuario = request.form.get('tipo_usuario')
    nome = request.form.get('nickname') 
    email = request.form.get('email')
    senha = request.form.get('senha')
    telefone = request.form.get('telefone')
    idade = request.form.get('idade')
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
    hashed_senha = generate_password_hash(senha)
    try:
        if tipo_usuario == 'jogador':
            novo_usuario = Jogador(nome=nome, email=email, senha=hashed_senha, telefone=telefone, idade=idade)
        elif tipo_usuario == 'organizador':
            novo_usuario = Organizador(nome=nome, email=email, senha=hashed_senha, telefone=telefone, idade=idade)
        else:
            flash("Erro: Tipo de usuário inválido.", "error")
            return redirect(url_for('login'))
        db.session.add(novo_usuario)
        db.session.commit()
        flash("Usuário criado com sucesso! Faça o login.", "info")
        return redirect(url_for('login'))
    except Exception as e:
        db.session.rollback()
        flash(f"Ocorreu um erro ao criar o usuário: {e}", "error")
        return redirect(url_for('login'))

# --- Rotas do Organizador (Dashboard) ---
@app.route('/dashboard')
@login_required
@organizador_required
def dashboard():
    # ... (sem mudança) ...
    org_id = session.get('user_id')
    eventos_ativos = Evento.query.filter_by(organizador_id=org_id, status='Ativo').order_by(Evento.data.asc()).all()
    eventos_finalizados = Evento.query.filter_by(organizador_id=org_id, status='Finalizado').order_by(Evento.data.desc()).all()
    return render_template(
        'dashboard.html', 
        eventos_ativos=eventos_ativos,
        eventos_finalizados=eventos_finalizados,
        user_session=session
    )

@app.route('/evento/criar')
@login_required
@organizador_required
def criar_evento():
    # ... (sem mudança) ...
    return render_template('criar_evento.html')

# --- CRUD Jogadores (sem mudança, rotas ocultas) ---
@app.route('/jogadores')
@login_required 
def lista_jogadores():
    jogadores = Jogador.query.all()
    return render_template('jogador.html', jogadores=jogadores)
@app.route('/jogador/novo', methods=['POST'])
@login_required 
@organizador_required 
def novo_jogador():
    nome = request.form.get('nome')
    email = request.form.get('email')
    if Jogador.query.filter_by(nome=nome).first() or Organizador.query.filter_by(nome=nome).first():
        flash("Nickname já existe", "error")
        return redirect(url_for('lista_jogadores'))
    if Jogador.query.filter_by(email=email).first() or Organizador.query.filter_by(email=email).first():
        flash("Email já existe", "error")
        return redirect(url_for('lista_jogadores'))
    hashed_senha = generate_password_hash(request.form.get('senha'))
    jogador = Jogador(
        nome=nome, email=email, idade=request.form.get('idade'),
        telefone=request.form.get('telefone'), senha=hashed_senha
    )
    db.session.add(jogador)
    db.session.commit()
    return redirect(url_for('lista_jogadores'))
@app.route('/jogador/delete/<int:id>')
@login_required 
@organizador_required 
def excluir_jogador(id):
    jogador = Jogador.query.filter_by(id=id).first() 
    if jogador:
        db.session.delete(jogador)
        db.session.commit()
    return redirect(url_for('lista_jogadores'))

# -----------------------------
# --- ROTAS DE EVENTO E INSCRIÇÃO ---
# -----------------------------

@app.route('/evento/detalhe/<int:id>')
@login_required
def evento_detalhe(id):
    evento = Evento.query.get_or_404(id)
    
    # --- MUDANÇA: Checar se o jogador já está inscrito ---
    is_inscrito = False # Começa como falso
    if session.get('user_type') == 'jogador':
        jogador_id = session.get('user_id')
        # Procura no banco se a combinação jogador+evento existe
        inscricao = Inscricao.query.filter_by(jogador_id=jogador_id, evento_id=evento.id).first()
        if inscricao:
            is_inscrito = True # Se achou, marca como verdadeiro
            
    return render_template(
        'evento_detalhe.html', 
        evento=evento, 
        user_session=session,
        is_inscrito=is_inscrito # Passa a informação (True/False) para o template
    )

@app.route('/evento/encerrar/<int:id>')
@login_required
@organizador_required
def encerrar_evento(id):
    # ... (sem mudança) ...
    evento = Evento.query.get_or_404(id)
    if evento.organizador_id != session.get('user_id'):
        flash("Acesso negado. Você não é o dono deste evento.", "error")
        return redirect(url_for('lista_eventos'))
    evento.status = 'Finalizado'
    db.session.commit()
    flash(f'O evento "{evento.nome}" foi marcado como finalizado.', 'info')
    return redirect(url_for('dashboard')) 


@app.route('/eventos')
@login_required 
def lista_eventos():
    # ... (sem mudança) ...
    eventos = Evento.query.filter_by(status='Ativo').order_by(Evento.data.asc()).all() 
    return render_template('evento.html', eventos=eventos, user_session=session)

@app.route('/evento/novo', methods=['POST'])
@login_required 
@organizador_required 
def novo_evento():
    # ... (sem mudança) ...
    org_id = session.get('user_id')
    data_string = request.form['data'] 
    data_objeto = None
    if data_string:
        try:
            data_objeto = datetime.strptime(data_string, '%Y-%m-%d').date()
        except ValueError:
            flash("Formato de data inválido. Use AAAA-MM-DD.", "error")
            return redirect(url_for('criar_evento'))
    evento = Evento(
        nome=request.form['nome'],
        jogo=request.form['jogo'],
        data=data_objeto, 
        limite_jogadores=request.form['limite_jogadores'],
        faixa_etaria=request.form['faixa_etaria'],
        local=request.form['local'],
        organizador_id=org_id 
    )
    db.session.add(evento)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/evento/delete/<int:id>')
@login_required 
@organizador_required 
def excluir_evento(id):
    # ... (sem mudança) ...
    evento = Evento.query.filter_by(id=id).first() 
    if evento:
        if evento.organizador_id != session.get('user_id'):
            flash("Acesso negado. Você não é o dono deste evento.", "error")
            return redirect(url_for('lista_eventos'))
        db.session.delete(evento)
        db.session.commit()
    if request.referrer and 'dashboard' in request.referrer:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('lista_eventos'))

# ------------------------------------
# --- MUDANÇA: NOVAS ROTAS DO JOGADOR ---
# ------------------------------------

@app.route('/evento/inscrever/<int:id>')
@login_required
def inscrever(id):
    # 1. Checa se o usuário é um Jogador (como você pediu!)
    if session.get('user_type') != 'jogador':
        flash("Apenas jogadores podem se inscrever em eventos.", "error")
        return redirect(url_for('evento_detalhe', id=id))

    evento = Evento.query.get_or_404(id)
    jogador_id = session.get('user_id')

    # 2. Checa se o evento ainda está Ativo
    if evento.status != 'Ativo':
        flash("Este evento não está mais aceitando inscrições.", "error")
        return redirect(url_for('evento_detalhe', id=id))

    # 3. Checa se ele já não está inscrito
    inscricao_existente = Inscricao.query.filter_by(jogador_id=jogador_id, evento_id=evento.id).first()
    if inscricao_existente:
        flash("Você já está inscrito neste evento.", "info")
        return redirect(url_for('evento_detalhe', id=id))
        
    # 4. (Opcional, mas bom) Checar limite de jogadores
    if evento.limite_jogadores:
        # Conta quantas inscrições o evento já tem
        total_inscritos = Inscricao.query.filter_by(evento_id=evento.id).count()
        if total_inscritos >= evento.limite_jogadores:
            flash("Inscrições esgotadas! O limite de jogadores foi atingido.", "error")
            return redirect(url_for('evento_detalhe', id=id))

    # 5. Se tudo estiver OK, cria a inscrição
    nova_inscricao = Inscricao(jogador_id=jogador_id, evento_id=evento.id)
    db.session.add(nova_inscricao)
    db.session.commit()

    flash(f'Inscrição confirmada no evento "{evento.nome}"!', 'info')
    return redirect(url_for('evento_detalhe', id=id))


@app.route('/evento/cancelar/<int:id>')
@login_required
def cancelar_inscricao(id):
    # 1. Checa se é jogador
    if session.get('user_type') != 'jogador':
        flash("Apenas jogadores podem cancelar inscrições.", "error")
        return redirect(url_for('evento_detalhe', id=id))

    evento = Evento.query.get_or_404(id)
    jogador_id = session.get('user_id')

    # 2. Encontra a inscrição
    inscricao = Inscricao.query.filter_by(jogador_id=jogador_id, evento_id=evento.id).first()
    
    # 3. Se ela existir, apaga
    if inscricao:
        db.session.delete(inscricao)
        db.session.commit()
        flash("Sua inscrição foi cancelada.", "info")
    else:
        flash("Você não estava inscrito neste evento.", "error")

    return redirect(url_for('evento_detalhe', id=id))

# --- Comando para Rodar o App ---
if __name__ == '__main__':
    app.run(debug=True)