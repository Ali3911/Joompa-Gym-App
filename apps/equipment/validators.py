import boto3

from joompa.settings import db_config

from django.core.exceptions import ValidationError


def validate_file_size(value):
    if value.size > 10485760:  # 10 MiB in bytes
        raise ValidationError("The maximum file size that can be uploaded is 10 MB")
    else:
        return value


def check_s3_bucket_access():
    try:
        s3 = boto3.resource(
            "s3",
            aws_access_key_id=db_config["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=db_config["AWS_SECRET_ACCESS_KEY"],
        )
        check = s3.Bucket(db_config["AWS_STORAGE_BUCKET_NAME"]) in s3.buckets.all()
        if check:
            return True
        else:
            return False
    except Exception:
        return False
