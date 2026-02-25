"""Initialize MinIO bucket and setup for StoryBloom"""

import asyncio
import sys
from typing import Any

from minio import Minio
from minio.error import S3Error

from app.core.config import get_settings

settings = get_settings()


def create_minio_client() -> Minio:
    """Create MinIO client"""
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_USE_SSL,
    )


def setup_minio():
    """Setup MinIO bucket and policies"""
    print("Initializing MinIO setup...")

    try:
        client = create_minio_client()

        # Check if bucket exists
        bucket = settings.MINIO_BUCKET_NAME
        if client.bucket_exists(bucket):
            print(f"✓ Bucket '{bucket}' already exists")
        else:
            # Create bucket
            client.make_bucket(bucket)
            print(f"✓ Created bucket '{bucket}'")

        # Set bucket policy for public read on certain paths
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": ["s3:GetObject"],
                    "Resource": [
                        f"arn:aws:s3:::{bucket}/public/*",
                        f"arn:aws:s3:::{bucket}/covers/*",
                        f"arn:aws:s3:::{bucket}/pages/*",
                    ],
                }
            ],
        }

        import json

        client.set_bucket_policy(bucket, json.dumps(policy))
        print(f"✓ Set bucket policy for public read on specific paths")

        # Create directory structure
        directories = [
            "public/",
            "covers/",
            "pages/",
            "avatars/",
            "temp/",
        ]

        for directory in directories:
            # MinIO doesn't really have directories, but we can create empty objects
            # with trailing slashes to simulate them
            try:
                client.put_object(
                    bucket,
                    directory,
                    data=b"",
                    length=0,
                    content_type="application/x-directory",
                )
                print(f"✓ Created directory '{directory}'")
            except S3Error as e:
                if "ObjectAlreadyExists" not in str(e):
                    print(f"⚠ Error creating directory '{directory}': {e}")

        print("\n✅ MinIO setup completed successfully!")
        print(f"\nMinIO Console: http://{settings.MINIO_ENDPOINT}")
        print(f"Access Key: {settings.MINIO_ACCESS_KEY}")
        print(f"Bucket: {bucket}")

    except S3Error as e:
        print(f"\n❌ MinIO Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    setup_minio()
