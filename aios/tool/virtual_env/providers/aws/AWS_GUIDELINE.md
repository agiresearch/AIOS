# ☁ Configuration of AWS

---

Welcome to the AWS VM Management documentation. Before you proceed with using the code to manage AWS services, please ensure the following variables are set correctly according to your AWS environment.

## Configuration Variables
You need to assign values to several variables crucial for the operation of these scripts on AWS:

- **`REGISTRY_PATH`**: Sets the file path for VM registration logging.
  - Example: `'.aws_vms'`
- **`DEFAULT_REGION`**: Default AWS region where your instances will be launched.
  - Example: `"us-east-1"`
- **`IMAGE_ID_MAP`**: Dictionary mapping regions to specific AMI IDs that should be used for instance creation. Here we already set the AMI id to the official OSWorld image of Ubuntu supported by us.
  - Formatted as follows:
    ```python
    IMAGE_ID_MAP = {
        "us-east-1": "ami-019f92c05df45031b",
        "ap-east-1": "ami-07b4956131da1b282"
        # Add other regions and corresponding AMIs
    }
    ```
- **`INSTANCE_TYPE`**: Specifies the type of EC2 instance to be launched.
  - Example: `"t3.medium"`
- **`KEY_NAME`**: Specifies the name of the key pair to be used for the instances.
  - Example: `"osworld_key"`
- **`NETWORK_INTERFACES`**: Configuration settings for network interfaces, which include subnet IDs, security group IDs, and public IP addressing.
  - Example:
    ```python
    NETWORK_INTERFACES = {
        "us-east-1": [
            {
                "SubnetId": "subnet-037edfff66c2eb894",
                "AssociatePublicIpAddress": True,
                "DeviceIndex": 0,
                "Groups": ["sg-0342574803206ee9c"]
            }
        ],
        # Add configurations for other regions
    }
    ```


### AWS CLI Configuration
Before using these scripts, you must configure your AWS CLI with your credentials. This can be done via the following commands:

```bash
aws configure
```
This command will prompt you for:
- AWS Access Key ID
- AWS Secret Access Key
- Default region name (Optional, you can press enter)

Enter your credentials as required. This setup will allow you to interact with AWS services using the credentials provided.

### Disclaimer
Use the provided scripts and configurations at your own risk. Ensure that you understand the AWS pricing model and potential costs associated with deploying instances, as using these scripts might result in charges on your AWS account.

> **Note:**  Ensure all AMI images used in `IMAGE_ID_MAP` are accessible and permissioned correctly for your AWS account, and that they are available in the specified region.
