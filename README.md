# NSX ALB Virtual Service Migrator v1.2
NSX ALB Virtual Service Migrator will migrate Virtual Services (and it's dependencies - pools, poolgroups, HTTPPolicySets and VSVIPs) across NSX ALB Cloud Accounts, VRF Contexts, Service Engine Groups and NSX-T T1 gateways. Currently the below NSX ALB cloud accounts are supported:
- vCenter Cloud
- NSX-T VLAN cloud
- NSX-T Overlay cloud
- No-Orchestrator cloud

This NSX ALB Virtual Service Migrator is currently in version 1.2 and the capabilities & limitations are available in the release notes.
# Overview
This NSX ALB Virtual Service Migrator supports the below migration scenarios for Virtual Services and dependencies within the same NSX ALB Tenant:

**Migration across Cloud Accounts**
1. Migration from vCenter Cloud Account to No-Orchestrator Cloud
2. Migration from No-Orchestrator Cloud to vCenter Cloud Account
3. Migration from one vCenter Cloud Account to another vCenter Cloud Account
4. Migration from vCenter Cloud Account to NSX-T VLAN Cloud Account
5. Migration from NSX-T VLAN Cloud Account to vCenter Cloud Account
6. Migration from No-orchestrator Cloud to NSX-T VLAN Cloud Account
7. Migration from NSX-T VLAN Cloud Account to No-orchestrator Cloud
8. Migration from vCenter Cloud Account to NSX-T Overlay Cloud
9. Migration from No-Orchestrator Cloud to NSX-T Overlay Cloud
10. Migration from NSX-T VLAN Cloud Account to NSX-T Overlay Cloud

**Migration across VRF Contexts (Routing Domains)**
1. Migration from one VRF Context to another in vCenter Cloud accounts
2. Migration from one VRF Context to another in No-Orchestrator Cloud accounts
3. Migration from one VRF Context to another in NSX-T VLAN Cloud accounts
4. Migration from one VRF Context (T1 Gateway) to another in NSX-T Overlay Cloud accounts
5. Migration to VRF Contexts within the same or across cloud accounts - vCenter, No-Orchestrator, NSX-T VLAN and Overlay cloud accounts

**Migration across Service Engine Groups**
1. Migration from one Service Engine Group to another in vCenter Cloud accounts
2. Migration from one Service Engine Group to another in No-Orchestrator Cloud accounts
3. Migration from one Service Engine Group to another in NSX-T VLAN Cloud accounts
4. Migration from one Service Engine Group to another in NSX-T Overlay Cloud accounts

**Note:** This NSX ALB Virtual Service Migrator supports only migration within the same NSX ALB Tenant. Cross Tenant migration is currently not supported.

# Instructions
1. Make sure that the target cloud account to which the Virtual Services need to be migrated is configured. This includes the cloud connector configuration, VRF Contexts, networks & routing configuration and service engine confguration under the Service Engine Group.
2. The necessary routes (default routes / static routes to the pool members) need to be avaialble on the target VRF context before migrating the VS / Pools.
3. Make sure that the target cloud account / VRF context doesn't have a conflicting VSVIP object (VIP) compared to the objects being migrated from the source cloud account. If it has, perform migration with IPAM profiles attached.   
4. A linux VM with connectivity to NSX ALB controllers is required to perform the migration.
5.  Install Python3 on the linux VM. On CentOS or RHEL systems, run -> *yum install -y python3*
6.  Install git -> *yum install -y git*
7.  Install the below python modules:
     - requests -> *python3 -m pip install requests*
     - urllib3 -> *python3 -m pip install urllib3* 
     - tabulate -> *python3 -m pip install tabulate*
     - pandas -> *python3 -m pip install pandas*
8. Clone the repository and navigate to NsxAlbCloudMigrator/V1.2/ -> *git clone https://github.com/harikrishnant/NsxAlbVirtualServiceMigrator.git && cd NsxAlbVirtualServiceMigrator/V1.2/*
9. The migration tool has three modes:
    - Migrate mode -> This mode will perform migration of virtual services to same or different NSX ALB Cloud account.
    - Remove Prefix mode -> This mode will perform automated removal of prefixes appended to the migrated objects. This needs to be done post cutover of virtual services.
    - Cleanup mode -> This mode will perform cleanup of migrated objects incase the tool encounters an error or if post migration validation fails. This needs to be done before the Remove Prefix mode.
11. The migration workflow will create a tracking directory (NsxAlbCloudMigrator/V1.2/Tracker/) which has the tracking information for each job. DO NOT DELETE this directory, as this is required for cleanup and remove_prefix jobs.
12. Logs for each job is save in NsxAlbCloudMigrator/V1.2/logs/

**Migration mode**

9. Run ./main.py with the "migrate" subcommand. -> *python3 main.py migrate --help* 

This will launch NSX ALB Virtual Service Migrator help menu for the migrate mode. Follow instructions on the screen.

Eg: python3 main.py migrate -i <CONTROLLER_IP/FQDN> -u <USERNAME> -p <PASSWORD> -a <API_VERSION> -t <NSX_ALB_TENANT> -c <TARGET_CLOUD> -r <TARGET_VRF_CONTEXT> -s <TARGET_SERVICE_ENGINE_GROUP> -d <TARGET_APPLICATION_DNS_DOMAINS> -n <TARGET_IPAM_NETWORK_NAME> -S <TARGET_IPAM_SUBNET> -P <OBJECT_PREFIX/RUN-ID>*

where
CONTROLLER_IP/FQDN -> This is the NSX ALB Controller cluster IP/FQDN
USERNAME -> This is the local "system-admin" user account to login to the NSX ALB Controller cluster. SAML authentication is currently not supported.
PASSWORD -> This is the password of the above user account to login to the NSX ALB Controller cluster.
API_VERSION -> This is the API version of the controller cluster. This is also the controller version (Eg:22.1.4)
NSX_ALB_TENANT -> This is the NSX ALB Tenant where the migration needs to be performed.
TARGET_CLOUD -> This is the target NSX ALB Cloud connector name
TARGET_VRF_CONTEXT -> This is the target VRF Context (under the target cloud connector)
TARGET_SERVICE_ENGINE_GROUP -> This is the target Service Engine Group (under the target cloud connector)0000000000
TARGET_APPLICATION_DNS_DOMAINS -> 
 
**Remove prefix mode**

10. Run ./main.py with the "remove_prefix" subcommand. -> *./main.py remove_prefix --help* 
 
This will launch NSX ALB Virtual Service Migrator help menu for the remove_prefix mode. Follow instructions on the screen.

Eg: *./main.py remove_prefix -i <NSX_ALB_Controller_IP/FQDN> -u <NSX_ALB_USER> -p <NSX_ALB_PASSWORD> -r <Prefix/Run-ID>*

**Cleanup mode**

10. Run ./main.py with the "cleanup" subcommand. -> *./main.py cleanup --help* 
 
This will launch NSX ALB Virtual Service Migrator help menu for the cleanup mode. Follow instructions on the screen.

Eg: *./main.py cleanup -i <NSX_ALB_Controller_IP/FQDN> -u <NSX_ALB_USER> -p <NSX_ALB_PASSWORD> -r <Prefix/Run-ID>*

# Migration Workflow

![VxPlanet.com](https://serveritpro.files.wordpress.com/2022/03/flowchart.jpg)

# Contact
Please contact me at https://vxplanet.com for improvising the code, feature enhancements and bugs. Alternatively you can also use Issue Tracker to report any bugs or questions regarding the NSX ALB Virtual Service Migrator tool. 

![VxPlanet.com](https://serveritpro.files.wordpress.com/2021/09/vxplanet_correct.png)
