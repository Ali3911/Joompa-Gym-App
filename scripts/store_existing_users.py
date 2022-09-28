import logging
import os

import pandas as pd
from dotenv import dotenv_values
from sqlalchemy import create_engine

base_path = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(base_path, "../.env")
db_config = dotenv_values(env_path)

logger = logging.getLogger(__name__)

try:
    engine = create_engine(
        f'postgresql://{db_config["USER"]}:{db_config["PASSWORD"]}@{db_config["HOST"]}:{db_config["PORT"]}/{db_config["NAME"]}'  # noqa: E501
    )

    ror_users_df = pd.read_sql_table("users", con=engine)
    django_users_df = ror_users_df[
        ["phone_number", "email", "password_digest", "last_name", "created_at", "updated_at", "first_name"]
    ]

    django_users_df = django_users_df.rename(columns={"password_digest": "password"})
    django_users_df["prefix"] = "bcrypt$"
    django_users_df["password"] = django_users_df["prefix"] + django_users_df["password"]
    del django_users_df["prefix"]
    django_users_df["is_staff"] = False
    django_users_df["is_active"] = True
    django_users_df["is_superuser"] = False
    django_users_df.to_sql("joompa_user", con=engine, if_exists="append", index=False)
    logger.info("All users from users table to joompa_user table have successfully copied.")
except Exception as e:
    message = "Error occurred while coping records from users table to joompa_user table."
    logger.exception(f"{message}:  {str(e)}")
