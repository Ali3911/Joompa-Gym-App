import logging
import os
from os import listdir
from os.path import isfile, join

import psycopg2
from dotenv import dotenv_values

logger = logging.getLogger(__name__)


def get_sql_filename(file_path: str):
    return [f for f in listdir(file_path) if isfile(join(file_path, f))]


base_path = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(base_path, "../.env")
db_config = dotenv_values(env_path)
path = os.path.join(base_path, "../database")
os.chdir(path)

con = psycopg2.connect(f"user={db_config['USER']} password='{db_config['PASSWORD']}'")
files = get_sql_filename(file_path=path)
if 0 < len(files) < 2 and str(files[0]).split(".")[1] == "sql":
    cursor = con.cursor()
    cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname='{db_config['NAME']}'")
    exists = cursor.fetchone()

    if not exists:
        logger.error(f"{db_config['NAME']} does not exist!")
        exit(-1)

    response = os.system(f' psql -h {db_config["HOST"]} -d {db_config["NAME"]} -U {db_config["USER"]} -f  {files[0]}')
else:
    logger.info("Database folder must have only and only a single .sql file.")
