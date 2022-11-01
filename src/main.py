#!/usr/bin/env python
import http
from constructs import Construct
from cdktf import App, TerraformStack, S3Backend
from cdktf_cdktf_provider_aws.provider import AwsProvider

from src.datalake import DataLake
from src.policies import LambdaPolicies
from src.sandbox_ec2 import SandboxEC2


class FAICInfra(TerraformStack):
    """Terraform stack for Finance AI Consortium Lab AWS infrastructure"""

    def __init__(self, scope: Construct, ns: str):
        super().__init__(scope, ns)

        # Tags applied to all AWS resources
        tags = {"env": "test", "project": "cse-global-infra"}

        # AWS Provider
        AwsProvider(self, "AWS", region="ap-southeast-2")

        # Backend for storing state
        S3Backend(
            self,
            bucket="terraform-backend-faic-infra",
            key="v0/terraform.tfstate",
            region="ap-southeast-2",
        )

        # Policies holds a few Lambda Policies references (Logging etc.)
        self.policies = LambdaPolicies(self, "policies", tags=tags)
        # The Datalake with its rest api
        DataLake(self, "datalake", tags=tags)
        # Sandbox EC2
        SandboxEC2(self, "sandbox", tags=tags)


app = App()
FAICInfra(app, "cse-finai-infra")

app.synth()
