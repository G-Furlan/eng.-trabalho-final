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

# ... (MANTENHA TUDO ANTES) ...

@app.route('/eventos')
@login_required 
def lista_eventos():
    termo = request.args.get('q', '') # Pega o que foi digitado (ou vazio)
    
    query = Evento.query.filter_by(status='Ativo')
    
    if termo:
        # Filtra se o nome ou o jogo contiver o termo (ilike = ignora maiúscula/minúscula)
        query = query.filter(
            (Evento.nome.ilike(f'%{termo}%')) | 
            (Evento.jogo.ilike(f'%{termo}%'))
        )
        
    eventos = query.order_by(Evento.data.asc()).all() 
    
    return render_template('evento.html', eventos=eventos, user_session=session, termo_busca=termo)

# ... (MANTENHA TUDO DEPOIS) ...

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
    
    vagas = int(request.form.get('vagas_mata_mata', 4))
    
    e = Evento(
        nome=request.form['nome'], jogo=request.form['jogo'], data=data, horario=hora,
        descricao=request.form['descricao'], link_externo=request.form['link_externo'],
        limite_jogadores=request.form['limite_jogadores'], faixa_etaria=request.form['faixa_etaria'],
        local=request.form['local'], organizador_id=session.get('user_id'),
        vagas_mata_mata=vagas 
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
            
    # Se o evento acabou, tenta redirecionar pro relatório
    if evento.status == 'Finalizado':
        # Mas só se for organizador ou se quisermos mostrar pra todos (opcional)
        pass

    return render_template('evento_detalhe.html', evento=evento, user_session=session, is_inscrito=is_inscrito)

# --- Inscrições ---
@app.route('/evento/inscrever/<int:id>')
@login_required
def inscrever(id):
    if session.get('user_type') != 'jogador': return redirect(url_for('evento_detalhe', id=id))
    e = Evento.query.get_or_404(id)
    uid = session.get('user_id')
    
    if e.status != 'Ativo':
        flash("Evento encerrado.", "error")
        return redirect(url_for('evento_detalhe', id=id))
        
    if Inscricao.query.filter_by(jogador_id=uid, evento_id=id).first():
        return redirect(url_for('evento_detalhe', id=id))
        
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

# --- Gestão e Chaves ---

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

@app.route('/evento/gerar_mata_mata/<int:id>')
@login_required
@organizador_required
def gerar_mata_mata(id):
    e = Evento.query.get_or_404(id)
    if e.organizador_id != session.get('user_id'): return redirect(url_for('dashboard'))
    
    vagas = e.vagas_mata_mata 
    top_inscricoes = Inscricao.query.filter_by(evento_id=id, status_participacao='Ativo')\
                                   .order_by(Inscricao.pontos.desc()).limit(vagas).all()
    
    if len(top_inscricoes) < vagas:
        flash(f"Você precisa de pelo menos {vagas} jogadores ativos para gerar a chave.", "error")
        return redirect(url_for('gerenciar_inscricoes', id=id))
        
    total_rodadas = int(math.log2(vagas)) 
    proximas_partidas = [] 
    
    partidas_criadas = []
    ordem_global = 100 
    
    for r in range(total_rodadas):
        qtd_jogos_na_rodada = 2**r
        jogos_dessa_rodada = []
        
        nome_rodada = "Eliminatória"
        if r == 0: nome_rodada = "Grande Final"
        elif r == 1: nome_rodada = "Semifinais"
        elif r == 2: nome_rodada = "Quartas de Final"
        elif r == 3: nome_rodada = "Oitavas de Final"
        
        for i in range(qtd_jogos_na_rodada):
            prox_id = None
            if r > 0:
                index_pai = i // 2
                prox_id = proximas_partidas[index_pai].id
            
            partida = Partida(
                evento_id=id,
                rodada=nome_rodada,
                ordem=ordem_global,
                proxima_partida_id=prox_id
            )
            db.session.add(partida)
            db.session.flush() 
            
            jogos_dessa_rodada.append(partida)
            partidas_criadas.append(partida)
            ordem_global -= 1
            
        proximas_partidas = jogos_dessa_rodada

    primeira_rodada = proximas_partidas 
    qtd_jogos = len(primeira_rodada)
    
    for i in range(qtd_jogos):
        partida = primeira_rodada[i]
        jogador_top = top_inscricoes[i].jogador_id 
        jogador_bottom = top_inscricoes[vagas - 1 - i].jogador_id
        
        partida.jogador1_id = jogador_top
        partida.jogador2_id = jogador_bottom
    
    e.fase_atual = 'Mata-Mata'
    db.session.commit()
    
    flash(f"Chaves geradas com sucesso para {vagas} jogadores!", "info")
    return redirect(url_for('visualizar_chaves', id=id))

@app.route('/evento/chaves/<int:id>')
@login_required
def visualizar_chaves(id):
    e = Evento.query.get_or_404(id)
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
    
    if partida.proxima_partida_id:
        prox = Partida.query.get(partida.proxima_partida_id)
        if prox:
            if prox.jogador1_id is None:
                prox.jogador1_id = vencedor_id
            elif prox.jogador2_id is None:
                prox.jogador2_id = vencedor_id
            db.session.commit()
            flash("Vencedor avançou para a próxima fase!", "info")
    else:
        # --- MUDANÇA: FINALIZAR O TORNEIO AUTOMATICAMENTE ---
        flash(f"Temos um campeão! O evento {evento.nome} foi concluído.", "info")
        
        # 1. Atualiza o status da Inscrição do Campeão
        inscricao_campeao = Inscricao.query.filter_by(evento_id=evento.id, jogador_id=vencedor_id).first()
        if inscricao_campeao:
            inscricao_campeao.status_participacao = 'Vencedor'
            
        # 2. Finaliza o evento
        evento.status = 'Finalizado'
        db.session.commit()
        
        # Redireciona para o relatório final
        return redirect(url_for('relatorio_evento', id=evento.id))

    return redirect(url_for('visualizar_chaves', id=evento.id))

# --- NOVA ROTA: RELATÓRIO FINAL ---
@app.route('/evento/relatorio/<int:id>')
@login_required
def relatorio_evento(id):
    e = Evento.query.get_or_404(id)
    
    # Acha o campeão (quem venceu a Grande Final)
    final = Partida.query.filter_by(evento_id=id, rodada='Grande Final').first()
    campeao = None
    vice = None
    
    if final and final.vencedor:
        campeao = final.vencedor
        # O vice é o outro jogador da final que não venceu
        if final.jogador1_id == campeao.id:
            vice = final.jogador2
        else:
            vice = final.jogador1
            
    # Lista geral classificada por pontos (para o resto do ranking)
    ranking_geral = Inscricao.query.filter_by(evento_id=id).order_by(Inscricao.pontos.desc()).all()
    
    return render_template('relatorio_evento.html', evento=e, campeao=campeao, vice=vice, ranking=ranking_geral)

# --- Rota de Perfil ---
@app.route('/perfil')
@login_required
def perfil():
    user_id = session.get('user_id')
    tipo = session.get('user_type')
    
    user_data = None
    historico_ativo = []
    historico_passado = []
    
    if tipo == 'jogador':
        user_data = Jogador.query.get(user_id)
        inscricoes = Inscricao.query.filter_by(jogador_id=user_id).all()
        for i in inscricoes:
            if i.evento.status == 'Ativo': historico_ativo.append(i)
            else: historico_passado.append(i)
                
    elif tipo == 'organizador':
        user_data = Organizador.query.get(user_id)
        todos_eventos = Evento.query.filter_by(organizador_id=user_id).order_by(Evento.data.desc()).all()
        for e in todos_eventos:
            if e.status == 'Ativo': historico_ativo.append(e)
            else:
                campeao = Inscricao.query.filter_by(evento_id=e.id, status_participacao='Vencedor').first()
                e.campeao_nome = campeao.jogador.nome if campeao else "Indefinido"
                historico_passado.append(e)

    return render_template('perfil.html', 
                           usuario=user_data, 
                           tipo=tipo,
                           ativos=historico_ativo, 
                           passados=historico_passado)

# --- Utils ---
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

# ... (MANTENHA TODO O CÓDIGO ANTERIOR) ...

# --- ROTAS DE EDIÇÃO (ADICIONE ISSO ANTES DO if __name__) ---

@app.route('/evento/editar/<int:id>')
@login_required
@organizador_required
def editar_evento(id):
    evento = Evento.query.get_or_404(id)
    
    # Segurança: Só o dono edita
    if evento.organizador_id != session.get('user_id'):
        flash("Você não tem permissão para editar este evento.", "error")
        return redirect(url_for('dashboard'))
        
    return render_template('editar_evento.html', evento=evento)

@app.route('/evento/atualizar/<int:id>', methods=['POST'])
@login_required
@organizador_required
def atualizar_evento(id):
    evento = Evento.query.get_or_404(id)
    if evento.organizador_id != session.get('user_id'):
        return redirect(url_for('dashboard'))
        
    try:
        # Atualiza campos básicos
        evento.nome = request.form['nome']
        evento.jogo = request.form['jogo']
        evento.descricao = request.form['descricao']
        evento.link_externo = request.form['link_externo']
        evento.local = request.form['local']
        evento.faixa_etaria = request.form['faixa_etaria']
        
        # Atualiza Data/Hora
        if request.form['data']:
            evento.data = datetime.strptime(request.form['data'], '%Y-%m-%d').date()
        if request.form['horario']:
            evento.horario = datetime.strptime(request.form['horario'], '%H:%M').time()
            
        # Atualiza Inteiros (se não estiver vazio)
        if request.form['limite_jogadores']:
            evento.limite_jogadores = int(request.form['limite_jogadores'])
        
        # Só permite mudar a estrutura do Mata-Mata se ainda estiver na fase de pontos
        if evento.fase_atual == 'Classificatoria':
             evento.vagas_mata_mata = int(request.form['vagas_mata_mata'])
        
        db.session.commit()
        flash("Evento atualizado com sucesso!", "info")
        
    except Exception as e:
        flash(f"Erro ao atualizar: {e}", "error")
        return redirect(url_for('editar_evento', id=id))
        
    return redirect(url_for('dashboard'))

# ... (MANTENHA O if __name__ == '__main__': NO FINAL) ...

if __name__ == '__main__':
    app.run(debug=True)