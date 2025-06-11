from virtual_env.providers.base import VMManager, Provider


def create_vm_manager_and_provider(provider_name: str, region: str):
    """
    Factory function to get the Virtual Machine Manager and Provider instances based on the provided provider name.
    """
    provider_name = provider_name.lower().strip()
    if provider_name == "vmware":
        from virtual_env.providers.vmware.manager import VMwareVMManager
        from virtual_env.providers.vmware.provider import VMwareProvider
        return VMwareVMManager(), VMwareProvider(region)
    elif provider_name == "virtualbox":
        from virtual_env.providers.virtualbox.manager import VirtualBoxVMManager
        from virtual_env.providers.virtualbox.provider import VirtualBoxProvider
        return VirtualBoxVMManager(), VirtualBoxProvider(region)
    elif provider_name in ["aws", "amazon web services"]:
        from virtual_env.providers.aws.manager import AWSVMManager
        from virtual_env.providers.aws.provider import AWSProvider
        return AWSVMManager(), AWSProvider(region)
    elif provider_name == "azure":
        from virtual_env.providers.azure.manager import AzureVMManager
        from virtual_env.providers.azure.provider import AzureProvider
        return AzureVMManager(), AzureProvider(region)
    elif provider_name == "docker":
        from virtual_env.providers.docker.manager import DockerVMManager
        from virtual_env.providers.docker.provider import DockerProvider
        return DockerVMManager(), DockerProvider(region)
    else:
        raise NotImplementedError(f"{provider_name} not implemented!")
