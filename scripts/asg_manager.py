import os
import argparse

import boto3
from dotenv import load_dotenv

# Defaults
default_launch_config_name = 'osb-big5-term-queries'
default_instance_type = 'c5.large'
default_ami_id = 'ami-03b0d5dc13adfbcdd'  # Replace with your desired AMI ID
default_min_size = 1
default_max_size = 5
default_desired_capacity = 3
default_key_name = "hoangia-ee-iad"
default_security_group = "launch-wizard-53"

def list_asg_instances(ec2_client, autoscaling_client, tags):
    # ASG API cannot filter based on asg_name, thus we need to use tags
    instances = autoscaling_client.describe_auto_scaling_instances()['AutoScalingInstances']

    # Filter all ASG instances based on tags
    matched_instances = []
    for instance in instances:
        instance_id = instance['InstanceId']
        instance_tags = {tag['Key']: tag['Value'] for tag in ec2_client.describe_tags(
            Filters=[{'Name': 'resource-id', 'Values': [instance_id]}]
        )['Tags']}

        if all(instance_tags.get(tag['Key'], None) == tag['Value'] for tag in tags):
            matched_instances.append(instance_id)

    print("Instances to run on: ", matched_instances)
    return matched_instances

def provision_asg(autoscaling_client, asg_name, launch_config_name, instance_type, ami_id, min_size, max_size, desired_capacity, tags, key_name, security_group):
    # Create a launch configuration
    if does_launch_config_exist(autoscaling_client, launch_config_name):
        print("Launch configuraiton already exists")
    else:
        response_launch_config = autoscaling.create_launch_configuration(
            LaunchConfigurationName=launch_config_name,
            ImageId=ami_id,
            InstanceType=instance_type,
            KeyName=key_name,
            SecurityGroups=[security_group]
        )

        print("Launch configuration response: ", response_launch_config)

    region = os.getenv('AWS_REGION')
    availability_zones_suffixes = ['a', 'b', 'c', 'd']
    availability_zones = [region + availability_zones_suffixes[i] for i in range(len(availability_zones_suffixes))]

    try:
        # Create an auto scaling group
        response_auto_scaling_group = autoscaling_client.create_auto_scaling_group(
            AutoScalingGroupName=asg_name,
            LaunchConfigurationName=launch_config_name,
            MinSize=min_size,
            MaxSize=max_size,
            DesiredCapacity=desired_capacity,
            AvailabilityZones=availability_zones,  # Replace with your desired availability zones
            Tags=tags
        )
    except autoscaling_client.exceptions.AlreadyExistsFault as e:
        raise Exception("Auto scaling group resource exists: ", e)

    print("Autoscaling group response: ", response_auto_scaling_group)

def scale_out_asg(autoscaling_client, asg_name, updated_desired_capacity):
    response = autoscaling_client.update_auto_scaling_group(
        AutoScalingGroupName=asg_name,
        DesiredCapacity=updated_desired_capacity
    )
    print(response)

def delete_asg(ec2_client, autoscaling_client, asg_name, launch_config_name):
    # Terminate all instances in the auto scaling group
    instance_ids = [i['InstanceId'] for i in autoscaling.describe_auto_scaling_instances(AutoScalingGroupName=asg_name)['AutoScalingInstances']]
    if instance_ids:
        ec2_client.terminate_instances(InstanceIds=instance_ids)

    # Delete the auto scaling group
    autoscaling_client.delete_auto_scaling_group(AutoScalingGroupName=asg_name)

    # Delete the launch configuration
    autoscaling_client.delete_launch_configuration(LaunchConfigurationName=launch_config_name)

def does_launch_config_exist(autoscaling_client, launch_config_name):
    try:
        response = autoscaling_client.describe_launch_configurations(
            LaunchConfigurationNames=[launch_config_name]
        )
        print("Launch configurations: ", response['LaunchConfigurations'])
        if len(response['LaunchConfigurations']) > 0 and launch_config_name in response['LaunchConfigurations']:
            return True
        else:
            return False
    except autoscaling_client.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'InvalidLaunchConfiguration.NotFound':
            return False
        else:
            raise e

if __name__ == '__main__':
    load_dotenv()

    # Create clients for Auto Scaling and EC2
    session = boto3.Session(
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION')
    )
    autoscaling = session.client('autoscaling')
    ec2 = session.client('ec2')

    tags = [
        {
            'Key': 'TYPE',
            'Value': 'OSB_INVESTIGATION',
            'PropagateAtLaunch': True
        }
    ]

    parser = argparse.ArgumentParser(description='Manage Auto Scaling Groups')
    subparsers = parser.add_subparsers(dest='command')

    # create-asg command
    create_parser = subparsers.add_parser('create', help='Create a new Auto Scaling Group')
    create_parser.add_argument('--asg-name', '-n', required=True, help='Auto Scaling Group Name')
    create_parser.add_argument('--launch-config-name', '-l', default=default_launch_config_name, help='Launch Configuration Name')
    create_parser.add_argument('--instance-type', '-t', default=default_instance_type, help='Instance Type')
    create_parser.add_argument('--ami-id', '-i', default=default_ami_id, help='AMI ID')
    create_parser.add_argument('--min-size', '-min', type=int, default=default_min_size, help='Min size of auto scaling group')
    create_parser.add_argument('--max-size', '-max', type=int, default=default_max_size, help='Max size of auto scaling group')
    create_parser.add_argument('--desired-capacity', '-c', type=int, default=default_desired_capacity, help='Desired capacity of auto scaling group')
    create_parser.add_argument('--key-name', '-k', default=default_key_name, help='Key name to access instances')
    create_parser.add_argument('--security-group', '-s', default=default_security_group, help='Security group to use')

    # scale-asg command
    scale_parser = subparsers.add_parser('update', help='Update capacity of an existing Auto Scaling Group')
    scale_parser.add_argument('--asg-name', '-n', required=True, help='Auto Scaling Group Name')
    scale_parser.add_argument('--updated-desired-capacity', '-c', type=int, required=True, help='Updated Desired Capacity')

    # delete-asg command
    delete_parser = subparsers.add_parser('delete', help='Delete an Auto Scaling Group')
    delete_parser.add_argument('--asg-name', '-n', required=True, help='Auto Scaling Group Name')
    delete_parser.add_argument('--launch-config-name', '-l', required=True, help='Launch Config Name')

    list_parser = subparsers.add_parser('list-instances', help='list an Auto Scaling Group instances')

    args = parser.parse_args()

    if args.command == 'create':
        provision_asg(autoscaling, args.asg_name, args.launch_config_name, args.instance_type, args.ami_id, args.min_size, args.max_size, args.desired_capacity, tags, args.key_name, args.security_group)
    elif args.command == 'scale':
        scale_out_asg(autoscaling, args.asg_name, args.updated_desired_capacity)
    elif args.command == 'delete':
        delete_asg(ec2, autoscaling, args.asg_name, args.launch_config_name)
    elif args.command == "list-instances":
        list_asg_instances(ec2, autoscaling, tags)
    else:
        parser.print_help()
