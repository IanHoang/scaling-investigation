import os

import boto3
from dotenv import load_dotenv

from asg_manager import list_asg_instances

def run_osb_on_asg(ssm_client, host, instance_ids):
    print(instance_ids)

    # Define the shell script commands
    shell_script_commands = [
        '#!/bin/bash',
        f"runuser -l ec2-user -c \"screen -dmS SCALE_TESTING /home/ec2-user/run-osb-term-queries.sh osb-test {host}\"",
        ''
    ]

    # Send the command to run the shell script
    response = ssm_client.send_command(
        InstanceIds=instance_ids,
        DocumentName="AWS-RunShellScript",
        Comment="Run osb script on all ASG instances",
        Parameters={
            'commands': shell_script_commands
        }
    )

    # Get the command ID
    command_id = response['Command']['CommandId']
    print(f"Running OSB scripts on {instance_ids}. Command ID: {command_id}")

if __name__ == "__main__":
    load_dotenv()

    session = boto3.Session(
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION')
    )
    ec2 = session.client('ec2')
    autoscaling = session.client('autoscaling')
    ssm_client = session.client('ssm')

    host = os.getenv('HOST')

    tags = [
        {
            'Key': 'aws:autoscaling:groupName',
            'Value': os.getenv('AUTOSCALING_GROUP_NAME'),
            'PropagateAtLaunch': True
        }
    ]
    instance_ids = list_asg_instances(ec2, autoscaling, tags)

    run_osb_on_asg(ssm_client, host, instance_ids)


