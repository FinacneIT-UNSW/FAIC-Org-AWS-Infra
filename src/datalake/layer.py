import json
from constructs import Construct
from cdktf import TerraformOutput
from cdktf_cdktf_provider_aws.iam_policy import IamPolicy
from cdktf_cdktf_provider_aws.s3_bucket import S3Bucket
from cdktf_cdktf_provider_aws.api_gateway_rest_api import ApiGatewayRestApi
from cdktf_cdktf_provider_aws.api_gateway_resource import ApiGatewayResource
from cdktf_cdktf_provider_aws.api_gateway_deployment import ApiGatewayDeployment
from cdktf_cdktf_provider_aws.api_gateway_stage import ApiGatewayStage
from cdktf_cdktf_provider_aws.api_gateway_usage_plan import ApiGatewayUsagePlan
from cdktf_cdktf_provider_aws.api_gateway_api_key import ApiGatewayApiKey
from cdktf_cdktf_provider_aws.api_gateway_usage_plan_key import ApiGatewayUsagePlanKey
from cdktf_cdktf_provider_aws.api_gateway_rest_api import ApiGatewayRestApi
from cdktf_cdktf_provider_aws.api_gateway_resource import ApiGatewayResource
from cdktf_cdktf_provider_aws.api_gateway_method import ApiGatewayMethod
from cdktf_cdktf_provider_aws.api_gateway_integration import ApiGatewayIntegration
from cdktf_cdktf_provider_aws.iam_role import IamRole
from cdktf_cdktf_provider_aws.lambda_function import LambdaFunction
from cdktf_cdktf_provider_aws.lambda_permission import LambdaPermission
from cdktf_cdktf_provider_aws.cloudwatch_log_group import CloudwatchLogGroup


class DataLake(Construct):
    def __init__(self, scope: Construct, id: str, tags: dict):
        self.scope = scope
        super().__init__(scope, id)

        """Datalake
        
        Resources:
        ----------
            S3Buckets: holds data
            IamPolicy: grants CRUD access
        """

        # Bronze bucket for 'raw' data
        bronze_bucket = S3Bucket(
            self, "bucket", bucket=f"unsw-cse-bronze-lake", tags=tags
        )

        # Silver Bucket for 'processed' data
        silver_bucket = S3Bucket(
            self, "silver", bucket=f"unsw-cse-silver-lake", tags=tags
        )

        # CRUD Policy to datalake
        policies_crud = IamPolicy(
            self,
            "crud",
            name=f"S3-CRUD-unsw-cse-datalake",
            policy=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Action": [
                                "s3:PutObject",
                                "s3:PutObjectAcl",
                                "s3:GetObject",
                                "s3:GetObjectAcl",
                                "s3:DeleteObject",
                            ],
                            "Resource": [
                                f"{bronze_bucket.arn}/*",
                                f"{silver_bucket.arn}/*",
                            ],
                            "Effect": "Allow",
                        }
                    ],
                }
            ),
            tags=tags,
        )

        """Datalake API
        
        Resources:
        ----------
            ApiGatewayRestApi: The API garetway
            ApiGatewayResource: The paths of the API (/a/b/c etc.)
            ApiGatewayDeployment: The deployement of the API (making it accessible)
            ApiGatewayStage: A version of the api (v1)
            ApiGatewayUsagePlan: Limitation on API usage
            ApiGatewayApiKey: Access Key
            ApiGatewayUsagePlanKey: link key to usage plan
            DatalakeEndpoint: Set of resources to configure endpoints of the API (GET, PUT etc.)
        """
        api = ApiGatewayRestApi(
            self,
            "api",
            name="unsw-cse-DatalakeAPI",
            api_key_source="HEADER",
            endpoint_configuration={"types": ["REGIONAL"]},
            binary_media_types=["text/csv"],
            tags=tags,
        )

        resource_layer = ApiGatewayResource(
            self,
            "layer",
            path_part="{layer}",
            parent_id=api.root_resource_id,
            rest_api_id=api.id,
        )

        resource_source_type = ApiGatewayResource(
            self,
            "source-type",
            path_part="{source_type}",
            parent_id=resource_layer.id,
            rest_api_id=api.id,
        )

        resource_source_name = ApiGatewayResource(
            self,
            "source-name",
            path_part="{source_name}",
            parent_id=resource_source_type.id,
            rest_api_id=api.id,
        )

        resource_source_time = ApiGatewayResource(
            self,
            "source-time",
            path_part="{ymd}",
            parent_id=resource_source_name.id,
            rest_api_id=api.id,
        )

        resource = ApiGatewayResource(
            self,
            "source-table",
            path_part="{table}",
            parent_id=resource_source_time.id,
            rest_api_id=api.id,
        )

        deployement = ApiGatewayDeployment(
            self,
            "deployement",
            rest_api_id=api.id,
            # triggers={"redeployment": "1"},
            lifecycle={"create_before_destroy": True},
        )

        stage = ApiGatewayStage(
            self,
            "stage",
            deployment_id=deployement.id,
            rest_api_id=api.id,
            stage_name="v1",
            tags=tags,
        )

        plan = ApiGatewayUsagePlan(
            self,
            "plan",
            name="DatalakeAPIUsagePlan",
            api_stages=[{"apiId": api.id, "stage": stage.stage_name}],
            tags=tags,
        )

        key = ApiGatewayApiKey(self, "key", name=f"KEY-{api.name}", tags=tags)

        ApiGatewayUsagePlanKey(
            self, "usagekey", key_id=key.id, key_type="API_KEY", usage_plan_id=plan.id
        )

        put = DatalakeEndpoint(
            self,
            "put",
            http="PUT",
            api=api,
            policy=policies_crud,
            resource=resource,
            file_name="/root/unsw/cse-infra-v2/src/code/archived/datalake_put.zip",
            handler="datalake_put.handler",
            tags=tags,
        )

        get = DatalakeEndpoint(
            self,
            "get",
            http="GET",
            api=api,
            policy=policies_crud,
            resource=resource,
            file_name="/root/unsw/cse-infra-v2/src/code/archived/datalake_get.zip",
            handler="datalake_get.handler",
            tags=tags,
        )

        TerraformOutput(self, "datalake_api_endpoint", value=stage.invoke_url)
        TerraformOutput(self, "datalake_api_key_name", value=key.name)
        TerraformOutput(self, "datalake_api_key_value", value=key.value, sensitive=True)


