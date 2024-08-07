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

    for batch in batches:
        # Send the command to run the shell script
        response = ssm_client.send_command(
            InstanceIds=batch,
            DocumentName="AWS-RunShellScript",
            Comment="Kill osb script on all ASG instances",
            Parameters={
                'commands': shell_script_commands
            }
        )

        # Get the command ID
        command_id = response['Command']['CommandId']
        print(f"Killed OSB on {len(batch)} instances")
        print(f"Command ID: {command_id}")

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

