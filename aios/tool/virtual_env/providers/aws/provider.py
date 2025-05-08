import boto3
from botocore.exceptions import ClientError

import logging

from virtual_env.providers.base import Provider

logger = logging.getLogger("desktopenv.providers.aws.AWSProvider")
logger.setLevel(logging.INFO)

WAIT_DELAY = 15
MAX_ATTEMPTS = 10


class AWSProvider(Provider):

    def start_emulator(self, path_to_vm: str, headless: bool):
        logger.info("Starting AWS VM...")
        ec2_client = boto3.client('ec2', region_name=self.region)

        try:
            # Start the instance
            ec2_client.start_instances(InstanceIds=[path_to_vm])
            logger.info(f"Instance {path_to_vm} is starting...")

            # Wait for the instance to be in the 'running' state
            waiter = ec2_client.get_waiter('instance_running')
            waiter.wait(InstanceIds=[path_to_vm], WaiterConfig={'Delay': WAIT_DELAY, 'MaxAttempts': MAX_ATTEMPTS})
            logger.info(f"Instance {path_to_vm} is now running.")

        except ClientError as e:
            logger.error(f"Failed to start the AWS VM {path_to_vm}: {str(e)}")
            raise

    def get_ip_address(self, path_to_vm: str) -> str:
        logger.info("Getting AWS VM IP address...")
        ec2_client = boto3.client('ec2', region_name=self.region)

        try:
            response = ec2_client.describe_instances(InstanceIds=[path_to_vm])
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    private_ip_address = instance.get('PrivateIpAddress', '')
                    return private_ip_address
            return ''  # Return an empty string if no IP address is found
        except ClientError as e:
            logger.error(f"Failed to retrieve private IP address for the instance {path_to_vm}: {str(e)}")
            raise

    def save_state(self, path_to_vm: str, snapshot_name: str):
        logger.info("Saving AWS VM state...")
        ec2_client = boto3.client('ec2', region_name=self.region)

        try:
            image_response = ec2_client.create_image(InstanceId=path_to_vm, ImageId=snapshot_name)
            image_id = image_response['ImageId']
            logger.info(f"AMI {image_id} created successfully from instance {path_to_vm}.")
            return image_id
        except ClientError as e:
            logger.error(f"Failed to create AMI from the instance {path_to_vm}: {str(e)}")
            raise

    def revert_to_snapshot(self, path_to_vm: str, snapshot_name: str):
        logger.info(f"Reverting AWS VM to snapshot: {snapshot_name}...")
        ec2_client = boto3.client('ec2', region_name=self.region)

        try:
            # Step 1: Retrieve the original instance details
            instance_details = ec2_client.describe_instances(InstanceIds=[path_to_vm])
            instance = instance_details['Reservations'][0]['Instances'][0]
            security_groups = [sg['GroupId'] for sg in instance['SecurityGroups']]
            subnet_id = instance['SubnetId']
            instance_type = instance['InstanceType']

            # Step 2: Terminate the old instance
            ec2_client.terminate_instances(InstanceIds=[path_to_vm])
            logger.info(f"Old instance {path_to_vm} has been terminated.")

            # Step 3: Launch a new instance from the snapshot
            logger.info(f"Launching a new instance from snapshot {snapshot_name}...")

            run_instances_params = {
                "MaxCount": 1,
                "MinCount": 1,
                "ImageId": snapshot_name,
                "InstanceType": instance_type,
                "EbsOptimized": True,
                "NetworkInterfaces": [
                    {
                        "SubnetId": subnet_id,
                        "AssociatePublicIpAddress": True,
                        "DeviceIndex": 0,
                        "Groups": security_groups
                    }
                ]
            }

            new_instance = ec2_client.run_instances(**run_instances_params)
            new_instance_id = new_instance['Instances'][0]['InstanceId']
            logger.info(f"New instance {new_instance_id} launched from snapshot {snapshot_name}.")
            logger.info(f"Waiting for instance {new_instance_id} to be running...")
            ec2_client.get_waiter('instance_running').wait(InstanceIds=[new_instance_id])
            logger.info(f"Instance {new_instance_id} is ready.")

            return new_instance_id

        except ClientError as e:
            logger.error(f"Failed to revert to snapshot {snapshot_name} for the instance {path_to_vm}: {str(e)}")
            raise

    def stop_emulator(self, path_to_vm, region=None):
        logger.info(f"Stopping AWS VM {path_to_vm}...")
        ec2_client = boto3.client('ec2', region_name=self.region)

        try:
            ec2_client.stop_instances(InstanceIds=[path_to_vm])
            waiter = ec2_client.get_waiter('instance_stopped')
            waiter.wait(InstanceIds=[path_to_vm], WaiterConfig={'Delay': WAIT_DELAY, 'MaxAttempts': MAX_ATTEMPTS})
            logger.info(f"Instance {path_to_vm} has been stopped.")
        except ClientError as e:
            logger.error(f"Failed to stop the AWS VM {path_to_vm}: {str(e)}")
            raise
