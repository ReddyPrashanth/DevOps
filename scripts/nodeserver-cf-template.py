"""
description: generates cloud formation templates to run jenkins on ec2 instance
author: @psreepathi
created_date: 4/4/2022
modified_date: 4/4/2022 
"""

from ipaddress import ip_network
from requests import get
from troposphere import (
    Base64,
    ec2,
    GetAtt,
    Join,
    Output,
    Parameter,
    Ref,
    Template
)

from troposphere.iam import (
    InstanceProfile,
    PolicyType as IAMPolicy,
    Role
)

from awacs.aws import (
    Action,
    Allow,
    Policy,
    Principal,
    Statement
)

from awacs.sts import AssumeRole

ApplicationName = "nodeserver"
ApplicationPort = "3000"
GithubAccount = "ReddyPrashanth"
GithubAnsibleURL = "https://github.com/{}/devops-ansible".format(GithubAccount)

PublicIp = get('https://api.ipify.org').text
PublicCidrIp = str(ip_network(PublicIp))
 

AnsiblePullCmd = "/usr/bin/ansible-pull -U {} {}.yml -i localhost".format(GithubAnsibleURL, ApplicationName)

t = Template()

t.description = "Effective DevOps in AWS: Hello world application"

t.add_parameter(
    Parameter(
        "KeyPair",
        Description="Name of an existing EC2 KeyPair to SSH",
        Type="AWS::EC2::KeyPair::KeyName",
        ConstraintDescription="must be the name of an existing EC2 KeyPair"
    )
)

t.add_resource(
    ec2.SecurityGroup(
        "SecurityGroup",
        GroupDescription = "Allow SSH and TCP/{} access".format(ApplicationPort),
        SecurityGroupIngress=[
            ec2.SecurityGroupRule(
                IpProtocol="tcp",
                FromPort="22",
                ToPort="22",
                CidrIp=PublicCidrIp,
            ),
            ec2.SecurityGroupRule(
                IpProtocol="tcp",
                FromPort=ApplicationPort,
                ToPort=ApplicationPort,
                CidrIp="0.0.0.0/0"
            )
        ]
    )
)

ud = Base64(
    Join('\n', [
        "#!/bin/bash",
        "amazon-linux-extras install epel -y",
        "yum-config-manager --enable epel",
        "yum install --enablerepo=epel -y git",
        "yum install --enablerepo=epel -y ansible",
        AnsiblePullCmd
    ])
)

t.add_resource(Role(
    "Role",
    AssumeRolePolicyDocument=Policy(
        Statement=[
            Statement(
                Effect=Allow,
                Action=[AssumeRole],
                Principal=Principal("Service", ["ec2.amazonaws.com"])
            )
        ]
    )
))

t.add_resource(
    InstanceProfile(
        "InstanceProfile",
        Path="/",
        Roles=[Ref("Role")]
    )
)

t.add_resource(
    ec2.Instance(
        "instance",
        ImageId="ami-064ff912f78e3e561",
        InstanceType="t2.micro",
        SecurityGroups=[Ref("SecurityGroup")],
        KeyName=Ref("KeyPair"),
        UserData=ud,
        IamInstanceProfile=Ref("InstanceProfile")
    )
)

t.add_resource(IAMPolicy( 
    "Policy", 
    PolicyName="AllowS3", 
    PolicyDocument=Policy(
        Statement=[
            Statement(
                Effect=Allow, 
                Action=[Action("s3", "*")], 
                Resource=["*"])
        ]
    ),
    Roles=[Ref("Role")]
))

t.add_output(
    Output(
        "InstancePublicIp",
        Description="public IP of our instance",
        Value=GetAtt("instance", "PublicIp"),
    )
)

t.add_output(
    Output(
        "WebUrl",
        Description="Application endpoint",
        Value=Join("", [
            "http://",
            GetAtt("instance", "PublicDnsName"),
            ":",
            ApplicationPort
        ])
    )
)

print(t.to_json())