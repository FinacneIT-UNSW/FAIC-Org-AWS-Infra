import json
from constructs import Construct
from cdktf_cdktf_provider_aws.data_aws_vpc import DataAwsVpc
from cdktf_cdktf_provider_aws.data_aws_subnets import DataAwsSubnets
from cdktf_cdktf_provider_aws.data_aws_iam_policy_document import (
    DataAwsIamPolicyDocument,
)
from cdktf_cdktf_provider_aws.iam_role import IamRole
from cdktf_cdktf_provider_aws.iam_instance_profile import IamInstanceProfile
from cdktf_cdktf_provider_aws.security_group import SecurityGroup
from cdktf_cdktf_provider_aws.security_group_rule import SecurityGroupRule
from cdktf_cdktf_provider_aws.data_aws_ami import DataAwsAmi
from cdktf_cdktf_provider_aws.instance import Instance
from traitlets import default


class SandboxEC2(Construct):
    def __init__(self, scope: Construct, id: str, tags: dict):
        super().__init__(scope, id)

        vpc = DataAwsVpc(self, "vpc", default=True)

        subnets = DataAwsSubnets(
            self, "subnets", filter=[dict(name="vpc-id", values=[vpc.id])]
        )

        assume = DataAwsIamPolicyDocument(
            self,
            "assume",
            statement=[
                {
                    "actions": ["sts:AssumeRole"],
                    "principals": [
                        {
                            "type": "Service",
                            "identifiers": ["ec2.amazonaws.com"],
                        }
                    ],
                }
            ],
        )

        role = IamRole(
            self, "role", name="Sandbox-EC2", assume_role_policy=assume.json, tags=tags
        )

        ec2_profile = IamInstanceProfile(
            self, "profile", name="Sandbox-EC2-Profile", role=role.name
        )

        sg = SecurityGroup(
            self,
            "ec2-sg",
            description="Ultra permissive SG for sandbox EC2",
            vpc_id=vpc.id,
            tags=tags,
        )

        SecurityGroupRule(
            self,
            "egress-all",
            type="egress",
            security_group_id=sg.id,
            from_port=0,
            to_port=0,
            protocol="-1",
            cidr_blocks=["0.0.0.0/0"],
        )

        SecurityGroupRule(
            self,
            "http",
            type="ingress",
            security_group_id=sg.id,
            from_port=80,
            to_port=80,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"],
        )
        SecurityGroupRule(
            self,
            "https",
            type="ingress",
            security_group_id=sg.id,
            from_port=443,
            to_port=443,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"],
        )
        SecurityGroupRule(
            self,
            "ssh",
            type="ingress",
            security_group_id=sg.id,
            from_port=22,
            to_port=22,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"],
        )
        SecurityGroupRule(
            self,
            "grafana",
            type="ingress",
            security_group_id=sg.id,
            from_port=3000,
            to_port=3000,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"],
        )

        ami = DataAwsAmi(
            self,
            "ami",
            most_recent=True,
            owners=["amazon"],
            filter=[dict(name="name", values=["amzn2-ami-hvm-*-x86_64-ebs"])],
        )

        instance = Instance(
            self,
            "ec2",
            # ami=ami.id,
            ami="ami-064c4502381c426f4",
            instance_type="t3.micro",
            root_block_device=dict(volume_size=8),
            vpc_security_group_ids=[sg.id],
            iam_instance_profile=ec2_profile.name,
            tags=tags,
            key_name="sandbox",
            monitoring=False,
            disable_api_termination=False,
            ebs_optimized=True,
            user_data="""#! /bin/sh
            yum update -y
            amazon-linux-extras install docker
            service docker start
            usermod -a -G docker ec2-user
            chkconfig docker on
            """,
        )
