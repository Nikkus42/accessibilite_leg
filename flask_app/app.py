from flask import Flask, render_template, jsonify, request, redirect, url_for, g
from flask_cors import CORS  # Importer CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, Table, Column, Integer, String, Boolean, Date, MetaData, text
from sqlalchemy.orm import sessionmaker
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from shapely.wkt import loads as wkt_loads
from urllib.parse import quote_plus
from datetime import date
from dateutil.relativedelta import relativedelta
import os
import time
import hashlib
import logging
from dotenv import load_dotenv
import json
import re

# Chargement des variables d'environnement
load_dotenv()

# Configuration du logger (à placer ici, juste après les imports)
logging.basicConfig(
    filename="/app/logs/app.log",  # Fichier où seront enregistrés les logs
    level=logging.INFO,  # Niveau d'enregistrement des logs
    format="%(asctime)s - %(levelname)s - %(message)s",  # Format des logs
)

logger = logging.getLogger(__name__)  # Création du logger

# Test des variables d'environnement
logger.info("Chargement des variables d'environnement...")
print("AUTH_POSTGRES_USER:", os.getenv('AUTH_POSTGRES_USER'))
print("AUTH_POSTGRES_PASSWORD:", os.getenv('AUTH_POSTGRES_PASSWORD'))
print("AUTH_POSTGRES_DB:", os.getenv('AUTH_POSTGRES_DB'))
print("AUTH_POSTGRES_HOST:", os.getenv('AUTH_POSTGRES_HOST'))
print("AUTH_POSTGRES_PORT:", os.getenv('AUTH_POSTGRES_PORT'))

# Initialisation de l’application Flask
app = Flask(__name__)
logger.info("Application Flask initialisée.")

# Configuration CORS pour permettre les requêtes depuis http://localhost:5001
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5001"}})

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
try:
    engine_access_leg = create_engine(app.config['SQLALCHEMY_DATABASE_URI_ACCESS_LEG'])
    logger.info("Connexion réussie à la base access_leg_db")
except Exception as e:
    logger.error(f"Erreur de connexion à access_leg_db : {str(e)}")

try:
    engine_authent_leg = create_engine(app.config['SQLALCHEMY_DATABASE_URI_AUTHENT_LEG'])
    logger.info("Connexion réussie à la base authent_leg_db")
except Exception as e:
    logger.error(f"Erreur de connexion à authent_leg_db : {str(e)}")

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

# Hooks pour le logging des requêtes
@app.before_request
def before_request_logging():
    g.start_time = time.time()
    logger.info(f"Nouvelle requête : {request.method} {request.path} depuis {request.remote_addr}")

@app.after_request
def after_request_logging(response):
    duration = time.time() - g.start_time
    logger.info(f"Réponse {response.status_code} pour {request.method} {request.path} en {duration:.3f}s")
    return response

@app.route('/client-log', methods=['POST'])
def client_log():
    log_data = request.get_json()
    # Vous recevrez un dictionnaire du type
    # { "level": "log"/"warn"/"error", "messages": [...], "timestamp": "..." }
    level = log_data.get('level', 'log')
    message = f"Log client à {log_data.get('timestamp')} : {log_data.get('messages')}"

    if level == 'warn':
        logger.warning(message)
    elif level == 'error':
        logger.error(message)
    else:
        logger.info(message)

    return jsonify(success=True), 200

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

@app.route('/contact')
def logging_concact():
    return render_template('contact.html')

