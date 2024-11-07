from flask import Flask, request, jsonify
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from database import db
from models.user import User
from models.meals import Meal
import bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:admin123@127.0.0.1:3306/daily-diet'

login_manager = LoginManager()
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route('/login', methods=["POST"])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if username and password:
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.checkpw(str.encode(password), str.encode(user.password)):
            login_user(user)
            
            return jsonify({'message' : f'Logado como {user.username}'})
        return jsonify({'message': 'Dados inválidos'}), 400
        
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message' : 'Logout feito com sucesso!'})


@app.route('/user', methods=['POST'])
def create_user():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if username and password:
        hashed_password = bcrypt.hashpw(str.encode(password), bcrypt.gensalt())
        user = User(username=username, password=hashed_password, role='user')
        db.session.add(user)
        db.session.commit()
        return jsonify({'message' : f'Usuário {user.username} foi criado com sucesso!'})
    
    return jsonify({'message' : "Dados incorretos"}), 400


@app.route('/meal', methods=['POST'])
def create_meal():
    data = request.json
    name = data.get('name')
    description = data.get('description')
    #date_time_str = data.get('date_time')
    on_diet = data.get('on_diet', False)

    if name and on_diet:
        meal = Meal(name=name, description=description, on_diet=on_diet, user_id=current_user.id)
        db.session.add(meal)
        db.session.commit()
        return jsonify({'message' : "Refeição criada com sucesso!"})
    return jsonify({'message': 'dados inválidos'}), 400

if __name__ == ('__main__'):
    app.run(debug=True)

    