# Postirony!
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, desc

# Шаблон БД
class Base(DeclarativeBase):
    pass

# Создание приложения 
app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////data/posts.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Инициализация таблиц бд
class Post(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    pretext: Mapped[str] = mapped_column(String, nullable=False)
    img: Mapped[str] = mapped_column(String)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=False)
    edit_key: Mapped[str] = mapped_column(String, nullable=False)

    def __repr__(self):
        return f'Название: {self.title}'


class Comments(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    pid: Mapped[int] = mapped_column(Integer, nullable=False)
    key: Mapped[str] = mapped_column(String)

    def __repr__(self):
        return f'Имя: {self.name}'
    
class Users(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    avatar: Mapped[str] = mapped_column(String)
    all: Mapped[str] = mapped_column(Text, nullable=False)

with app.app_context():
    db.create_all()

# Главная страница
@app.route('/')
def index():
    posts = Post.query.order_by(desc(Post.id)).all()
    return render_template('index.html', data=posts)

# Вывод статей одного автора
@app.route('/author/<string:name>')
def author(name):
    names = Post.query.order_by(desc(Post.id)).all()
    return render_template('authors-post.html', data=names, name=name)

# Поиск статей по автору
@app.route('/search', methods=["POST", "GET"])
def search():
    if request.method == "POST":
        name = request.form["author"]
        searching = Post.query.order_by(desc(Post.id)).all()
        return render_template('authors-post.html', data=searching, name=name)
    else:
        return render_template('search.html')

# Загрузки сразу всех статей 
@app.route('/all')
def all():
    posts = Post.query.order_by(desc(Post.id)).all()
    return render_template('all.html', data=posts)

# Поиск статей по названию
@app.route('/pname', methods=['POST', 'GET'])
def pname():
    if request.method == 'POST':
        post = request.form["title"]
        searching = Post.query.order_by(desc(Post.id)).all()
        return render_template('pname.html', data=searching, name=post)
    else:
        return render_template('sname.html')

# Создание комментариев
@app.route('/posts/<int:id>/comment', methods=['POST', 'GET'])
def comment(id):
    if request.method == 'POST':
        name = request.form['name']
        pid = request.form['pid']
        text = request.form['text']
        key = request.form['key']
        if len(text) < 10:
            return render_template("error.html", error="Слишком маленький текст...")
        comment = Comments(name=name, pid=pid, text=text, key=key)
        try:
            db.session.add(comment)
            db.session.commit()
            return redirect(f'/posts/{id}')
        except:
            return render_template('error.html', error="Ошибка базы данных...")
    else:
        post = db.session.get(Post, id)
        return render_template('comment.html', post=post)

# О сайте
@app.route('/about')
def about():
    return render_template('about.html')

# Загрузка поста по id
@app.route('/posts/<int:id>', methods=['POST', 'GET'])
def posts(id):
    post = db.session.get(Post, id)
    comment = Comments.query.filter_by(pid=id).all()
    return render_template('posts.html', post=post, comment=comment)

# Редактирование статьи
@app.route('/posts/<int:id>/auth-editor', methods=['POST', 'GET'])
def auth_editor(id):
    post = Post.query.get(id)
    if request.method == 'POST':
        if request.form['type'] == "1":
            key = request.form['edit_key']
            if key == post.edit_key:
                return render_template('editor.html', post_edit=post)
            else:
                return render_template('error.html', error="Неверный пароль...")
        elif request.form['type'] == "2":
            title = request.form['title']
            pretext = request.form['pretext']
            text = request.form['text']
            img = request.form['img']
            if len(title) < 5 or len(pretext) < 10 or len(text) < 50:
                return render_template("error.html", error="Слишком маленький текст, интро-текст или заголовок...")
            post.title = title
            post.pretext = pretext
            post.text = text
            post.img = img
            try:
                db.session.commit()
                return render_template('successfully-edit.html', post=post)
            except:
                return render_template('error.html', error="Ошибка базы данных...")
        else:
            return render_template('error.html', error="Неизвестно...")
    else:
        return render_template('auth-editor.html')

# Удаление статьи
@app.route('/posts/<int:id>/del', methods=["POST", "GET"])
def posts_delete(id):
    post_delete = Post.query.get_or_404(id)
    comp = Comments.query.order_by(Comments.pid)
    if request.method == 'POST':
        key = request.form['edit_key']
        if key == post_delete.edit_key:
            try:
                for i in comp: # удаление комментариев к посту
                    if i.pid == id:
                        db.session.delete(i)
                db.session.delete(post_delete)
                db.session.commit()
                return render_template('successfully-del.html')
            except:
                return render_template('error.html', error="Ошибка базы данных...")
        else:
            return render_template('error.html', error="Неверный пароль...")
    else:
        return render_template('auth-del.html')
    
# Редактирование комментария
@app.route('/posts/<int:pid>/comments/<int:id>/cedit', methods=['POST', 'GET'])
def auth_com(id, pid):
    com = Comments.query.get(id)
    if request.method == 'POST':
        if request.form['type'] == "1":  
            if request.form['key'] == com.key:
                post = Post.query.get(pid)
                return render_template('comment-edit.html', post=post, com=com)
            else:
                return render_template('error.html', error='Неверный пароль...')
        elif request.form['type'] == "2":
            com.name = request.form['name']
            com.key = request.form['key']
            com.text = request.form['text']
            try:
                db.session.commit()
                return redirect(f'/posts/{pid}')
            except:
                return render_template('error.html', error="Ошибка базы данных...")
        else:
            return render_template('error.html', error="Неизвестно...")
    else:
        return render_template('auth-com.html')
    
# User manual
@app.route('/user-manual')
def user_manual():
    return render_template('user-manual.html')

# Удаление комментария
@app.route('/posts/<int:pid>/comments/<int:id>/del', methods=['POST', 'GET'])
def del_comments(id, pid):
    comment_delete = Comments.query.get_or_404(id)
    if request.method == 'POST':
        if comment_delete.key == request.form['key']:
            try:
                db.session.delete(comment_delete)
                db.session.commit()
                return redirect(f'/posts/{pid}')
            except:
                return render_template('error.html', error="Ошибка базы данных...")
        else:
            return render_template('error.html', error="Неверный пароль...")
    else:
        return render_template("auth-com-del.html")

# Создание статьи
@app.route('/create', methods=["POST", "GET"])
def create():
    if request.method == "POST":
        title = request.form['title']
        pretext = request.form['pretext']
        author = request.form['name']
        img = request.form['img']
        edit_key = request.form['password']
        text = request.form['text']
        user = Users.query.filter_by(name=author).first()
        if user != None:
            if user.password == edit_key:
                if len(title) < 5 or len(pretext) < 10 or len(text) < 50:
                    return render_template("error.html", error="Слишком маленький текст, интро-текст или заголовок...")
                post_create = Post(title=title, pretext=pretext, author=author, img=img, edit_key=edit_key, text=text)
                try:
                    db.session.add(post_create)
                    db.session.commit()
                    return render_template('successfully-create.html', post=post_create)
                except:
                    return render_template('error.html', error="Ошибка базы данных...")
            else:
                return render_template('error.html', error="Неправильный пароль...")
        else:
            return render_template('error.html', error="Такого пользователя не существует...")

    else:
        return render_template('create.html')

# Регистрация пользователей
@app.route("/register", methods=['POST', 'GET'])
def register():
    if request.method == 'GET':
        return render_template("register.html")
    elif request.method == 'POST':
        data = Users.query.order_by().all()
        name = request.form['name']
        password = request.form['password']
        avatar = request.form['avatar']
        all = request.form['all']
        for i in data:
            if i.name == name:
                return render_template('error.html', error="Пользователь с таким именем уже существует...")
        user = Users(name = name, password = password, avatar = avatar, all = all)
        try:
            db.session.add(user)
            db.session.commit()
            return render_template('true-register.html')
        except:
            return render_template('error.html', error="Ошибка базы данных...")
        
# Авторизация пользователей
@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        return render_template("login.html")
    elif request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        user = Users.query.filter_by(name=name).first()
        if user.password == password:
            data = Post.query.filter_by(author=user.name).all()
            return render_template('profile.html', user=user, data=data)
        else:
            return render_template('error.html', error='Неверный пароль...')

# Запуск
if __name__ == "__main__":
    app.run(port=8080)
