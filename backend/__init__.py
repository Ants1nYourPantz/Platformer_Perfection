from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import Blueprint
from os import path
import os



DB_NAME = 'database.db'
    
app = Flask(__name__)
app.config['SECRET_KEY'] = 'test'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'

db = SQLAlchemy(app)
# db.init_app(app)



api = Blueprint('api', __name__, url_prefix='/api')
app.register_blueprint(api)


from backend import routes, models

with app.app_context():
    if not path.exists('backend/' + DB_NAME):
        db.create_all()
        print('created database')
        print(os.getcwd())
        print(os.path.abspath(DB_NAME))





if __name__ == '__main__':
    app.run(debug=True)






# migrate = Migrate(app, db)