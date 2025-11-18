from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, Jogador, Evento, Organizador, Inscricao, Partida
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import math

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'sua-chave-secreta-aqui-pode-ser-qualquer-coisa'
db.init_app(app)

with app.app_context():
    db.create_all()

# --- Protetores ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Você precisa estar logado.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def organizador_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_type') != 'organizador':
            flash("Acesso negado.", "error")
            return redirect(url_for('lista_eventos'))
        return f(*args, **kwargs)
    return decorated_function

# --- Rotas Básicas ---
@app.route('/')
def index(): return render_template('index.html')
@app.route('/login')
def login(): return render_template('login.html')
@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu.', 'info')
    return redirect(url_for('index'))

@app.route('/login_submit', methods=['POST'])
def login_submit():
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
        flash(f'Bem-vindo, {usuario.nome}!', 'info')
        if tipo == 'organizador': return redirect(url_for('dashboard')) 
        else: return redirect(url_for('lista_eventos')) 
    else:
        flash('Dados inválidos.', 'error')
        return redirect(url_for('login'))

@app.route('/register', methods=['POST'])
def register():
    tipo = request.form.get('tipo_usuario')
    nome = request.form.get('nickname') 
    email = request.form.get('email')
    senha = request.form.get('senha')
    telefone = request.form.get('telefone')
    idade = request.form.get('idade')
    if Jogador.query.filter_by(nome=nome).first() or Organizador.query.filter_by(nome=nome).first():
        flash("Nickname já existe.", "error")
        return redirect(url_for('login'))
    hashed = generate_password_hash(senha)
    try:
        if tipo == 'jogador': u = Jogador(nome=nome, email=email, senha=hashed, telefone=telefone, idade=idade)
        else: u = Organizador(nome=nome, email=email, senha=hashed, telefone=telefone, idade=idade)
        db.session.add(u)
        db.session.commit()
        flash("Conta criada! Faça login.", "info")
    except Exception as e: flash(f"Erro: {e}", "error")
    return redirect(url_for('login'))

# --- Dashboard/Eventos ---
@app.route('/dashboard')
@login_required
@organizador_required
def dashboard():
    org_id = session.get('user_id')
    ativos = Evento.query.filter_by(organizador_id=org_id, status='Ativo').order_by(Evento.data.asc()).all()
    finalizados = Evento.query.filter_by(organizador_id=org_id, status='Finalizado').order_by(Evento.data.desc()).all()
    return render_template('dashboard.html', eventos_ativos=ativos, eventos_finalizados=finalizados, user_session=session)

@app.route('/evento/criar')
@login_required
@organizador_required
def criar_evento(): return render_template('criar_evento.html')

@app.route('/eventos')
@login_required 
def lista_eventos():
    eventos = Evento.query.filter_by(status='Ativo').order_by(Evento.data.asc()).all() 
    return render_template('evento.html', eventos=eventos, user_session=session)

@app.route('/evento/novo', methods=['POST'])
@login_required 
@organizador_required 
def novo_evento():
    try:
        data = datetime.strptime(request.form['data'], '%Y-%m-%d').date() if request.form['data'] else None
        hora = datetime.strptime(request.form['horario'], '%H:%M').time() if request.form['horario'] else None
    except:
        flash("Data/Hora inválida.", "error")
        return redirect(url_for('criar_evento'))
    
    # MUDANÇA: Pegar o número de vagas do mata-mata
    vagas = int(request.form.get('vagas_mata_mata', 4))
    
    e = Evento(
        nome=request.form['nome'], jogo=request.form['jogo'], data=data, horario=hora,
        descricao=request.form['descricao'], link_externo=request.form['link_externo'],
        limite_jogadores=request.form['limite_jogadores'], faixa_etaria=request.form['faixa_etaria'],
        local=request.form['local'], organizador_id=session.get('user_id'),
        vagas_mata_mata=vagas # Salva a configuração
    )
    db.session.add(e)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/evento/detalhe/<int:id>')
@login_required
def evento_detalhe(id):
    evento = Evento.query.get_or_404(id)
    is_inscrito = False
    if session.get('user_type') == 'jogador':
        if Inscricao.query.filter_by(jogador_id=session.get('user_id'), evento_id=evento.id).first():
            is_inscrito = True
    return render_template('evento_detalhe.html', evento=evento, user_session=session, is_inscrito=is_inscrito)