@app.route('/create_user', methods=['POST'])
def create_user():
    email = request.form['email']
    password = request.form['password']
    user_type = 'interne' if email.endswith('@leg.fr') else 'externe'

    logger.info(f"Tentative de création d'utilisateur : {email}, type : {user_type}")

    # Vérification de la complexité du mot de passe
    if (len(password) < 12 or 
        not re.search(r'[A-Z]', password) or 
        not re.search(r'[a-z]', password) or 
        not re.search(r'\d', password) or 
        not re.search(r'[^A-Za-z0-9]', password)):
        return """
            <script>
                alert("Le mot de passe ne respecte pas les règle de sécurité : 12 caractères minimum contenant des lettres majuscules et minuscules des chiffres et des caractères spéciaux");
                window.location.href = "/logging_new.html";
            </script>
        """

    try:
        # Hashage SHA-256 répété 10 fois pour l'email
        hashed_email = email
        for _ in range(10):
            hashed_email = hashlib.sha256(hashed_email.encode()).hexdigest()

        # Hashage SHA-256 répété 10 fois pour le mot de passe
        hashed_password = password
        for _ in range(10):
            hashed_password = hashlib.sha256(hashed_password.encode()).hexdigest()

        # Insertion dans la base de données (avec log en cas de succès)
        with engine_authent_leg.begin() as connection:
            connection.execute(usager_table.insert().values(
                utilisateur=hashed_email,
                pwd=hashed_password,
                type=user_type,
                date_creat_pwd=date.today(),
                validation=False
            ))

        logger.info(f"Utilisateur créé avec succès : {email} (type : {user_type})")
        # Rediriger vers la page de connexion
        return redirect(url_for('success_page'))

    except Exception as e:
        logger.error(f"Erreur lors de la création de l'utilisateur {email} : {str(e)}")
        return "Erreur lors de la création de l’utilisateur", 500

    
# Route de confirmation après inscription (on retourne sur la page de connexion)
@app.route('/success')
def success_page():
    return render_template('logging.html')

# Route pour le login (authentification)
@app.route('/login', methods=['POST'])
def login():
    # Récupération des données du formulaire
    email = request.form.get('email')
    password = request.form.get('password')

    logger.info(f"Tentative de connexion pour {email}")

    try:
        # Hashage SHA-256 répété 10 fois pour l'email
        hashed_email = email
        for _ in range(10):
            hashed_email = hashlib.sha256(hashed_email.encode()).hexdigest()

        # Hashage SHA-256 répété 10 fois pour le mot de passe
        hashed_password = password
        for _ in range(10):
            hashed_password = hashlib.sha256(hashed_password.encode()).hexdigest()

        # Mesure du temps d'exécution de la requête --> début
        start_time = time.time()
        # Requête pour chercher le compte correspondant dans la table usager
        with engine_authent_leg.connect() as connection:
            query = usager_table.select().where(
                usager_table.c.utilisateur == hashed_email
            ).where(
                usager_table.c.pwd == hashed_password
            )
            # Utilisation de .mappings() pour obtenir un dictionnaire par ligne
            result = connection.execute(query).mappings().fetchone()
        # Mesure du temps d'exécution de la requête --> fin
        duration = time.time() - start_time
        logger.info(f"Exécution de la requête de login pour {email} en {duration:.3f}s")

        # Si aucun enregistrement n'est trouvé
        if result is None:
            logger.warning(f"Échec de connexion pour {email} : Identifiants incorrects")
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
            logger.warning(f"Compte non activé pour {email}")
            return """
                <script>
                    alert("Vous n'avez pas activé votre compte. Allez dans votre boîte mail pour activer votre compte en cliquant sur le lien dans votre e-mail d'authentification. Sinon, recréez un nouveau compte.");
                    window.location.href = "/logging.html";
                </script>
            """

        # Si le compte est validé, on vérifie le type d'utilisateur
        if result['type'] == 'interne':
            logger.info(f"Connexion réussie pour {email} - Type : interne")
            return redirect(url_for('cartographie_interne'))
        elif result['type'] == 'externe':
            logger.info(f"Connexion réussie pour {email} - Type : externe")
            return redirect(url_for('cartographie_externe'))
        else:
            logger.error(f"Type d'utilisateur inconnu pour {email}")
            return """
                <script>
                    alert("Type d'utilisateur inconnu");
                    window.location.href = "/logging.html";
                </script>
            """

    except Exception as e:
        logger.error(f"Erreur lors de la tentative de connexion de {email} : {str(e)}")
        return "Erreur interne", 500

