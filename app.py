from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import requests
import io
import os
from datetime import datetime, timedelta
import random
from flask_misaka import Misaka


app = Flask(__name__)
Misaka(app, fenced_code=True, tables=True, strikethrough=True)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.sqlite')
app.config['SECRET_KEY'] = 'svejk5417xm049p2gypu1wthixd2rh92jkrx28pc83vlmemi'  # Mude isto para uma string secreta real
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Simule uma base de dados de notícias (você substituiria isso por um banco de dados real)
noticias_mock = [
    {
        "id": i,
        "titulo": f"Notícia de IA {i}",
        "resumo": f"Este é um resumo da notícia de IA número {i}. Aqui teríamos uma breve descrição do conteúdo da notícia.",
        "imagem_url": f"/api/placeholder/400/200?text=Notícia+{i}",
        "link": f"#noticia-{i}",
        "data_publicacao": datetime.now() - timedelta(days=random.randint(0, 30))
    } for i in range(1, 21)  # Cria 20 notícias de exemplo
]

# Inicialize a extensão Markdown
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Noticia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    resumo = db.Column(db.Text, nullable=False)
    imagem_url = db.Column(db.String(500), nullable=False)
    link = db.Column(db.String(500), nullable=False)
    data_publicacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<Noticia {self.titulo}>'
    
