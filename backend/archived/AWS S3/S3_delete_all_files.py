import boto3
from botocore.exceptions import ClientError

BUCKET_NAME = "population-cog20"

PREFIX = None   # set to None to delete EVERYTHING

# Set to False to actually delete
DRY_RUN = True

s3 = boto3.client("s3")


def delete_all_objects(bucket, prefix=None, dry_run=True):
    paginator = s3.get_paginator("list_objects_v2")

    delete_count = 0

    for page in paginator.paginate(
        Bucket=bucket,
        Prefix=prefix or ""
    ):
        contents = page.get("Contents", [])
        if not contents:
            continue

        objects = [{"Key": obj["Key"]} for obj in contents]

        if dry_run:
            for obj in objects:
                print(f"[DRY RUN] Would delete: {obj['Key']}")
        else:
            response = s3.delete_objects(
                Bucket=bucket,
                Delete={"Objects": objects}
            )

            deleted = response.get("Deleted", [])
            errors = response.get("Errors", [])

            delete_count += len(deleted)

            for err in errors:
                print(f"ERROR deleting {err['Key']}: {err['Message']}")

    print(f"\nDone. Deleted {delete_count} objects.")


delete_all_objects(bucket=BUCKET_NAME,prefix=PREFIX,dry_run=DRY_RUN)
