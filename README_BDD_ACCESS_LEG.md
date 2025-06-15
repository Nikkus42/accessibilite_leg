# Base de données access_leg:

Cette base de données regroupe les données affichées dans l’application web SIG.<br> 
Elle comporte quatre schémas.

## Création des 4 shémas:

-- Créer le schéma 'travaux': <br>
CREATE SCHEMA IF NOT EXISTS travaux;

-- Créer le schéma 'accessibilite':<br>
CREATE SCHEMA IF NOT EXISTS accessibilite;

-- Créer le schéma 'transport':<br>
CREATE SCHEMA IF NOT EXISTS transport;

-- Créer le schéma 'limite_admin':<br>
CREATE SCHEMA IF NOT EXISTS limite_admin;

# Création des tables:

Les tables ont été créées et les données injectées dans cette base de données via le gestionnaire DB de l'outil SIG QGIS.

# Création de la vue matérialisée d'indicateurs

Le projet prévoit des indicateurs d’accessibilité permettant à l’agglomération d’identifier les zones du territoire nécessitant des aménagements pour améliorer la circulation des personnes en situation de handicap.

Un indicateur a été conçu pour mettre en évidence les quartiers IRIS où l’accessibilité est limitée.<br>
La formule de calcul appliquée à chaque quartier IRIS est la suivante :<br>
```
(longueur troncon non accessible +(longueur toncon accessilité moyenne / 2) * population iris) / population agglomération
```

Cette fomule prend en compte les longueurs de tronçons selon leur niveau d’accessibilité et les met en relation avec la population du quartier.

### La VM fait appelle à 3 tables:<br>

- limite_admin.iris<br>
- accessibilite.troncon_cheminement<br>
- limite_admin.population_iris<br>

Script de création de la VM:


```
CREATE MATERIALIZED VIEW limite_admin.vm_iris_indicateur AS
WITH longueur_lignes AS (
    SELECT
        i.nom_iris AS nom_iris,
        i.code_iris AS code_iris,
        i.geom AS geom_iris,
        SUM(
            ST_Length(
                ST_Transform(ST_Intersection(t.geom, i.geom), 2154)
            )
        ) FILTER (WHERE t.accessibiliteglobale = 'accessible') AS lg_accessible,
        SUM(
            ST_Length(
                ST_Transform(ST_Intersection(t.geom, i.geom), 2154)
            )
        ) FILTER (WHERE t.accessibiliteglobale = 'accessibilité moyenne') AS lg_access_moy,
        SUM(
            ST_Length(
                ST_Transform(ST_Intersection(t.geom, i.geom), 2154)
            )
        ) FILTER (WHERE t.accessibiliteglobale = 'non accessible') AS lg_non_access
    FROM
        limite_admin.iris i
    JOIN
        accessibilite.troncon_cheminement t
    ON
        ST_Intersects(i.geom, t.geom)
    GROUP BY
        i.nom_iris, i.code_iris, i.geom
),
calculs_pourcentages AS (
    SELECT
        nom_iris,
        code_iris,
        geom_iris,
        lg_accessible,
        lg_access_moy,
        lg_non_access,
        (COALESCE(lg_accessible, 0) + COALESCE(lg_access_moy, 0) + COALESCE(lg_non_access, 0)) AS longueur_totale
    FROM
        longueur_lignes
),
arrondis_pourcentages AS (
    SELECT
        nom_iris,
        code_iris,
        geom_iris,
        lg_accessible,
        lg_access_moy,
        lg_non_access,
        longueur_totale,
        FLOOR((COALESCE(lg_accessible, 0) / NULLIF(longueur_totale, 0)) * 100) AS pourcent_access_brut,
        FLOOR((COALESCE(lg_access_moy, 0) / NULLIF(longueur_totale, 0)) * 100) AS pourcent_access_moy_brut,
        FLOOR((COALESCE(lg_non_access, 0) / NULLIF(longueur_totale, 0)) * 100) AS pourcent_non_access_brut
    FROM
        calculs_pourcentages
),
population_data AS (
    SELECT
        iris AS iris_pop,
        p20_pop AS population_iris
    FROM
        limite_admin.population_iris
),
indic_calcul AS (
    SELECT
        ap.nom_iris,
        ap.code_iris,
        ap.geom_iris,
        ap.lg_accessible,
        ap.lg_access_moy,
        ap.lg_non_access,
        ap.pourcent_access_brut +
            CASE WHEN (ap.pourcent_access_brut + ap.pourcent_access_moy_brut + ap.pourcent_non_access_brut) < 100 THEN
                1 ELSE 0 END AS pourcent_access,
        ap.pourcent_access_moy_brut +
            CASE WHEN (ap.pourcent_access_brut + ap.pourcent_access_moy_brut + ap.pourcent_non_access_brut) > 100 THEN
                -1 ELSE 0 END AS pourcent_access_moy,
        ap.pourcent_non_access_brut AS pourcent_non_access,
        p.population_iris,
        (ap.lg_non_access + (ap.lg_access_moy / 2)) * p.population_iris AS raw_indic
    FROM
        arrondis_pourcentages ap
    LEFT JOIN
        population_data p
    ON
        ap.code_iris = p.iris_pop
),
total_population AS (
    SELECT
        SUM(population_iris) AS total_population
    FROM
        population_data
)
SELECT
    i.nom_iris,
    i.code_iris,
    i.geom_iris,
    i.lg_accessible,
    i.lg_access_moy,
    i.lg_non_access,
    i.pourcent_access,
    i.pourcent_access_moy,
    i.pourcent_non_access,
    COALESCE(i.population_iris, 0) AS population_iris,
    COALESCE(i.raw_indic / t.total_population, 0) AS indicateur
FROM
    indic_calcul i,
    total_population t;
    
```

## Rafraichissement de la VM 

Une fonction et trois triggers ont été créés pour mettre à jour la vue après chaque modification des données.

### Création de la fonction de rafraichissement

```
CREATE OR REPLACE FUNCTION limite_admin.refresh_vm_iris_indicateur()
RETURNS TRIGGER AS $$
BEGIN
    REFRESH MATERIALIZED VIEW limite_admin.vm_iris_indicateur;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
```


### Création des trigger

- Sur table limite_admin.iris:

```
CREATE TRIGGER refresh_vm_iris_indicateur_iris_trigger
AFTER INSERT OR UPDATE OR DELETE ON limite_admin.iris
FOR EACH STATEMENT
EXECUTE FUNCTION limite_admin.refresh_vm_iris_indicateur();
```

- Sur accessibilite.troncon_cheminement:

```
CREATE TRIGGER refresh_vm_iris_indicateur_troncon_trigger
AFTER INSERT OR UPDATE OR DELETE ON accessibilite.troncon_cheminement
FOR EACH STATEMENT
EXECUTE FUNCTION limite_admin.refresh_vm_iris_indicateur();
```

- Sur limite_admin.population_iris:

```
CREATE TRIGGER refresh_vm_iris_indicateur_population_trigger
AFTER INSERT OR UPDATE OR DELETE ON limite_admin.population_iris
FOR EACH STATEMENT
EXECUTE FUNCTION limite_admin.refresh_vm_iris_indicateur();
```