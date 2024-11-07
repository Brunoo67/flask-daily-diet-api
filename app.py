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

#ROTA DE USUÁRIOS

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



@app.route('/edit-username/<int:user_id>', methods=['PUT'])
@login_required
def edit_username(user_id):
    user = User.query.get(user_id)
    data = request.json
    old_username = user.username

    if not user:
        return jsonify({'message': f'Usuário não encontrado'}), 404

    if User.query.filter_by(username=data.get('username')).first():
        return jsonify({'message': 'Nome de usuário já existe. Escolha outro.'}), 400

    if (data.get('username') and current_user.role == 'admin') or (data.get('username') and user_id == current_user.id):
        user.username = data.get('username')
        db.session.commit()
        return jsonify({'message' : f'Nome antigo: {old_username} | Nome atualizado: {user.username}'})
    
    return jsonify({'message' : 'Você não tem permissão para isso.'}), 403



@app.route('/edit-password/<int:user_id>', methods=['PUT'])
@login_required
def edit_password(user_id):
    user = User.query.get(user_id)
    data = request.json

    if not user:
        return jsonify({'message': f'Usuário não encontrado'}), 404
    
    if (data.get('password') and current_user.role == 'admin') or (data.get('password') and user_id == current_user.id):
        hashed_password = bcrypt.hashpw(str.encode(data.get('password')), bcrypt.gensalt())
        user.password = hashed_password
        db.session.commit()
        return jsonify({'message' : 'Senha alterada com sucesso!'})
    
    return jsonify({'message' : 'Você não tem permissão para isso.'}), 403



@app.route('/user-delete/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    user = User.query.get(user_id)
    username = user.username
    if not user:
        return jsonify({'message': f'Usuário não encontrado'}), 404
    
    if current_user.role == 'admin' or user_id == current_user.id:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message' : f'Usuário {user_id} | {username} deletado com sucesso!'})
    
    return jsonify({'message' : 'Você não tem permissão para isso.'}), 403

##### ROTAS DE REFEIÇÃO

@app.route('/meal', methods=['POST'])
@login_required
def create_meal():
    data = request.json
    name = data.get('name')
    description = data.get('description')
    #date_time_str = data.get('date_time')
    on_diet = data.get('on_diet')

    if name:
        meal = Meal(name=name, description=description, on_diet=on_diet, user_id=current_user.id)
        db.session.add(meal)
        db.session.commit()
        return jsonify({'message' : "Refeição criada com sucesso!"})
    return jsonify({'message': 'dados inválidos'}), 400



@app.route('/read-meal/<int:id_meal>', methods=['GET'])
@login_required
def read_meal(id_meal):
    meal = Meal.query.get(id_meal)

    if (meal and current_user.role == 'admin') or (meal and meal.user_id == current_user.id):
        return jsonify({'message' : f'ID: {meal.id} | Nome: {meal.name} | Descrição: {meal.description} | Na dieta: {meal.on_diet}'})
    
    if not meal:
        return jsonify({'message': f'Refeição de id {id_meal} não encontrada'}), 404
    
    return jsonify({'message' : 'Você não tem permissão para isso.'}), 403



@app.route('/read-all-meals/<int:user_id>', methods=['GET'])
@login_required
def read_all_meals_by_user(user_id):

    if current_user.role == 'admin' or current_user.id == user_id:
        meals = Meal.query.filter_by(user_id=user_id).all()
        user = User.query.get(user_id)

        if meals:
            meal_information= [

                {
                    "ID" : meal.id,
                    "Nome" : meal.name,
                    "Descrição" : meal.description,
                    "On diet" : meal.on_diet
                }
                for meal in meals
            ]

            count = len(meals)
            return jsonify({
                            f'Número de refeições cadastradas pelo usuário {user_id} | {user.username}:' : count,
                            'Refeições: ' : meal_information})
        
        
        return jsonify({'message': f'Nenhuma refeição encontrada para o usuário de id {user_id}'}), 404
    
    return jsonify({'message': 'Você não tem permissão para isso.'}), 403



@app.route('/edit-meal-name/<int:id_meal>', methods=['PUT'])
@login_required
def edit_meal_name(id_meal):
    meal = Meal.query.get(id_meal)
    data = request.json
    old_name = meal.name
    if not meal:
        return jsonify({'message': f'Refeição de id {id_meal} não encontrada'}), 404
    
    if (data.get('name') and current_user.role == 'admin') or (data.get('name') and meal.user_id == current_user.id):

        meal.name = data.get('name')
        db.session.commit()
        return jsonify({'message' : f'Refeição {id_meal} | {old_name} foi atualizado para {meal.name}'})
    
    return jsonify({'message' : 'Você não tem permissão para isso.'}), 403

@app.route('/edit-meal-description/<int:id_meal>', methods=['PUT'])
@login_required
def edit_meal_description(id_meal):
    meal = Meal.query.get(id_meal)
    data = request.json
    if not meal:
        return jsonify({'message': f'Refeição de id {id_meal} não encontrada'}), 404
    
    if (data.get('description') and current_user.role == 'admin') or (data.get('description') and meal.user_id == current_user.id):

        meal.description = data.get('description')
        db.session.commit()
        return jsonify({'message' : f'Refeição {id_meal} | {meal.name} deve a descrição atualiazada para: {meal.description}'})
    
    return jsonify({'message' : 'Você não tem permissão para isso.'}), 403

@app.route('/edit-meal-on_diet/<int:id_meal>', methods=['PUT'])
@login_required
def edit_meal_on_diet(id_meal):
    meal = Meal.query.get(id_meal)
    data = request.json
    if not meal:
        return jsonify({'message': f'Refeição de id {id_meal} não encontrada'}), 404
    
    if data.get('on_diet') not in [True, False]:
        return jsonify({'message': 'O campo "on_diet" deve ser um valor booleano (true ou false)'}), 400


    if current_user.role == 'admin' or meal.user_id == current_user.id:

        meal.on_diet = data.get('on_diet')
        db.session.commit()
        return jsonify({'message' : f'Refeição {id_meal} | {meal.name} está na dieta: {meal.on_diet}'})
    
    return jsonify({'message' : f'Você não tem permissão para isso. {current_user.role} {data.get('on_diet')}'}), 403


@app.route('/delete-meal/<int:id_meal>', methods=['DELETE'])
@login_required
def delete_meal(id_meal):
    meal = Meal.query.get(id_meal)
    if not meal:
        return jsonify({'message': f'Refeição de id {id_meal} não encontrada.'}), 404

    if current_user.role == 'admin' or meal.user_id == current_user.id:
        db.session.delete(meal)
        db.session.commit()
        return jsonify({'message': f'Refeição {meal.id} | {meal.name} deletada com sucesso!'}), 200
    
    
    return jsonify({'message': 'Você não tem permissão para isso.'}), 403


if __name__ == ('__main__'):
    app.run(debug=True)
    