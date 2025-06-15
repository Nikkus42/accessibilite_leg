# Projet Accessibilité

Il s'agit d'une application cartographique web est en cours de développement. 
Elle a été conçue dans le cadre d’un projet d’étude en gestion de projet géomatique.

### Cadre du pojet
L’agglomération fictive de Losse-en-Gelaisse, en tant qu’Autorité Organisatrice de la Mobilité, a confié la collecte de données sur l’accessibilité à un prestataire afin de répondre aux obligations de la Loi d’Orientation des Mobilités (LOM). Elle souhaite maintenant développer un outil web pour analyser les enjeux liés à l’accessibilité de son territoire.

### Sujet:
Développer une application web cartographique pour étudier les problématiques d’accessibilité d’un territoire. L’outil prend en compte l’offre de transports et la densité de population afin d’identifier les zones à prioriser.

### L'application 

Les données exploitées proviennent de l’open data Data Grand Lyon (Métropole de Lyon) ainsi que de l’INSEE (données démographiques).

L’application repose sur :

    - Un serveur cartographique Geoserver

    - Une application Python Flask

    - Un serveur web avec reverse proxy Nginx

    - Une base de données PostGres SQL - PostGIS pour le volet cartographique

    - Une base de données PostGres SQL pour la gestion des utilisateurs

Elle fonctionne avec Docker via un fichier docker-compose.

