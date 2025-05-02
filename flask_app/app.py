from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, Table, Column, Integer, String, Boolean, Date, MetaData, text
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
from datetime import date
from dateutil.relativedelta import relativedelta  # pour le calcul de 6 mois
import os
import hashlib
from dotenv import load_dotenv
load_dotenv()

# Test des variables d'environnement
print("AUTH_POSTGRES_USER:", os.getenv('AUTH_POSTGRES_USER'))
print("AUTH_POSTGRES_PASSWORD:", os.getenv('AUTH_POSTGRES_PASSWORD'))
print("AUTH_POSTGRES_DB:", os.getenv('AUTH_POSTGRES_DB'))
print("AUTH_POSTGRES_HOST:", os.getenv('AUTH_POSTGRES_HOST'))
print("AUTH_POSTGRES_PORT:", os.getenv('AUTH_POSTGRES_PORT'))

app = Flask(__name__)



# On encode le mot de passe pour la base access_leg_db car caractère spéciaux dans le mot de passe
postgres_password_quoted = quote_plus(os.getenv('POSTGRES_PASSWORD'))

# Configuration pour la base de données access_leg_db
app.config['SQLALCHEMY_DATABASE_URI_ACCESS_LEG'] = (
    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{postgres_password_quoted}"
    f"@{os.getenv('POSTGRES_HOST')}:5432/{os.getenv('POSTGRES_DB')}"
)

# On encode le mot de passe pour la base authent_leg car caractère spéciaux dans le mot de passe
auth_postgres_password_quoted = quote_plus(os.getenv('AUTH_POSTGRES_PASSWORD'))


# Configuration pour la base de données authent_leg_db
app.config['SQLALCHEMY_DATABASE_URI_AUTHENT_LEG'] = (
    f"postgresql+psycopg2://{os.getenv('AUTH_POSTGRES_USER')}:{auth_postgres_password_quoted}"
    f"@{os.getenv('AUTH_POSTGRES_HOST')}:5432/{os.getenv('AUTH_POSTGRES_DB')}"
)

# Ajout du print ici pour vérifier l'URI générée
print("URI ACCESS_LEG :", app.config['SQLALCHEMY_DATABASE_URI_ACCESS_LEG'])
print("URI AUTHENT_LEG :", app.config['SQLALCHEMY_DATABASE_URI_AUTHENT_LEG'])


# Initialisation des connexions aux bases de données
engine_access_leg = create_engine(app.config['SQLALCHEMY_DATABASE_URI_ACCESS_LEG'])
engine_authent_leg = create_engine(app.config['SQLALCHEMY_DATABASE_URI_AUTHENT_LEG'])

metadata = MetaData()

# Définir la table user
usager_table = Table(
    'usager', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('utilisateur', String(255)),
    Column('pwd', String(255)),
    Column('type', String(10)),
    Column('date_creat_pwd', Date),
    Column('validation', Boolean, default=False),
    schema='authentification'
)


@app.route('/cartographie_interne')
def cartographie_interne():
    return render_template('cartographie_interne.html')

# Route pour cartographie externe
@app.route('/cartographie_externe')
def cartographie_externe():
    return render_template('cartographie_externe.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/logging.html')
def logging():
    return render_template('logging.html')

@app.route('/logging_new.html')
def logging_new():
    return render_template('logging_new.html')

@app.route('/logging_modif_pwd')
def logging_modif_pwd():
    return render_template('logging_modif_pwd.html')



@app.route('/create_user', methods=['POST'])
def create_user():
    email = request.form['email']
    password = request.form['password']

    # Vérification du type d'utilisateur
    user_type = 'interne' if email.endswith('@leg.fr') else 'externe'

    # Hashage SHA-256 répété 10 fois
    hashed_email = email
    for _ in range(10):
        hashed_email = hashlib.sha256(hashed_email.encode()).hexdigest()

    hashed_password = password
    for _ in range(10):
        hashed_password = hashlib.sha256(hashed_password.encode()).hexdigest()

    # Insertion dans la base de données
    with engine_authent_leg.begin() as connection:
        connection.execute(usager_table.insert().values(
            utilisateur=hashed_email,
            pwd=hashed_password,
            type=user_type,
            date_creat_pwd=date.today(),
            validation=False
        ))
    
    # Rediriger vers la page de connexion (ou une page de confirmation)
    return redirect(url_for('success_page'))  # Redirige vers une autre route

# Route de confirmation après inscription (par exemple, on retourne sur la page de connexion)
@app.route('/success')
def success_page():
    return render_template('logging.html')

