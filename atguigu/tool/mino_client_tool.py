import json

from minio import Minio

from atguigu.config.config import MinIoConfig
from atguigu.tool.logger import logger

minio_client = None

def get_minio_client():
    global minio_client

    if not minio_client:
        try:
            minio_client = Minio(
                endpoint=MinIoConfig.minio_endpoint,
                access_key=MinIoConfig.minio_access_key,
                secret_key=MinIoConfig.minio_secret_key,
                secure=False #禁用https
            )


            bucket_name = MinIoConfig.minio_bucket_name
            #创建桶

            if not minio_client.bucket_exists(bucket_name=bucket_name):
                minio_client.make_bucket(bucket_name=bucket_name)

            #设置权限 读公开 写认证
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "*"},
                        "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
                        "Resource": "arn:aws:s3:::my-bucket",
                    },
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "*"},
                        "Action": "s3:GetObject",
                        "Resource": "arn:aws:s3:::my-bucket/*",
                    },
                ],
            }
            minio_client.set_bucket_policy(bucket_name=bucket_name, policy = json.dumps(policy))
        except Exception as e:
            logger.error("minio客户端初始化失败")
            raise e
    return minio_client