import logging
import boto3
import traceback
import json
import os
import base64
import re


LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

REGION = os.environ.get("REGION", "ap-southeast-2")
session = boto3.Session(region_name=REGION)
s3 = session.client("s3")

BUCKET_NAME = "unsw-cse-model-repo"  # os.environ["BUCKET_NAME"]


def handler(event, context):

    try:
        LOGGER.info(f"Received event: {event}")

        model_name = event["pathParameters"]["model_name"].lower()
        model_version = event["pathParameters"]["model_version"].lower()

        url = s3.generate_presigned_url(
            "put_object",
            ExpiresIn=120,
            Params={
                "Key": f"{model_name}/{model_version}/{model_name}-{model_version}.zip",
                "Bucket": BUCKET_NAME,
                "ContentType": "application/zip",
            },
        )

        LOGGER.info(f"URL generated")

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "url": url,
                    "key": f"{model_name}/{model_version}/{model_name}-{model_version}.zip",
                }
            ),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }
    except Exception as e:
        LOGGER.error(f"Error generating url")
        traceback.print_exc()
        return {
            "statusCode": 500,
            "body": '{"status":"Server error"}',
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }
