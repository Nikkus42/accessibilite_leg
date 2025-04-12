# Creer sont espace de travail

nom : accessibilite_leg
URI de l'espace de nommage : http://localhost:8085/geoserver

Cocher espace de tavail par défault


# Configurer la connection Geoserver avec BDD postgis

## Il va y avoir autant de connection que de schemas dans notre BDD

Aller dans Etrepôts
Ajouter un nouvel entrepôts
Choisir PostGIS - PostGIS database

config:
Espace de travail: accessibilite_leg
Nom de la source de données: acess_leg_tvx
host : db
port: 5423
database: acess_leg
schemas : travaux
user et password: cf fichier .env

## Configurer les style

Recupérer les fichier SLD dans le dossier style_couche_geoserver

### On va configurer les style pour la couche "travaux":
allez dans style et ajouter un nouveau style

puis dans la configuraton du style:
Nom : travaux
Espace de travail : accessibilite_leg
Format : SLD
Fichier de style ==> charger le fichier travaux.sld.
cliquer sur les boutton sauvegarder et appliquer.