@app.route('/evento/inscrever/<int:id>')
@login_required
def inscrever(id):
    if session.get('user_type') != 'jogador': return redirect(url_for('evento_detalhe', id=id))
    e = Evento.query.get_or_404(id)
    uid = session.get('user_id')
    if e.status != 'Ativo':
        flash("Evento encerrado.", "error")
        return redirect(url_for('evento_detalhe', id=id))
    if Inscricao.query.filter_by(jogador_id=uid, evento_id=id).first(): return redirect(url_for('evento_detalhe', id=id))
    if e.limite_jogadores and Inscricao.query.filter_by(evento_id=id).count() >= e.limite_jogadores:
        flash("Vagas esgotadas.", "error")
        return redirect(url_for('evento_detalhe', id=id))
    db.session.add(Inscricao(jogador_id=uid, evento_id=id))
    db.session.commit()
    flash("Inscrito com sucesso!", "info")
    return redirect(url_for('evento_detalhe', id=id))

@app.route('/evento/cancelar/<int:id>')
@login_required
def cancelar_inscricao(id):
    i = Inscricao.query.filter_by(jogador_id=session.get('user_id'), evento_id=id).first()
    if i:
        db.session.delete(i)
        db.session.commit()
        flash("Inscrição cancelada.", "info")
    return redirect(url_for('evento_detalhe', id=id))

# --- Gestão Avançada ---

@app.route('/evento/inscricoes/<int:id>')
@login_required
def gerenciar_inscricoes(id):
    e = Evento.query.get_or_404(id)
    if e.fase_atual == 'Mata-Mata':
        return redirect(url_for('visualizar_chaves', id=id))
    if session.get('user_type') == 'organizador' and e.organizador_id != session.get('user_id'):
         return redirect(url_for('dashboard'))
    inscricoes = Inscricao.query.filter_by(evento_id=id).order_by(Inscricao.pontos.desc()).all()
    return render_template('gerenciar_inscricoes.html', evento=e, inscricoes=inscricoes, total_inscritos=len(inscricoes))

@app.route('/inscricao/pontuar/<int:id>', methods=['POST'])
@login_required
@organizador_required
def pontuar_inscricao(id):
    i = Inscricao.query.get_or_404(id)
    if i.evento.organizador_id != session.get('user_id'): return redirect(url_for('dashboard'))
    try:
        i.pontos = int(request.form.get('pontos'))
        db.session.commit()
    except: flash("Erro ao salvar pontos.", "error")
    return redirect(url_for('gerenciar_inscricoes', id=i.evento_id))

# --- GERADOR DE CHAVES DINÂMICO (A MÁGICA) ---
@app.route('/evento/gerar_mata_mata/<int:id>')
@login_required
@organizador_required
def gerar_mata_mata(id):
    e = Evento.query.get_or_404(id)
    if e.organizador_id != session.get('user_id'): return redirect(url_for('dashboard'))
    
    vagas = e.vagas_mata_mata # Ex: 4, 8, 16...
    
    # 1. Pega os X melhores ativos
    top_inscricoes = Inscricao.query.filter_by(evento_id=id, status_participacao='Ativo')\
                                   .order_by(Inscricao.pontos.desc()).limit(vagas).all()
    
    if len(top_inscricoes) < vagas:
        flash(f"Você precisa de pelo menos {vagas} jogadores ativos para gerar a chave.", "error")
        return redirect(url_for('gerenciar_inscricoes', id=id))
        
    # 2. Algoritmo de Criação da Árvore (Do Final para o Início)
    # Exemplo para 4 jogadores:
    # Nível 0: Final (1 jogo)
    # Nível 1: Semis (2 jogos) -> Alimentam a Final
    
    # Vamos criar "rodadas".
    # rodada_final (1 jogo)
    # rodada_semi (2 jogos)
    # rodada_quartas (4 jogos)
    
    total_rodadas = int(math.log2(vagas)) # Ex: log2(8) = 3 rodadas
    proximas_partidas = [] # Lista de partidas da rodada "de cima" para linkar
    
    partidas_criadas = []
    ordem_global = 100 # Para ordenar visualmente
    
    # Loop reverso: Cria a Final, depois as Semis, depois as Quartas...
    for r in range(total_rodadas):
        # r=0 -> Final (1 jogo)
        # r=1 -> Semis (2 jogos)
        qtd_jogos_na_rodada = 2**r
        jogos_dessa_rodada = []
        
        nome_rodada = "Eliminatória"
        if r == 0: nome_rodada = "Grande Final"
        elif r == 1: nome_rodada = "Semifinais"
        elif r == 2: nome_rodada = "Quartas de Final"
        elif r == 3: nome_rodada = "Oitavas de Final"
        
        for i in range(qtd_jogos_na_rodada):
            # Se r>0 (não é a final), precisamos saber pra onde o vencedor vai
            # O vencedor do jogo 'i' e 'i+1' da rodada atual vão para o jogo 'i//2' da rodada anterior
            prox_id = None
            if r > 0:
                # Pega o ID da partida "pai" (que criamos no loop anterior)
                index_pai = i // 2
                prox_id = proximas_partidas[index_pai].id
            
            partida = Partida(
                evento_id=id,
                rodada=nome_rodada,
                ordem=ordem_global, # Ordem decrescente para exibir Final no fim da lista
                proxima_partida_id=prox_id
            )
            db.session.add(partida)
            db.session.flush() # Garante que o ID seja gerado agora
            
            jogos_dessa_rodada.append(partida)
            partidas_criadas.append(partida)
            ordem_global -= 1
            
        # As partidas criadas agora viram as "próximas" para o próximo loop
        proximas_partidas = jogos_dessa_rodada

    # 3. Preencher a Primeira Rodada (A última criada no loop) com os Jogadores
    # A lista 'proximas_partidas' agora contém os jogos da PRIMEIRA RODADA (ex: Quartas)
    primeira_rodada = proximas_partidas 
    
    # Ordenação Seed (1º vs Último, 2º vs Penúltimo...)
    # Exemplo 8 vagas: Jogo A (1 vs 8), Jogo B (4 vs 5), Jogo C (2 vs 7), Jogo D (3 vs 6)
    # Para simplificar e não bugar a cabeça: Vamos fazer pareamento sequencial nas chaves
    # Jogo 1: 1º vs 2º (Para simplificar visualização)
    # OU Pareamento Olímpico Simples:
    # Lista: [1, 2, 3, 4, 5, 6, 7, 8]
    # Match 1: 1 vs 8
    # Match 2: 2 vs 7 ...
    
    # Vamos usar pareamento olímpico clássico (1 vs N)
    qtd_jogos = len(primeira_rodada)
    
    for i in range(qtd_jogos):
        partida = primeira_rodada[i]
        
        # Topo da lista
        jogador_top = top_inscricoes[i].jogador_id 
        # Fundo da lista
        jogador_bottom = top_inscricoes[vagas - 1 - i].jogador_id
        
        partida.jogador1_id = jogador_top
        partida.jogador2_id = jogador_bottom
    
    db.session.commit()
    
    e.fase_atual = 'Mata-Mata'
    db.session.commit()
    
    flash(f"Chaves geradas com sucesso para {vagas} jogadores!", "info")
    return redirect(url_for('visualizar_chaves', id=id))

