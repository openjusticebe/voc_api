# voc_api
A microservice API to link vocabulary terms to items through their respective iri's.

## Vocabulary terms ?
**Voc_api** uses [SPARQL](https://fr.wikipedia.org/wiki/SPARQL) endpoints to search for semantic vocabularies and ontologies.

## Items ?
Elements, things : anything, really, as long as it has an [IRI](https://datatracker.ietf.org/doc/html/rfc3987).

## Development

For the moment, install & run with poetry

```bash
poetry install
poetry run api --debug
```

### Database
A PostGRESQL DB has to be available

```
docker run --name vocapi-postgres -v postgres-data:/var/lib/postgresql/data \
    -p 5432:5432 \
    -e POSTGRES_USER=vocapi -e POSTGRES_PASSWORD=vocapi \
    -d postgres:14
```

With a proper [schema](./ressources/schema.sql)), using above docker:
```
# Erases any existing data, run at your own risk
psql -Atx postgres://vocapi:vocapi@localhost:5432/vocapi \
    -f ./ressources/schema.sql
```

### Environment
Don't forget to set a dotenv file (see [config](./voc_api/lib_cfg.py) file
for details)

```
cat > .env <<- EOF
SPARQL_ENDPOINT=[http://example.com/endpoint/sparql]
PG_DSN=[postgres://vocapi:vocapi@localhost:5432/db]
EOF
```
