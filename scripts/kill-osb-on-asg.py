import os

import boto3
from dotenv import load_dotenv

from asg_manager import list_asg_instances

def kill_osb_on_asg(ssm_client, host, instance_ids):
    # Define the shell script commands
    shell_script_commands = [
        '#!/bin/bash',
        'runuser -l ec2-user -c "pkill -f -9 opensearch-benchmark"',
        ''
    ]

    # Send the command to run the shell script
    response = ssm_client.send_command(
        InstanceIds=instance_ids,
        DocumentName="AWS-RunShellScript",
        Comment="Kill osb script on all ASG instances",
        Parameters={
            'commands': shell_script_commands
        }
    )

    # Get the command ID
    command_id = response['Command']['CommandId']
    print(f"Killed OSB on {instance_ids}. Command ID: {command_id}")

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

    host = ""

    tags = [
        {
            'Key': 'aws:autoscaling:groupName',
            'Value': 'scale_testing_demo',
            'PropagateAtLaunch': True
        }
    ]
    instance_ids = list_asg_instances(ec2, autoscaling, tags)

    kill_osb_on_asg(ssm_client, host, instance_ids)