@app.route('/evento/chaves/<int:id>')
@login_required
def visualizar_chaves(id):
    e = Evento.query.get_or_404(id)
    # Ordena por ordem crescente (criamos decrescente, entao invertemos pra mostrar da 1a rodada pra final)
    partidas = Partida.query.filter_by(evento_id=id).order_by(Partida.id.desc()).all()
    return render_template('chaves.html', evento=e, partidas=partidas, user_session=session)

@app.route('/partida/vencedor/<int:partida_id>/<int:vencedor_id>')
@login_required
@organizador_required
def definir_vencedor(partida_id, vencedor_id):
    partida = Partida.query.get_or_404(partida_id)
    evento = partida.evento
    if evento.organizador_id != session.get('user_id'): return redirect(url_for('dashboard'))
    
    partida.vencedor_id = vencedor_id
    db.session.commit()
    
    # --- LÓGICA DE AVANÇO DINÂMICA ---
    if partida.proxima_partida_id:
        prox = Partida.query.get(partida.proxima_partida_id)
        if prox:
            # Preenche o primeiro slot vazio que achar
            if prox.jogador1_id is None:
                prox.jogador1_id = vencedor_id
            elif prox.jogador2_id is None:
                prox.jogador2_id = vencedor_id
            db.session.commit()
            flash("Vencedor avançou para a próxima fase!", "info")
    else:
        # Se não tem próxima partida, é a FINAL
        flash(f"Temos um campeão! O evento {evento.nome} foi concluído.", "info")

    return redirect(url_for('visualizar_chaves', id=evento.id))

@app.route('/evento/delete/<int:id>')
@login_required 
@organizador_required 
def excluir_evento(id):
    evento = Evento.query.filter_by(id=id).first() 
    if evento:
        if evento.organizador_id != session.get('user_id'): return redirect(url_for('lista_eventos'))
        Partida.query.filter_by(evento_id=id).delete()
        Inscricao.query.filter_by(evento_id=id).delete()
        db.session.delete(evento)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/evento/encerrar/<int:id>')
@login_required
@organizador_required
def encerrar_evento(id):
    evento = Evento.query.get_or_404(id)
    if evento.organizador_id != session.get('user_id'): return redirect(url_for('lista_eventos'))
    evento.status = 'Finalizado'
    db.session.commit()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)