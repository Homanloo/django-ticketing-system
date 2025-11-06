from django.core.management.base import BaseCommand
from minio import Minio
from decouple import config
import os
import json


class Command(BaseCommand):
    help = 'Initialize MinIO buckets with proper policies'

    def handle(self, *args, **options):
        endpoint = os.getenv('MINIO_ENDPOINT')
        access_key = os.getenv('MINIO_ACCESS_KEY')
        secret_key = os.getenv('MINIO_SECRET_KEY')
        media_bucket = config('MINIO_MEDIA_BUCKET_NAME', default='media-bucket')
        static_bucket = config('MINIO_STATIC_BUCKET_NAME', default='static-bucket')

        client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False
        )

        # Policy to allow public read access (for presigned URLs to work)
        read_only_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": ["s3:GetObject"],
                    "Resource": "arn:aws:s3:::{bucket}/*"
                }
            ]
        }

        # Create media bucket
        if not client.bucket_exists(media_bucket):
            client.make_bucket(media_bucket)
            self.stdout.write(self.style.SUCCESS(f'Created bucket: {media_bucket}'))
        else:
            self.stdout.write(self.style.WARNING(f'Bucket already exists: {media_bucket}'))
        
        # Set policy for media bucket
        try:
            policy = json.dumps(read_only_policy).replace('{bucket}', media_bucket)
            client.set_bucket_policy(media_bucket, policy)
            self.stdout.write(self.style.SUCCESS(f'Set read policy for: {media_bucket}'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not set policy for {media_bucket}: {e}'))

        # Create static bucket
        if not client.bucket_exists(static_bucket):
            client.make_bucket(static_bucket)
            self.stdout.write(self.style.SUCCESS(f'Created bucket: {static_bucket}'))
        else:
            self.stdout.write(self.style.WARNING(f'Bucket already exists: {static_bucket}'))
        
        # Set policy for static bucket
        try:
            policy = json.dumps(read_only_policy).replace('{bucket}', static_bucket)
            client.set_bucket_policy(static_bucket, policy)
            self.stdout.write(self.style.SUCCESS(f'Set read policy for: {static_bucket}'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not set policy for {static_bucket}: {e}'))

        self.stdout.write(self.style.SUCCESS('MinIO initialization complete!'))

