# Portfolio Project = nc-plus-one-seeding

This is the README file for the portfolio project

## Database Setup

To setup the database for this project execute the below terminal command from the project root directory:

```bash
psql -f db/setup.sql
```

It should then be possible to use the Postgres client to connect to the database using the below command:

```bash
psql -d nc_plus_one
```

## Database Connection

An `.env` file will require creation to allow secure management of credentials when connecting to the database through Python.
The format should be:

```none
DB_NAME=your_db_name
HOST=your_host
PASSWORD=your_password
```