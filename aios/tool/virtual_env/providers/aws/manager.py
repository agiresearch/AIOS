import os
from filelock import FileLock
import boto3
import psutil
import logging

from virtual_env.providers.base import VMManager

logger = logging.getLogger("desktopenv.providers.aws.AWSVMManager")
logger.setLevel(logging.INFO)

REGISTRY_PATH = '.aws_vms'

DEFAULT_REGION = "us-east-1"
# todo: Add doc for the configuration of image, security group and network interface
# todo: public the AMI images
IMAGE_ID_MAP = {
    "us-east-1": "ami-05e7d7bd279ea4f14",
    "ap-east-1": "ami-0c092a5b8be4116f5"
}

INSTANCE_TYPE = "t3.medium"

NETWORK_INTERFACE_MAP = {
    "us-east-1": [
        {
            "SubnetId": "subnet-037edfff66c2eb894",
            "AssociatePublicIpAddress": True,
            "DeviceIndex": 0,
            "Groups": [
                "sg-0342574803206ee9c"
            ]
        }
    ],
    "ap-east-1": [
        {
            "SubnetId": "subnet-011060501be0b589c",
            "AssociatePublicIpAddress": True,
            "DeviceIndex": 0,
            "Groups": [
                "sg-090470e64df78f6eb"
            ]
        }
    ]
}


def _allocate_vm(region=DEFAULT_REGION):
    run_instances_params = {
        "MaxCount": 1,
        "MinCount": 1,
        "ImageId": IMAGE_ID_MAP[region],
        "InstanceType": INSTANCE_TYPE,
        "EbsOptimized": True,
        "NetworkInterfaces": NETWORK_INTERFACE_MAP[region]
    }

    ec2_client = boto3.client('ec2', region_name=region)
    response = ec2_client.run_instances(**run_instances_params)
    instance_id = response['Instances'][0]['InstanceId']
    logger.info(f"Waiting for instance {instance_id} to be running...")
    ec2_client.get_waiter('instance_running').wait(InstanceIds=[instance_id])
    logger.info(f"Instance {instance_id} is ready.")

    return instance_id


