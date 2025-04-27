### creation du shémas authentification

CREATE SCHEMA IF NOT EXISTS authentification;

### creation table user

```
CREATE TABLE authentification.usager (
    id SERIAL PRIMARY KEY,
    utilisateur VARCHAR(255) NOT NULL UNIQUE,
    pwd VARCHAR(255) NOT NULL,
    type VARCHAR(10) CHECK (type IN ('interne', 'externe')),
    date_creat DATE DEFAULT CURRENT_DATE,
    validation BOOLEAN DEFAULT FALSE
);
```