class Dica(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    autor = db.Column(db.String(50), nullable=False)
    data_publicacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    texto = db.Column(db.Text, nullable=False)

class Imagem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    link = db.Column(db.String(200), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    categorias = db.Column(db.String(200), default='')

class Projeto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    tecnologias = db.Column(db.String(200), nullable=False)
    link = db.Column(db.String(500))
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Projeto {self.nome}>'
class Tutorial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    tag_tutorial = db.Column(db.String(50), nullable=False)  # Ex: "Python", "Machine Learning", etc.
    ferramentas = db.Column(db.String(200), nullable=False)  # Ferramentas utilizadas
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Tutorial {self.titulo}>'
        
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.template_filter('nl2br')
def nl2br(value):
    if not value:
        return value
    return value.replace('\n', '<br>\n')

# Configurações para upload de imagens
UPLOAD_FOLDER = 'static/uploads/tutoriais'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    dicas = Dica.query.order_by(Dica.data_publicacao.desc()).limit(3).all()
    imagens = Imagem.query.order_by(Imagem.data_criacao.desc()).limit(4).all()  # Limitado a 4 imagens
    return render_template('index.html', dicas=dicas, imagens=imagens)

@app.route('/imagens')
def listar_imagens():
    categoria = request.args.get('categoria', '')
    query = Imagem.query

    if categoria:
        query = query.filter(Imagem.categorias.like(f'%{categoria}%'))

    imagens = query.order_by(Imagem.data_criacao.desc()).all()
    
    print(f"Categoria selecionada: {categoria}")  # Debug print
    print(f"Número de imagens após filtro: {len(imagens)}")  # Debug print

    return render_template('imagens.html', imagens=imagens, categoria_selecionada=categoria)

@app.route('/dicas')
def dicas():
    dicas = Dica.query.order_by(Dica.data_publicacao.desc()).all()
    return render_template('dicas.html', dicas=dicas)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        flash('Nome de usuário ou senha inválidos', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('index'))

@app.route('/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_dica():
    if not current_user.is_admin:
        flash('Acesso negado. Você precisa ser um administrador.', 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        titulo = request.form['titulo']
        autor = request.form['autor']
        texto = request.form['texto']
        nova_dica = Dica(titulo=titulo, autor=autor, texto=texto)
        db.session.add(nova_dica)
        db.session.commit()
        flash('Dica adicionada com sucesso!', 'success')
        return redirect(url_for('index'))
    return render_template('adicionar_dica.html')

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_dica(id):
    if not current_user.is_admin:
        flash('Acesso negado. Você precisa ser um administrador.', 'danger')
        return redirect(url_for('index'))
    dica = Dica.query.get_or_404(id)
    if request.method == 'POST':
        dica.titulo = request.form['titulo']
        dica.autor = request.form['autor']
        dica.texto = request.form['texto']
        db.session.commit()
        flash('Dica atualizada com sucesso!', 'success')
        return redirect(url_for('index'))
    return render_template('editar_dica.html', dica=dica)

@app.route('/excluir/<int:id>')
@login_required
def excluir_dica(id):
    if not current_user.is_admin:
        flash('Acesso negado. Você precisa ser um administrador.', 'danger')
        return redirect(url_for('index'))
    dica = Dica.query.get_or_404(id)
    db.session.delete(dica)
    db.session.commit()
    flash('Dica excluída com sucesso!', 'success')
    return redirect(url_for('index'))

@app.route('/adicionar_imagem', methods=['GET', 'POST'])
@login_required
def adicionar_imagem():
    if not current_user.is_admin:
        flash('Acesso negado. Você precisa ser um administrador.', 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        link = request.form['link']
        prompt = request.form['prompt']
        categorias = request.form['categorias']
        nova_imagem = Imagem(link=link, prompt=prompt, categorias=categorias)
        db.session.add(nova_imagem)
        db.session.commit()
        flash('Imagem adicionada com sucesso!', 'success')
        return redirect(url_for('listar_imagens'))
    return render_template('adicionar_imagem.html')

@app.route('/editar_imagem/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_imagem(id):
    if not current_user.is_admin:
        flash('Acesso negado. Você precisa ser um administrador.', 'danger')
        return redirect(url_for('index'))
    
    imagem = Imagem.query.get_or_404(id)
    
    if request.method == 'POST':
        imagem.link = request.form['link']
        imagem.prompt = request.form['prompt']
        categorias = request.form.getlist('categorias')
        imagem.categorias = ', '.join(categorias) if categorias else None
        db.session.commit()
        flash('Imagem atualizada com sucesso!', 'success')
        return redirect(url_for('listar_imagens'))
    
    return render_template('editar_imagem.html', imagem=imagem)

@app.route('/excluir_imagem/<int:id>')
@login_required
def excluir_imagem(id):
    if not current_user.is_admin:
        flash('Acesso negado. Você precisa ser um administrador.', 'danger')
        return redirect(url_for('index'))
    imagem = Imagem.query.get_or_404(id)
    db.session.delete(imagem)
    db.session.commit()
    flash('Imagem excluída com sucesso!', 'success')
    return redirect(url_for('listar_imagens'))

@app.route('/download_imagem/<int:id>')
def download_imagem(id):
    imagem = Imagem.query.get_or_404(id)
    response = requests.get(imagem.link)
    return send_file(
        io.BytesIO(response.content),
        mimetype=response.headers['Content-Type'],
        as_attachment=True,
        download_name=f"imagem_{id}.jpg"
    )

@app.route('/noticias')
def noticias():
    page = request.args.get('page', 1, type=int)
    per_page = 9  # Número de notícias por página
    noticias_paginadas = Noticia.query.order_by(Noticia.data_publicacao.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('noticias.html', noticias=noticias_paginadas.items, pagina_atual=page, paginas=noticias_paginadas.pages)

@app.route('/adicionar_noticia', methods=['GET', 'POST'])
@login_required
def adicionar_noticia():
    if not current_user.is_admin:
        flash('Acesso negado. Você precisa ser um administrador.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        nova_noticia = Noticia(
            titulo=request.form['titulo'],
            resumo=request.form['resumo'],
            imagem_url=request.form['imagem_url'],
            link=request.form['link']
        )
        db.session.add(nova_noticia)
        db.session.commit()
        flash('Nova notícia adicionada com sucesso!', 'success')
        return redirect(url_for('noticias'))
    
    return render_template('adicionar_noticia.html')

@app.route('/projetos')
def listar_projetos():
    busca = request.args.get('busca', '')
    query = Projeto.query

    if busca:
        query = query.filter(
            db.or_(
                Projeto.nome.ilike(f'%{busca}%'),
                Projeto.descricao.ilike(f'%{busca}%'),
                Projeto.tecnologias.ilike(f'%{busca}%')
            )
        )

    projetos = query.order_by(Projeto.data_criacao.desc()).all()
    return render_template('projetos.html', projetos=projetos, busca=busca)

@app.route('/adicionar_projeto', methods=['GET', 'POST'])
@login_required
def adicionar_projeto():
    if not current_user.is_admin:
        flash('Acesso negado. Você precisa ser um administrador.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        novo_projeto = Projeto(
            nome=request.form['nome'],
            descricao=request.form['descricao'],
            tecnologias=request.form['tecnologias'],
            link=request.form['link']
        )
        db.session.add(novo_projeto)
        db.session.commit()
        flash('Novo projeto adicionado com sucesso!', 'success')
        return redirect(url_for('listar_projetos'))
    
    return render_template('adicionar_projeto.html')

@app.route('/cursos')
def cursos():
    tutoriais = Tutorial.query.order_by(Tutorial.data_criacao.desc()).all()
    return render_template('cursos.html', tutoriais=tutoriais)

@app.route('/adicionar_tutorial', methods=['GET', 'POST'])
@login_required
def adicionar_tutorial():
    if not current_user.is_admin:
        flash('Acesso negado. Você precisa ser um administrador.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        novo_tutorial = Tutorial(
            titulo=request.form['titulo'],
            texto=request.form['texto'],
            tag_tutorial=request.form['tag_tutorial'],
            ferramentas=request.form['ferramentas']
        )
        db.session.add(novo_tutorial)
        db.session.commit()
        flash('Tutorial adicionado com sucesso!', 'success')
        return redirect(url_for('cursos'))
    
    return render_template('adicionar_tutorial.html')

@app.route('/editar_tutorial/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_tutorial(id):
    if not current_user.is_admin:
        flash('Acesso negado. Você precisa ser um administrador.', 'danger')
        return redirect(url_for('cursos'))
    
    tutorial = Tutorial.query.get_or_404(id)
    if request.method == 'POST':
        tutorial.titulo = request.form['titulo']
        tutorial.texto = request.form['texto']
        tutorial.tag_tutorial = request.form['tag_tutorial']
        tutorial.ferramentas = request.form['ferramentas']
        db.session.commit()
        flash('Tutorial atualizado com sucesso!', 'success')
        return redirect(url_for('cursos'))
    
    return render_template('editar_tutorial.html', tutorial=tutorial)

@app.route('/excluir_tutorial/<int:id>')
@login_required
def excluir_tutorial(id):
    if not current_user.is_admin:
        flash('Acesso negado. Você precisa ser um administrador.', 'danger')
        return redirect(url_for('cursos'))
    
    tutorial = Tutorial.query.get_or_404(id)
    db.session.delete(tutorial)
    db.session.commit()
    flash('Tutorial excluído com sucesso!', 'success')
    return redirect(url_for('cursos'))

@app.route('/tutorial/<int:id>')
def ver_tutorial(id):
    tutorial = Tutorial.query.get_or_404(id)
    return render_template('ver_tutorial.html', tutorial=tutorial)

@app.route('/upload_imagem', methods=['POST'])
@login_required
def upload_imagem():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Adiciona timestamp ao nome do arquivo para evitar duplicatas
        filename = f"{int(datetime.now().timestamp())}_{filename}"
        
        # Cria o diretório de upload se não existir
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Retorna a URL da imagem
        return jsonify({
            'location': url_for('static', filename=f'uploads/tutoriais/{filename}')
        })
    
    return jsonify({'error': 'Tipo de arquivo não permitido'}), 400

def create_admin_user():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', is_admin=True)
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
        print("Usuário admin criado com sucesso!")
    else:
        print("Usuário admin já existe.")

with app.app_context():
    db.create_all()
    create_admin_user()

if __name__ == '__main__':
    app.run(debug=True)