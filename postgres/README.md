# Postgres Pack

The `postgres.py` plugin will need to be updated with the database name, user and password.

```
# settings
HOST = 'localhost'
PORT = '5432'
DB = ''
USER = 'postgres'
PASSWORD = ''
```

If you want to create a non privileged user to run this script use:

```
CREATE ROLE dataloop WITH LOGIN ENCRYPTED PASSWORD 'changeme';
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO dataloop;
```

And set the settings block below to match these details.

