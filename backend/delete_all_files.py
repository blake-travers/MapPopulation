import boto3
import os
from dotenv import load_dotenv

R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")
BUCKET_NAME = os.getenv("BUCKET_NAME")

ENDPOINT = f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com"

session = boto3.session.Session()
s3 = session.client(
    service_name="s3",
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    endpoint_url=ENDPOINT
)

def delete_all_files():
    paginator = s3.get_paginator("list_objects_v2")

    total_deleted = 0

    for page in paginator.paginate(Bucket=BUCKET_NAME):
        contents = page.get("Contents", [])
        if not contents:
            continue

        # S3/R2 allows deleting up to 1000 keys per request
        delete_batch = {"Objects": [{"Key": obj["Key"]} for obj in contents]}

        response = s3.delete_objects(
            Bucket=BUCKET_NAME,
            Delete=delete_batch
        )

        deleted_count = len(response.get("Deleted", []))
        total_deleted += deleted_count

        print(f"Deleted {deleted_count} files in this batch...")

    print(f"\nDone. Total deleted: {total_deleted}")

if __name__ == "__main__":
    delete_all_files()