class AWSVMManager(VMManager):
    def __init__(self, registry_path=REGISTRY_PATH):
        self.registry_path = registry_path
        self.lock = FileLock(".aws_lck", timeout=60)
        self.initialize_registry()

    def initialize_registry(self):
        with self.lock:  # Locking during initialization
            if not os.path.exists(self.registry_path):
                with open(self.registry_path, 'w') as file:
                    file.write('')

    def add_vm(self, vm_path, region=DEFAULT_REGION, lock_needed=True):
        if lock_needed:
            with self.lock:
                self._add_vm(vm_path, region)
        else:
            self._add_vm(vm_path, region)

    def _add_vm(self, vm_path, region=DEFAULT_REGION):
        with open(self.registry_path, 'r') as file:
            lines = file.readlines()
            vm_path_at_vm_region = "{}@{}".format(vm_path, region)
            new_lines = lines + [f'{vm_path_at_vm_region}|free\n']
        with open(self.registry_path, 'w') as file:
            file.writelines(new_lines)

    def delete_vm(self, vm_path, region=DEFAULT_REGION, lock_needed=True):
        if lock_needed:
            with self.lock:
                self._delete_vm(vm_path, region)
        else:
            self._delete_vm(vm_path, region)

    def _delete_vm(self, vm_path, region=DEFAULT_REGION):
        new_lines = []
        with open(self.registry_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                vm_path_at_vm_region, pid_str = line.strip().split('|')
                if vm_path_at_vm_region == "{}@{}".format(vm_path, region):
                    continue
                else:
                    new_lines.append(line)
        with open(self.registry_path, 'w') as file:
            file.writelines(new_lines)

    def occupy_vm(self, vm_path, pid, region=DEFAULT_REGION, lock_needed=True):
        if lock_needed:
            with self.lock:
                self._occupy_vm(vm_path, pid, region)
        else:
            self._occupy_vm(vm_path, pid, region)

    def _occupy_vm(self, vm_path, pid, region=DEFAULT_REGION):
        new_lines = []
        with open(self.registry_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                registered_vm_path, _ = line.strip().split('|')
                if registered_vm_path == "{}@{}".format(vm_path, region):
                    new_lines.append(f'{registered_vm_path}|{pid}\n')
                else:
                    new_lines.append(line)
        with open(self.registry_path, 'w') as file:
            file.writelines(new_lines)

    def check_and_clean(self, lock_needed=True):
        if lock_needed:
            with self.lock:
                self._check_and_clean()
        else:
            self._check_and_clean()

    def _check_and_clean(self):
        # Get active PIDs
        active_pids = {p.pid for p in psutil.process_iter()}

        new_lines = []
        vm_path_at_vm_regions = {}

        with open(self.registry_path, 'r') as file:
            lines = file.readlines()

        # Collect all VM paths and their regions
        for line in lines:
            vm_path_at_vm_region, pid_str = line.strip().split('|')
            vm_path, vm_region = vm_path_at_vm_region.split("@")
            if vm_region not in vm_path_at_vm_regions:
                vm_path_at_vm_regions[vm_region] = []
            vm_path_at_vm_regions[vm_region].append((vm_path_at_vm_region, pid_str))

        # Process each region
        for region, vm_info_list in vm_path_at_vm_regions.items():
            ec2_client = boto3.client('ec2', region_name=region)
            instance_ids = [vm_info[0].split('@')[0] for vm_info in vm_info_list]

            # Batch describe instances
            try:
                response = ec2_client.describe_instances(InstanceIds=instance_ids)
                reservations = response.get('Reservations', [])

                terminated_ids = set()
                stopped_ids = set()
                active_ids = set()

                # Collect states of all instances
                for reservation in reservations:
                    for instance in reservation.get('Instances', []):
                        instance_id = instance.get('InstanceId')
                        instance_state = instance['State']['Name']
                        if instance_state in ['terminated', 'shutting-down']:
                            terminated_ids.add(instance_id)
                        elif instance_state == 'stopped':
                            stopped_ids.add(instance_id)
                        else:
                            active_ids.add(instance_id)

                # Write results back to file
                for vm_path_at_vm_region, pid_str in vm_info_list:
                    vm_path = vm_path_at_vm_region.split('@')[0]

                    if vm_path in terminated_ids:
                        logger.info(f"VM {vm_path} not found or terminated, releasing it.")
                        continue
                    elif vm_path in stopped_ids:
                        logger.info(f"VM {vm_path} stopped, mark it as free")
                        new_lines.append(f'{vm_path}@{region}|free\n')
                        continue

                    if pid_str == "free":
                        new_lines.append(f'{vm_path}@{region}|{pid_str}\n')
                    elif int(pid_str) in active_pids:
                        new_lines.append(f'{vm_path}@{region}|{pid_str}\n')
                    else:
                        new_lines.append(f'{vm_path}@{region}|free\n')

            except ec2_client.exceptions.ClientError as e:
                if 'InvalidInstanceID.NotFound' in str(e):
                    logger.info(f"VM not found, releasing instances in region {region}.")
                    continue

        # Writing updated lines back to the registry file
        with open(self.registry_path, 'w') as file:
            file.writelines(new_lines)

        # We won't check and clean on the files on aws and delete the unregistered ones
        # Since this can lead to unexpected delete on other server
        # PLease do monitor the instances to avoid additional cost

    def list_free_vms(self, region=DEFAULT_REGION, lock_needed=True):
        if lock_needed:
            with self.lock:
                return self._list_free_vms(region)
        else:
            return self._list_free_vms(region)

    def _list_free_vms(self, region=DEFAULT_REGION):
        free_vms = []
        with open(self.registry_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                vm_path_at_vm_region, pid_str = line.strip().split('|')
                vm_path, vm_region = vm_path_at_vm_region.split("@")
                if pid_str == "free" and vm_region == region:
                    free_vms.append((vm_path, pid_str))

        return free_vms

    def get_vm_path(self, region=DEFAULT_REGION):
        with self.lock:
            if not AWSVMManager.checked_and_cleaned:
                AWSVMManager.checked_and_cleaned = True
                self._check_and_clean()

        allocation_needed = False
        with self.lock:
            free_vms_paths = self._list_free_vms(region)

            if len(free_vms_paths) == 0:
                # No free virtual machine available, generate a new one
                allocation_needed = True
            else:
                # Choose the first free virtual machine
                chosen_vm_path = free_vms_paths[0][0]
                self._occupy_vm(chosen_vm_path, os.getpid(), region)
                return chosen_vm_path
        
        if allocation_needed:
            logger.info("No free virtual machine available. Generating a new one, which would take a while...☕")
            new_vm_path = _allocate_vm(region)
            with self.lock:
                self._add_vm(new_vm_path, region)
                self._occupy_vm(new_vm_path, os.getpid(), region)
            return new_vm_path
