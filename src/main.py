#!/usr/bin/env python
import http
from constructs import Construct
from cdktf import App, TerraformStack
from cdktf_cdktf_provider_aws.provider import AwsProvider

from src.datalake import DataLake
from src.policies import LambdaPolicies


class MyStack(TerraformStack):
    def __init__(self, scope: Construct, ns: str):
        super().__init__(scope, ns)

        tags = {"env": "test", "project": "cse-global-infra"}

        AwsProvider(self, "AWS", region="ap-southeast-2")

        self.policies = LambdaPolicies(self, "policies", tags=tags)

        landing = DataLake(self, "datalake", tags=tags)


app = App()
MyStack(app, "cse-finai-infra")

app.synth()