@app.route('/modif_pwd', methods=['POST'])
def modif_pwd():
    # Récupération des données du formulaire
    email = request.form.get('email')
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    new_password_confirm = request.form.get('new_password_confirm')

    # Vérification que le nouveau mot de passe a été correctement répété
    if new_password != new_password_confirm:
        return """
            <script>
                alert("Les nouveaux mots de passe ne correspondent pas");
                window.location.href = "/logging_modif_pwd";
            </script>
        """

    # Vérification que le nouveau mot de passe est différent de l'ancien
    if new_password == old_password:
        return """
            <script>
                alert("Le nouveau mot de passe est identique à l'ancien. Veuillez le changer");
                window.location.href = "/logging_modif_pwd";
            </script>
        """

    # Vérification de la complexité du nouveau mot de passe
    if (len(new_password) < 12 or 
        not re.search(r'[A-Z]', new_password) or 
        not re.search(r'[a-z]', new_password) or 
        not re.search(r'\d', new_password) or 
        not re.search(r'[^A-Za-z0-9]', new_password)):
        return """
            <script>
                alert("Le nouveau mot de passe ne respecte pas les règle de sécurité : 12 caractères minimum contenant des lettres majuscules et minuscules des chiffres et des caractères spéciaux");
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

    # Mesurer le temps de début de la requête
    start_time = time.time()

    with engine_access_leg.connect() as connection:
        query = text("SELECT lg_accessible, lg_access_moy, lg_non_access, pourcent_access, pourcent_access_moy, pourcent_non_access FROM limite_admin.vm_commune_access")
        result = connection.execute(query).fetchone()

    # Calculer la durée d'exécution de la requête
    duration = time.time() - start_time
    logger.info(f"Exécution de la requête get_accessibility_data en {duration:.3f}s")

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

# ===========================================
# 🔁 API de calcul d'itinéraire piéton
# Cette route reçoit deux points (lon/lat) et utilise PGRouting (pgr_dijkstra)
# pour calculer l'itinéraire le plus court sur la table accessibilite.troncon_cheminement.
# Elle relie aussi dynamiquement les points de clic à leur nœud le plus proche
# avec des arcs temporaires créés à la volée.
# ===========================================

@app.route('/api/itineraire_coord', methods=['POST'])
def itineraire_coord():
    try:
        data = request.json
        logger.info(f"Données reçues : {data}")
        lon1, lat1 = data['start']
        lon2, lat2 = data['end']

        query = text("""
            WITH
            --Définition des points de départ et d’arrivée, transformés en projection métrique (EPSG:3857)
            point_depart AS (
                SELECT ST_Transform(ST_SetSRID(ST_MakePoint(:lon1, :lat1), 4326), 3857) AS geom
            ),
            point_arrivee AS (
                SELECT ST_Transform(ST_SetSRID(ST_MakePoint(:lon2, :lat2), 4326), 3857) AS geom
            ),

            -- Calcul du plus court chemin via pgr_dijkstra avec les tronçons + deux arcs virtuels départ/arrivée
            route AS (
                SELECT * FROM pgr_dijkstra(
                    $$
                    SELECT id, source, target, cost, reverse_cost, geom FROM (
                        SELECT
                            idtroncon AS id, from_id AS source, to_id AS target, lg_troncon AS cost, lg_troncon AS reverse_cost, geom
                        FROM accessibilite.troncon_cheminement

                        UNION ALL

                        SELECT * FROM (
                            SELECT
                                -1 AS id,
                                -1 AS source,
                                noeud.idnoeud AS target,
                                ST_Distance(noeud.geom, p.geom) AS cost,
                                ST_Distance(noeud.geom, p.geom) AS reverse_cost,
                                ST_MakeLine(p.geom, noeud.geom) AS geom
                            FROM accessibilite.noeud noeud,
                                (SELECT ST_Transform(ST_SetSRID(ST_MakePoint(:lon1, :lat1), 4326), 3857) AS geom) p
                            ORDER BY noeud.geom <-> p.geom
                            LIMIT 1
                        ) AS arc_depart

                        UNION ALL

                        SELECT * FROM (
                            SELECT
                                -2 AS id,
                                noeud.idnoeud AS source,
                                -2 AS target,
                                ST_Distance(noeud.geom, p.geom) AS cost,
                                ST_Distance(noeud.geom, p.geom) AS reverse_cost,
                                ST_MakeLine(p.geom, noeud.geom) AS geom
                            FROM accessibilite.noeud noeud,
                                (SELECT ST_Transform(ST_SetSRID(ST_MakePoint(:lon2, :lat2), 4326), 3857) AS geom) p
                            ORDER BY noeud.geom <-> p.geom
                            LIMIT 1
                        ) AS arc_arrivee
                    ) AS all_edges

                    $$,
                    -1, -2, directed := true
                )
            )
            -- Requête finale pour reconstruire la géométrie de l’itinéraire à partir des identifiants d’arêtes
            -- en incluant les géométries des tronçons classiques + les lignes virtuelles de début/fin
            SELECT ST_AsGeoJSON(e.geom) AS geojson, e.id, r.seq, r.cost
            FROM route r
            JOIN (
                SELECT id, source, target, cost, reverse_cost, geom FROM (
                    SELECT
                        idtroncon AS id, from_id AS source, to_id AS target, lg_troncon AS cost, lg_troncon AS reverse_cost, geom
                    FROM accessibilite.troncon_cheminement

                    UNION ALL

                    SELECT * FROM (
                        SELECT
                            -1 AS id,
                            -1 AS source,
                            n.idnoeud AS target,
                            ST_Distance(n.geom, p.geom) AS cost,
                            ST_Distance(n.geom, p.geom) AS reverse_cost,
                            ST_MakeLine(p.geom, n.geom) AS geom
                        FROM (
                            SELECT idnoeud, geom FROM accessibilite.noeud
                            ORDER BY geom <-> (
                                SELECT ST_Transform(ST_SetSRID(ST_MakePoint(:lon1, :lat1), 4326), 3857)
                            )
                            LIMIT 1
                        ) n,
                        (SELECT ST_Transform(ST_SetSRID(ST_MakePoint(:lon1, :lat1), 4326), 3857) AS geom) p
                    ) AS arc_depart

                    UNION ALL

                    SELECT * FROM (
                        SELECT
                            -1 AS id,
                            -1 AS source,
                            n.idnoeud AS target,
                            ST_Distance(n.geom, p.geom) AS cost,
                            ST_Distance(n.geom, p.geom) AS reverse_cost,
                            ST_MakeLine(p.geom, n.geom) AS geom
                        FROM (
                            SELECT idnoeud, geom FROM accessibilite.noeud
                            ORDER BY geom <-> (
                                SELECT ST_Transform(ST_SetSRID(ST_MakePoint(:lon1, :lat1), 4326), 3857)
                            )
                            LIMIT 1
                        ) n,
                        (SELECT ST_Transform(ST_SetSRID(ST_MakePoint(:lon1, :lat1), 4326), 3857) AS geom) p
                    ) AS arc_arrivee
                ) AS all_edges
            ) e ON r.edge = e.id
            ORDER BY r.seq;
        """)

        logger.info(f"Exécution de la requête avec lon1: {lon1}, lat1: {lat1}, lon2: {lon2}, lat2: {lat2}")

        with engine_access_leg.connect() as conn:
            result = conn.execute(query, {
                "lon1": lon1, "lat1": lat1,
                "lon2": lon2, "lat2": lat2
            }).mappings()
            features = []
            for row in result:
                geom = json.loads(row['geojson'])
                features.append({
                    "type": "Feature",
                    "geometry": geom,
                    "properties": {
                        "id": row['id'],
                        "seq": row['seq'],
                        "cost": row['cost']
                    }
                })
            return jsonify({"type": "FeatureCollection", "features": features})

    except Exception as e:
        logger.error(f"Erreur lors du calcul de l'itinéraire : {str(e)}")
        return jsonify({"error": str(e)}), 500    

@app.route('/api/get_nearest_node')
def get_nearest_node():
    lon = float(request.args.get("lon"))
    lat = float(request.args.get("lat"))
    with engine_access_leg.connect() as conn:
        query = text("""
            SELECT idnoeud
            FROM accessibilite.noeud
            ORDER BY geom <-> ST_Transform(ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), 3857)
            LIMIT 1
        """)
        result = conn.execute(query, {"lon": lon, "lat": lat}).mappings().fetchone()
        if result: # Retourne l'identifiant du nœud sous forme JSON si un résultat est trouvé
            return jsonify({"idnoeud": result[0]})
        else:
            return jsonify({"error": "Aucun nœud trouvé"}), 404

if __name__ == '__main__':
    logger.info("L'application Flask est sur le point de démarrer.")
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
        logger.info("L'application Flask fonctionne correctement.")
    except Exception as e:
        logger.error(f"Erreur lors du lancement de l'application Flask : {str(e)}")