class DatalakeEndpoint(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        http: str,
        api: ApiGatewayRestApi,
        resource: ApiGatewayResource,
        policy: IamPolicy,
        file_name: str,
        handler: str,
        tags: dict,
    ):
        super().__init__(scope, id)

        """Resources for endpoints
        
        Resources:
        ----------
            ApiGatewayMethod: GET, PUT, POST...
            IamRole: Role for the lambda (Crud on datalake, loging etc.)
            LambdaFunction: Lambda function handling the endpoint
            LambdaPermission: Allow lambda to be executed by the API
            ApiGatewayIntegration: Integration between API endpoint and lambda
            CloudwatchLogGroup: Logs
        """

        endpoint_method = ApiGatewayMethod(
            self,
            "methode",
            rest_api_id=api.id,
            resource_id=resource.id,
            http_method=http,
            authorization="NONE",
            api_key_required=True,
        )

        lambdas_role = IamRole(
            self,
            "role",
            name=f"{http}Datalake",
            assume_role_policy=scope.scope.policies.assume.json,
            managed_policy_arns=[
                scope.scope.policies.logging.arn,
                policy.arn,
                "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
            ],
            tags=tags,
        )

        function = LambdaFunction(
            self,
            "lambda",
            filename=file_name,
            function_name=f"{http}Datalake-Function",
            role=lambdas_role.arn,
            handler=handler,
            runtime="python3.9",
            memory_size=512,
            timeout=20,
            environment={
                "variables": {
                    "REGION": "ap-southeast-2",
                    "BUCKET_NAME": "unsw-cse-layer-lake",
                }
            },
            tags=tags,
        )

        permission = LambdaPermission(
            self,
            "permission",
            statement_id="AllowExecutionFromAPIGateway",
            action="lambda:InvokeFunction",
            function_name=function.function_name,
            principal="apigateway.amazonaws.com",
            source_arn="arn:aws:execute-api:ap-southeast-2:092201464628:*/*/*",
        )

        integration = ApiGatewayIntegration(
            self,
            "integration",
            rest_api_id=api.id,
            resource_id=resource.id,
            http_method=http,
            integration_http_method="POST",
            type="AWS_PROXY",
            uri=function.invoke_arn,
        )

        CloudwatchLogGroup(
            self,
            "logs",
            name=f"/aws/lambda/{function.function_name}",
            retention_in_days=30,
            tags=tags,
        )
