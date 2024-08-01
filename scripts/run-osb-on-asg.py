import os
import argparse

import boto3
from dotenv import load_dotenv

from asg_manager import list_asg_instances

def run_osb_on_asg(ssm_client, host, instance_ids, test_execution_id):
    # Define the shell script commands
    shell_script_commands = [
        '#!/bin/bash',
        f"runuser -l ec2-user -c \"screen -dmS SCALE_TESTING /home/ec2-user/run-osb-term-queries.sh {test_execution_id} {host}\"",
        ''
    ]

    ### SSM has a max number of instances it can send commands to. Need to send them in batches
    batches = []
    batch = []
    for instance_id in instance_ids:
        if len(batch) == 50:
            batches.append(batch)
            batch = []
            # Need to add current instance id still
            batch.append(instance_id)
        else:
            batch.append(instance_id)

    # Add remainder if any
    batches.append(batch)

    print("Number of batches: ", len(batches))
    print("Batches: ", batches)

    # Send the command to run the shell script
    for batch in batches:
        response = ssm_client.send_command(
            InstanceIds=batch,
            DocumentName="AWS-RunShellScript",
            Comment="Run osb script on all ASG instances",
            Parameters={
                'commands': shell_script_commands
            }
        )

    # Get the command ID
        command_id = response['Command']['CommandId']
        print(f"Running OSB scripts on {len(batch)} instances")
        print(f"Command ID: {command_id}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Aggregate Results from MDS')
    parser.add_argument('--id', '-i', required=True, help='Test-execution-id to use for a round of experiments')
    args = parser.parse_args()

    load_dotenv()

    session = boto3.Session(
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION')
    )
    ec2 = session.client('ec2')
    autoscaling = session.client('autoscaling')
    ssm_client = session.client('ssm')

    host = os.getenv('TARGET_HOST')

    tags = [
        {
            'Key': 'aws:autoscaling:groupName',
            'Value': os.getenv('AUTOSCALING_GROUP_NAME'),
            'PropagateAtLaunch': True
        }
    ]
    instance_ids = list_asg_instances(ec2, autoscaling, tags)

    run_osb_on_asg(ssm_client, host, instance_ids, args.id)