#route pour le login (authentification)
@app.route('/login', methods=['POST'])
def login():
    # Récupération des données du formulaire
    email = request.form.get('email')
    password = request.form.get('password')
    
    # Hashage SHA-256 répété 10 fois pour l'email
    hashed_email = email
    for _ in range(10):
        hashed_email = hashlib.sha256(hashed_email.encode()).hexdigest()

    # Hashage SHA-256 répété 10 fois pour le mot de passe
    hashed_password = password
    for _ in range(10):
        hashed_password = hashlib.sha256(hashed_password.encode()).hexdigest()
    
    # Requête pour chercher le compte correspondant dans la table usager
    with engine_authent_leg.connect() as connection:
        query = usager_table.select().where(
            usager_table.c.utilisateur == hashed_email
        ).where(
            usager_table.c.pwd == hashed_password
        )
        # Utilisation de .mappings() pour obtenir un dictionnaire par ligne
        result = connection.execute(query).mappings().fetchone()
    
    # Si aucun enregistrement n'est trouvé
    if result is None:
        return """
            <script>
                alert("Nom d'utilisateur ou mot de passe incorrect");
                window.location.href = "/logging.html";
            </script>
        """
    # Vérification de l'expiration du mot de passe
    # Si la date de création est antérieure à (date d'aujourd'hui - 6 mois)
    if result['date_creat_pwd'] < date.today() - relativedelta(months=6):
        return """
            <html>
                <body>
                    <script>
                        alert("Votre mot de passe a expiré (il date de plus de 6 mois).");
                    </script>
                    <p>Veuillez cliquer sur le lien suivant : 
                        <a href="/logging_modif_pwd">Modification de mot de passe</a>
                    </p>
                </body>
            </html>
        """
    

    
    # Si le compte n'a pas été validé
    if not result['validation']:
        return """
            <script>
                alert("Vous n'avez pas activé votre compte. Allez dans votre boîte mail pour activer votre compte en cliquant sur le lien dans votre e-mail d'authentification. Sinon, recéez un nouveau compte.");
                window.location.href = "/logging.html";
            </script>
        """
    
    # Si le compte est validé, on vérifie le type d'utilisateur
    if result['type'] == 'interne':
        return redirect(url_for('cartographie_interne'))
    elif result['type'] == 'externe':
        return redirect(url_for('cartographie_externe'))
    else:
        return """
            <script>
                alert("Type d'utilisateur inconnu");
                window.location.href = "/logging.html";
            </script>
        """

@app.route('/modif_pwd', methods=['POST'])
def modif_pwd():
    # Récupération des données du formulaire
    email = request.form.get('email')
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    new_password_confirm = request.form.get('new_password_confirm')

    # Vérification que le nouveau mot de passe a été correctement confirmé
    if new_password != new_password_confirm:
        return """
            <script>
                alert("Les nouveaux mots de passe ne correspondent pas");
                window.location.href = "/logging_modif_pwd";
            </script>
        """
    
    # Hashage des mots de passe (en utilisant le même procédé que pour la connexion)
    hashed_email = email
    for _ in range(10):
        hashed_email = hashlib.sha256(hashed_email.encode()).hexdigest()
    
    hashed_old_password = old_password
    for _ in range(10):
        hashed_old_password = hashlib.sha256(hashed_old_password.encode()).hexdigest()
    
    hashed_new_password = new_password
    for _ in range(10):
        hashed_new_password = hashlib.sha256(hashed_new_password.encode()).hexdigest()
    
    # Recherche l'utilisateur correspondant par email et ancien mot de passe
    with engine_authent_leg.connect() as connection:
        query = usager_table.select().where(
            usager_table.c.utilisateur == hashed_email
        ).where(
            usager_table.c.pwd == hashed_old_password
        )
        user = connection.execute(query).mappings().fetchone()
    
    if user is None:
        return """
            <script>
                alert("Identifiant ou ancien mot de passe incorrect");
                window.location.href = "/logging_modif_pwd";
            </script>
        """
    
    # Mise à jour du mot de passe avec le nouveau mot de passe hashé et de la date de modification du mot de passe
    with engine_authent_leg.begin() as connection:
        update_query = usager_table.update().where(
            usager_table.c.id == user['id']
        ).values(
            pwd=hashed_new_password,
            date_creat_pwd=date.today()  # met à jour la date du mot de passe
        )
        connection.execute(update_query)
    
    return """
        <script>
            alert("Votre mot de passe a bien été modifié");
            window.location.href = "/logging.html";
        </script>
    """

@app.route('/get_accessibility_data')
def get_accessibility_data():
    with engine_access_leg.connect() as connection:
        query = text("SELECT lg_accessible, lg_access_moy, lg_non_access, pourcent_access, pourcent_access_moy, pourcent_non_access FROM limite_admin.vm_commune_access")
        result = connection.execute(query).fetchone()

        if result:
            data = {
                'lg_accessible': result[0],  # Utilisez des indices entiers
                'lg_access_moy': result[1],
                'lg_non_access': result[2],
                'pourcent_access': result[3],
                'pourcent_access_moy': result[4],
                'pourcent_non_access': result[5]
            }
            return jsonify(data)
        else:
            return jsonify({'error': 'No data found'}), 404
        

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

    