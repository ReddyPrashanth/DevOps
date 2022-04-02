"""
description: generates cloud formation templates to run ec2 instance
author: @psreepathi
created_date: 4/1/2022
modified_date: 4/1/2022 
"""

from troposphere import (
    Base64,
    ec2,
    GetAtt,
    Join,
    Output,
    Parameter,
    Ref,
    Template,
)

application_port = "3000"

t = Template()
t.description = "Effective DevOps in AWS: helloWorld web application"
t.add_parameter(
    Parameter(
        "KeyPair",
        Description="Name of an existing keypair to SSH",
        Type="AWS::EC2::KeyPair::KeyName",
        ConstraintDescription="must be the name of an existing EC2 KeyPair"
    )
)
t.add_resource(ec2.SecurityGroup(
    "SecurityGroup",
    GroupDescription="Allow SSH and TCP/{} access".format(application_port),
    SecurityGroupIngress=[
        ec2.SecurityGroupRule(
            IpProtocol="tcp",
            FromPort="22",
            ToPort="22",
            CidrIp="0.0.0.0/0"
        ),
        ec2.SecurityGroupRule(
            IpProtocol="tcp",
            FromPort=application_port,
            ToPort=application_port,
            CidrIp="0.0.0.0/0"
        ),
    ]
))

ud = Base64(Join('\n', [
    "#!/bin/bash",
    "curl -fsSL https://rpm.nodesource.com/setup_17.x | bash -",
    "yum install -y nodejs",
    "mkdir /home/ec2-user/src",
    "wget https://raw.githubusercontent.com/ReddyPrashanth/DevOps/master/helloworld.js -O /home/ec2-user/src/helloworld.js",
    "wget https://raw.githubusercontent.com/ReddyPrashanth/DevOps/master/helloworld.service -O /lib/systemd/system/helloworld.service",
    "chown -R ec2-user:ec2-user /home/ec2-user/src",
    "systemctl daemon-reload",
    "systemctl start helloworld.service"
]))

t.add_resource(ec2.Instance(
    "instance",
    ImageId="ami-064ff912f78e3e561",
    InstanceType="t2.micro",
    SecurityGroups=[Ref("SecurityGroup")],
    KeyName=Ref("KeyPair"),
    UserData=ud
))

t.add_output(Output(
    "InstancePublicIp",
    Description="Public IP of our hello world instance",
    Value=GetAtt("instance", "PublicIp")
))

t.add_output(Output(
    "WebUrl",
    Description="Application endpoint",
    Value=Join("", [
        "http://",
        GetAtt("instance", "PublicDnsName"),
        ":",
        application_port
    ])
))

print(t.to_json())