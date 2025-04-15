# Creation des 4 shémas

-- Créer le schéma 'travaux' si nécessaire <br>
CREATE SCHEMA IF NOT EXISTS travaux;

-- Créer le schéma 'accessibilite' si nécessaire<br>
CREATE SCHEMA IF NOT EXISTS accessibilite;

-- Créer le schéma 'transport' si nécessaire<br>
CREATE SCHEMA IF NOT EXISTS transport;

-- Créer le schéma 'limite_admin' si nécessaire<br>
CREATE SCHEMA IF NOT EXISTS limite_admin;

# Création d'une vue matérialisé d'indicateur
Pour chaque quartier IRIS la formule est:<br>
(longueur troncon non accessible +(longueur toncon accessiilité moyenne / 2) * popultation iris) / population agglomération<br>

la VM fait appelle à 3 tables:<br>

- limite_admin.iris<br>
- accessibilite.troncon_cheminement<br>
- limite_admin.population_iris<br>


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

# Rafraichissement de la VM ==> création d'une fonction et de 3 trigger

## Création de la fonction de rafraichissement de la VM

```
CREATE OR REPLACE FUNCTION limite_admin.refresh_vm_iris_indicateur()
RETURNS TRIGGER AS $$
BEGIN
    REFRESH MATERIALIZED VIEW limite_admin.vm_iris_indicateur;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
```


## Création trigger sur table limite_admin.iris

```
CREATE TRIGGER refresh_vm_iris_indicateur_iris_trigger
AFTER INSERT OR UPDATE OR DELETE ON limite_admin.iris
FOR EACH STATEMENT
EXECUTE FUNCTION limite_admin.refresh_vm_iris_indicateur();
```

## Création trigger sur table accessibilite.troncon_cheminement

```
CREATE TRIGGER refresh_vm_iris_indicateur_troncon_trigger
AFTER INSERT OR UPDATE OR DELETE ON accessibilite.troncon_cheminement
FOR EACH STATEMENT
EXECUTE FUNCTION limite_admin.refresh_vm_iris_indicateur();
```

## Création trigger sur table limite_admin.population_iris

```
CREATE TRIGGER refresh_vm_iris_indicateur_population_trigger
AFTER INSERT OR UPDATE OR DELETE ON limite_admin.population_iris
FOR EACH STATEMENT
EXECUTE FUNCTION limite_admin.refresh_vm_iris_indicateur();
```