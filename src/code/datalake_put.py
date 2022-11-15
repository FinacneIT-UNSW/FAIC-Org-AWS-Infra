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

BUCKET_NAME = os.environ["BUCKET_NAME"]


def handler(event, context):

    try:
        LOGGER.info(f"Received event: {event}")

        layer = event["pathParameters"]["layer"].lower()
        source_type = event["pathParameters"]["source_type"].lower()
        source_name = event["pathParameters"]["source_name"].lower()
        ymd = event["pathParameters"]["ymd"].lower()
        table = event["pathParameters"]["table"].lower()

        TABLE_NAME = r"^(\w+\.)((csv)|(json)){1}$"
        table_name = re.search(TABLE_NAME, table)

        if layer not in ("bronze", "silver"):
            return {
                "statusCode": 400,
                "body": '{"status":"Invalid layer name. Available layers: bronze, silver"}',
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
            }

        if table_name is None:
            return {
                "statusCode": 400,
                "body": '{"status":"Invalid table name."}',
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
            }

        table_name = table_name.group()
        fformat = table_name.split(".")[1]

        url = s3.generate_presigned_url(
            "put_object",
            ExpiresIn=60,
            Params={
                "Key": f"{source_type}/{source_name}/{ymd}/{table_name}",
                "Bucket": BUCKET_NAME.replace("layer", layer),
                "ContentType": "application/json" if fformat == "json" else "text/csv",
            },
        )

        LOGGER.info(f"URL generated")

        return {
            "statusCode": 200,
            "body": json.dumps(
                {"url": url, "key": f"{source_type}/{source_name}/{ymd}/{table_name}"}
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
