# Configuration du géoserver

## Création de l’espace de travail

nom : accessibilite_leg<br>
URI de l'espace de nommage : http://localhost:8085/geoserver<br>

Cocher espace de tavail par défault


## Connexion du Geoserver à la base de données d’accessibilité

Le nombre de connexions dépend du nombre de schémas présents dans la base de données. Comme il y en a quatre, il faut répéter la configuration pour chaque schéma.

	1 Accéder à la section Entrepôts

	2 Ajouter un nouvel entrepôt

	3 Sélectionner PostGIS - PostGIS database

### Paramètres de configuration (exemple du schémas travaux):

    - Espace de travail : accessibilite_leg

    - Nom de la source de données :

        - access_leg_tvx

        - access_leg_lim_admin

        - access_leg_tpt (tpt pour transport)

        - access_leg_tvx (tvx pour travaux)

    - Hôte : db

    - Port : 5432

    - Base de données : access_leg

    - Schéma : travaux

    - Utilisateur et mot de passe : voir fichier .env

Liste des couches à configurées dans Geoserver :

    - arret (arrêt de bus) : schémas transport

	- ligne (ligne de bus): schémas transport

    - commune (limite communale): schémas admin

	- iris (limites iris - quartiers): schémas admin

    - erp: schémas accessibilité
    
    - stationnement_pmr: schémas accessibilité

    - troncon_cheminement: schémas accessibilité

	- travaux: schémas travaux

## Configuration des styles

Les fichiers SLD sont disponibles dans le dossier style_couche_geoserver.

### Configuration du style pour la couche "travaux"

    1 Accéder à la section Style

    2 Ajouter un nouveau style

    3 Paramétrer les informations suivantes :

        - Nom : travaux

        - Espace de travail : accessibilite_leg

        - Format : SLD

        Fichier de style : charger travaux.sld

    4 Enregistrer et appliquer

Répéter l’opération pour chaque couche.