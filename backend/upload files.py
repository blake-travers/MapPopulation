import os
import boto3
import concurrent.futures
from botocore.exceptions import ClientError
import threading
from dotenv import load_dotenv

# ==== CONFIG ====
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")
BUCKET_NAME = os.getenv("BUCKET_NAME")
LOCAL_DIRECTORY = "cog_tiles"
MAX_WORKERS = 32  # parallel uploads
# ===============

ENDPOINT = f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com"

session = boto3.session.Session()
s3 = session.client(
    service_name="s3",
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    endpoint_url=ENDPOINT
)

failed_uploads = []
lock = threading.Lock()

def upload_single(file_path, key):
    try:
        s3.upload_file(file_path, BUCKET_NAME, key)
        print(f"Uploaded: {key}")
    except Exception as e:
        print(f"FAILED: {key} -> {e}")
        with lock:
            failed_uploads.append(key)

def walk_all_files(root):
    for base, _, files in os.walk(root):
        for f in files:
            full_path = os.path.join(base, f)
            rel_path = os.path.relpath(full_path, root)
            yield full_path, rel_path.replace("\\", "/")

def main():
    all_files = list(walk_all_files(LOCAL_DIRECTORY))
    print(f"Uploading {len(all_files)} files...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for file_path, key in all_files:
            futures.append(executor.submit(upload_single, file_path, key))

        concurrent.futures.wait(futures)

    print("\n=== DONE ===")
    print(f"Total files: {len(all_files)}")
    print(f"Failed uploads: {len(failed_uploads)}")

    if failed_uploads:
        with open("failed_uploads.txt", "w") as f:
            f.write("\n".join(failed_uploads))
        print("Saved failed upload list to failed_uploads.txt")


import time

def retry_failed_uploads(max_retries=3, retry_delay=5):
    """
    Retry uploading files listed in `failed_uploads` or `failed_uploads.txt`.
    max_retries: number of retry attempts per file
    retry_delay: seconds to wait between retries
    """
    global failed_uploads

    # If there is a failed_uploads.txt file, load it
    if os.path.exists("failed_uploads.txt"):
        with open("failed_uploads.txt", "r") as f:
            lines = [line.strip() for line in f if line.strip()]
        failed_uploads = [(os.path.join(LOCAL_DIRECTORY, line), line) for line in lines]

    if not failed_uploads:
        print("No failed uploads to retry.")
        return

    print(f"\nRetry for {len(failed_uploads)} failed uploads...")
    current_failures = []

    for file_path, key in failed_uploads:
        try:
            s3.upload_file(file_path, BUCKET_NAME, key)
            print(f"Uploaded on retry: {key}")
        except Exception as e:
            print(f"Retry FAILED: {key} -> {e}")
            current_failures.append((file_path, key))


    # Update the failed_uploads.txt file
    if current_failures:
        with open("failed_uploads.txt", "w") as f:
            f.write("\n".join([k for _, k in current_failures]))
        print(f"{len(current_failures)} files still failed.")
    else:
        if os.path.exists("failed_uploads.txt"):
            os.remove("failed_uploads.txt")
        print("All previously failed uploads succeeded!")


if __name__ == "__main__":
    main()
    retry_failed_uploads()
