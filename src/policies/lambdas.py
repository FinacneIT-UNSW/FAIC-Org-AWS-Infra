import json
from constructs import Construct
from cdktf_cdktf_provider_aws.iam_policy import IamPolicy, IamPolicyConfig
from cdktf_cdktf_provider_aws.data_aws_iam_policy_document import (
    DataAwsIamPolicyDocument,
)


class LambdaPolicies(Construct):
    def __init__(self, scope: Construct, id: str, tags: dict):
        super().__init__(scope, id)

        self.logging = IamPolicy(
            self,
            "logging",
            name="LambdaLogging",
            policy=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
                            "Resource": ["arn:aws:logs:*:*:*"],
                            "Effect": "Allow",
                        }
                    ],
                }
            ),
            tags=tags,
        )

        self.assume = DataAwsIamPolicyDocument(
            self,
            "assume",
            statement=[
                {
                    "actions": ["sts:AssumeRole"],
                    "principals": [
                        {
                            "type": "Service",
                            "identifiers": ["lambda.amazonaws.com"],
                        }
                    ],
                }
            ],
        )
