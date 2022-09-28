# flake8: noqa
import logging
import os

import psycopg2
from dotenv import dotenv_values

logger = logging.getLogger(__name__)

base_path = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(base_path, "../.env")
db_config = dotenv_values(env_path)
con = None
cur = None
try:
    con = psycopg2.connect(
        host=db_config["HOST"], database=db_config["NAME"], user=db_config["USER"], password=db_config["PASSWORD"]
    )

    cur = con.cursor()
    cur.execute("select * from information_schema.tables where table_name='users'")
    if cur.rowcount == 0:
        logger.error("ROR users table doesn't exist in the database.")
        exit(-1)

    cur.execute("select * from information_schema.tables where table_name='joompa_user'")
    if cur.rowcount == 0:
        logger.error("Django users table doesn't exist in the database.")
        exit(-1)

    cur.execute(
        """
    CREATE OR REPLACE FUNCTION login_user_sync() RETURNS TRIGGER AS $user_sync$
        BEGIN
            IF (TG_OP = 'DELETE') THEN
                DELETE FROM public.joompa_user WHERE email=OLD.email;
                return OLD;
            ELSIF (TG_OP = 'UPDATE') THEN
                UPDATE public.joompa_user
                SET  password=concat('bcrypt$',NEW.password_digest), first_name=NEW.first_name, last_name=NEW.last_name,
                is_staff=false, is_active=true, is_superuser=false, phone_number=NEW.phone_number
                WHERE email=NEW.email;
                RETURN NEW;
            ELSIF (TG_OP = 'INSERT') THEN
                INSERT INTO public.joompa_user(
                password, email,phone_number, first_name, last_name, is_staff, is_active, is_superuser)
                VALUES (concat('bcrypt$',NEW.password_digest), NEW.email,NEW.phone_number, NEW.first_name, NEW.last_name, false, true, false);
                RETURN NEW;
            END IF;
            RETURN NULL; -- result is ignored since this is an AFTER trigger
        END;
    $user_sync$ LANGUAGE plpgsql;
    """
    )

    cur.execute(
        """
        CREATE TRIGGER syncronize_users
        AFTER INSERT OR DELETE OR UPDATE
        ON public.users
        FOR EACH ROW
        EXECUTE FUNCTION public.login_user_sync();

    COMMENT ON TRIGGER syncronize_users ON public.users
        IS 'sync users tables within joompa_user';
    """
    )
    con.commit()
except (Exception, psycopg2.DatabaseError) as error:
    logger.exception("Error occured while connecting to PostgreSQL", error)

finally:
    # closing database connection.
    if con:
        cur.close()
        con.close()
        logger.info("PostgreSQL connection is closed after applying trigger and functions.")
