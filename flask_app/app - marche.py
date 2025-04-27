from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os


# Charger les variables d'environnement depuis le fichier .env
load_dotenv()


app = Flask(__name__)

# Configuration pour la base de données access_leg_db
app.config['SQLALCHEMY_DATABASE_URI_ACCESS_LEG'] = (
    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST', 'access_leg_db')}:{os.getenv('POSTGRES_PORT', 5435)}"
    f"/{os.getenv('POSTGRES_DB')}"
)

# Configuration pour la base de données authent_leg_db
app.config['SQLALCHEMY_DATABASE_URI_AUTHENT_LEG'] = (
    f"postgresql+psycopg2://{os.getenv('AUTH_POSTGRES_USER')}:{os.getenv('AUTH_POSTGRES_PASSWORD')}"
    f"@{os.getenv('AUTH_POSTGRES_HOST', 'authent_leg_db')}:{os.getenv('AUTH_POSTGRES_PORT', 5438)}"
    f"/{os.getenv('AUTH_POSTGRES_DB')}"
)

# Initialisation des connexions aux bases de données
engine_access_leg = create_engine(app.config['SQLALCHEMY_DATABASE_URI_ACCESS_LEG'])
engine_authent_leg = create_engine(app.config['SQLALCHEMY_DATABASE_URI_AUTHENT_LEG'])

@app.route('/cartographie_interne')
def cartographie_interne():
    return render_template('cartographie_interne.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/logging.html')
def logging():
    return render_template('logging.html')

@app.route('/logging_new.html')
def logging_new():
    return render_template('logging_new.html')






# Créer des sessions pour interagir avec les bases de données
#SessionAccessLeg = sessionmaker(bind=engine_access_leg)
#SessionAuthentLeg = sessionmaker(bind=engine_authent_leg)

#@app.route('/data_from_access_leg')
#def data_from_access_leg():
#    session = SessionAccessLeg()
#    # Exécutez vos requêtes ici
#    result = session.execute("SELECT * FROM your_table")
#    data = result.fetchall()
#    session.close()
#    return str(data)

#@app.route('/data_from_authent_leg')
#def data_from_authent_leg():
#    session = SessionAuthentLeg()
    # Exécutez vos requêtes ici
#    result = session.execute("SELECT * FROM your_auth_table")
#    data = result.fetchall()
#    session.close()
#    return str(data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

    