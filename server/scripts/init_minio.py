"""Initialize MinIO bucket and setup for PandaTales"""

import io
import json
import sys
from typing import Any

from minio import Minio
from minio.commonconfig import ENABLED, Filter
from minio.error import S3Error
from minio.lifecycleconfig import Expiration, LifecycleConfig, Rule

from app.core.config import get_settings

settings = get_settings()


def create_minio_client() -> Minio:
    """Create MinIO client"""
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )


def create_directory_structure(client: Minio, bucket: str) -> None:
    """Create directory structure by uploading marker objects"""
    
    directories = [
        # Template directories
        "templates/story-books/covers/",
        "templates/story-books/previews/",
        "templates/story-books/samples/",
        "templates/coloring-books/covers/",
        "templates/coloring-books/previews/",
        "templates/coloring-books/samples/",
        
        # Generated content directories
        "generated/books/story/pdfs/",
        "generated/books/story/covers/",
        "generated/books/story/pages/",
        "generated/books/coloring/pdfs/",
        "generated/books/coloring/covers/",
        "generated/books/coloring/pages/",
        "generated/temp/",
        
        # User content directories
        "users/avatars/",
        "users/uploads/photos/",
        
        # Public directories
        "public/assets/",
        "public/marketing/",
    ]

    print("\n📁 Creating directory structure...")
    for directory in directories:
        try:
            # Check if marker already exists
            try:
                client.stat_object(bucket, directory)
                print(f"   ✓ {directory} (already exists)")
                continue
            except S3Error:
                pass  # Doesn't exist, create it
            
            # Create directory marker (0-byte object with trailing slash)
            client.put_object(
                bucket,
                directory,
                data=io.BytesIO(b""),
                length=0,
                content_type="application/x-directory",
            )
            print(f"   ✓ {directory}")
        except S3Error as e:
            print(f"   ⚠ Error creating {directory}: {e}")


def set_bucket_policy(client: Minio, bucket: str) -> None:
    """Set bucket policy for public read access on specific paths"""
    
    print("\n🔐 Setting bucket policy...")
    
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicReadTemplates",
                "Effect": "Allow",
                "Principal": {"AWS": "*"},
                "Action": ["s3:GetObject"],
                "Resource": [
                    f"arn:aws:s3:::{bucket}/templates/*/covers/*",
                    f"arn:aws:s3:::{bucket}/templates/*/previews/*",
                    f"arn:aws:s3:::{bucket}/templates/*/samples/*",
                    f"arn:aws:s3:::{bucket}/public/*",
                ],
            },
            {
                "Sid": "PublicListTemplates",
                "Effect": "Allow",
                "Principal": {"AWS": "*"},
                "Action": ["s3:ListBucket"],
                "Resource": [f"arn:aws:s3:::{bucket}"],
                "Condition": {
                    "StringLike": {
                        "s3:prefix": [
                            "templates/*",
                            "public/*"
                        ]
                    }
                }
            }
        ],
    }

    try:
        client.set_bucket_policy(bucket, json.dumps(policy))
        print("   ✓ Bucket policy set successfully")
        print("   ℹ Public read access enabled for:")
        print("     - templates/*/covers/*")
        print("     - templates/*/previews/*")
        print("     - templates/*/samples/*")
        print("     - public/*")
    except S3Error as e:
        print(f"   ⚠ Error setting bucket policy: {e}")


def set_lifecycle_policy(client: Minio, bucket: str) -> None:
    """Set lifecycle policy to auto-delete temporary files"""
    
    print("\n⏱️  Setting lifecycle policy...")
    
    try:
        # Rule to delete temporary files after 7 days
        temp_rule = Rule(
            rule_id="delete-temp-files",
            rule_filter=Filter(prefix="generated/temp/"),
            status=ENABLED,
            expiration=Expiration(days=7),
        )
        
        config = LifecycleConfig([temp_rule])
        client.set_bucket_lifecycle(bucket, config)
        print("   ✓ Lifecycle policy set successfully")
        print("   ℹ Temporary files (generated/temp/) will be deleted after 7 days")
    except Exception as e:
        print(f"   ⚠ Error setting lifecycle policy: {e}")
        print("   ℹ This feature may not be available in older MinIO versions")


def print_summary(bucket: str) -> None:
    """Print setup summary"""
    
    print("\n" + "=" * 70)
    print("✅ MinIO setup completed successfully!")
    print("=" * 70)
    
    print(f"\n📦 Bucket: {bucket}")
    print(f"🌐 MinIO Console: http://{settings.MINIO_ENDPOINT.replace(':9000', ':9001')}")
    print(f"🔌 API Endpoint: http://{settings.MINIO_ENDPOINT}")
    print(f"👤 Access Key: {settings.MINIO_ACCESS_KEY}")
    print(f"🗂️  Region: {settings.MINIO_REGION}")
    
    print("\n📋 Directory Structure Created:")
    print("   ├── templates/")
    print("   │   ├── story-books/")
    print("   │   └── coloring-books/")
    print("   ├── generated/")
    print("   │   ├── books/")
    print("   │   └── temp/")
    print("   ├── users/")
    print("   │   ├── avatars/")
    print("   │   └── uploads/")
    print("   └── public/")
    
    print("\n🔐 Access Policies:")
    print("   ✓ Public read: templates/*, public/*")
    print("   ✓ Private: generated/*, users/*")
    
    print("\n⏱️  Lifecycle Policies:")
    print("   ✓ Temp files deleted after 7 days")
    
    print("\n🧪 Test with AWS CLI:")
    print(f"   export AWS_ACCESS_KEY_ID={settings.MINIO_ACCESS_KEY}")
    print(f"   export AWS_SECRET_ACCESS_KEY={settings.MINIO_SECRET_KEY}")
    print(f"   aws s3 ls s3://{bucket}/ --endpoint-url http://{settings.MINIO_ENDPOINT}")
    
    print("\n" + "=" * 70)


def setup_minio() -> None:
    """Main setup function for MinIO"""
    
    print("=" * 70)
    print("🐼 PandaTales MinIO Setup")
    print("=" * 70)
    
    bucket = settings.MINIO_BUCKET
    
    try:
        print("\n🔌 Connecting to MinIO...")
        client = create_minio_client()
        
        # Check if bucket exists
        print(f"\n📦 Checking bucket '{bucket}'...")
        if client.bucket_exists(bucket):
            print(f"   ✓ Bucket '{bucket}' already exists")
        else:
            # Create bucket
            client.make_bucket(bucket, location=settings.MINIO_REGION)
            print(f"   ✓ Created bucket '{bucket}'")
        
        # Create directory structure
        create_directory_structure(client, bucket)
        
        # Set bucket policy
        set_bucket_policy(client, bucket)
        
        # Set lifecycle policy
        set_lifecycle_policy(client, bucket)
        
        # Print summary
        print_summary(bucket)
        
    except S3Error as e:
        print(f"\n❌ MinIO Error: {e}")
        print(f"\nDetails:")
        print(f"   Endpoint: {settings.MINIO_ENDPOINT}")
        print(f"   Bucket: {bucket}")
        print(f"   Secure: {settings.MINIO_SECURE}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    setup_minio()

