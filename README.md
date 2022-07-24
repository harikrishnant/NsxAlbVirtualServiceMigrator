# NSX ALB Cloud Migrator
NSX ALB Cloud Migrator will migrate Virtual Services (and it's dependencies - pools, poolgroups, HTTPPolicySets and VSVIPs) across NSX ALB Cloud Accounts, VRFs, Service Engine Groups and NSX-T T1 gateways. Currently the below NSX ALB cloud accounts are supported:
- vCenter Cloud
- NSX-T VLAN cloud
- NSX-T Overlay cloud
- No-Orchestrator cloud

This NSX ALB Cloud Migrator is currently in version 1.1 and the capabilities & limitations are available in the release notes.
# Overview
This NSX ALB Cloud Migrator supports the below migration scenarios for Virtual Services and dependencies within the same NSX ALB Tenant:

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

**Note:** This NSX ALB Cloud Migrator supports only migration within the same NSX ALB Tenant. Cross Tenant migration is currently not supported.

# Instructions
1. Make sure that the target cloud account to which the Virtual Services need to be migrated is configured. This includes the cloud connector configuration, VRF Contexts, networks & routing configuration and service engine confguration under the Service Engine Group.
2. The necessary routes (default routes / static routes to the pool members) need to be avaialble on the target VRF context before migrating the VS / Pools.
3. Make sure that the target cloud account / VRF context doesn't have a conflicting VSVIP object (VIP) compared to the objects being migrated from the source cloud account   
4. A linux VM with connectivity to NSX ALB controllers
5.  Install Python3 on the linux VM. On CentOS or RHEL systems, run -> *yum install -y python3*
6.  Install git -> *yum install -y git*
7.  Install the below python modules:
     - requests -> *python3 -m pip install requests*
     - urllib3 -> *python3 -m pip install urllib3* 
     - tabulate -> *python3 -m pip install tabulate*
     - pandas -> *python3 -m pip install pandas*
8. Clone the repository and navigate to NsxAlbCloudMigrator/V1.1/ -> *git clone https://github.com/harikrishnant/NsxAlbCloudMigrator.git && cd NsxAlbCloudMigrator/V1.1/*
9. The migration workflow will create a tracking directory (NsxAlbCloudMigrator/V1.1/Tracker/) which has the tracking information for each job. DO NOT DELETE this directory, as this is required for cleanup and remove_prefix jobs.
10. Logs for each job is save in NsxAlbCloudMigrator/V1.1/logs/

**Migration mode**

9. Run ./main.py with the "migrate" subcommand. -> *./main.py migrate --help* 

This will launch NSX ALB Cloud Migrator help menu for the migrate mode. Follow instructions on the screen.

Eg: *./main.py migrate -i <NSX_ALB_Controller_IP/FQDN> -a <API_Version> -u <NSX_ALB_USER> -t <NSX_ALB_TENANT> -c <Target_Cloud_Account> -r <Target_VRF_Context> -s <Target_SEG> -P <Prefix/Run-ID>*
 
**Remove prefix mode**

10. Run ./main.py with the "remove_prefix" subcommand. -> *./main.py remove_prefix --help* 
 
This will launch NSX ALB Cloud Migrator help menu for the remove_prefix mode. Follow instructions on the screen.

Eg: *./main.py remove_prefix -i <NSX_ALB_Controller_IP/FQDN> -u <NSX_ALB_USER> -p <NSX_ALB_PASSWORD> -r <Prefix/Run-ID>*

**Cleanup mode**

10. Run ./main.py with the "cleanup" subcommand. -> *./main.py cleanup --help* 
 
This will launch NSX ALB Cloud Migrator help menu for the cleanup mode. Follow instructions on the screen.

Eg: *./main.py cleanup -i <NSX_ALB_Controller_IP/FQDN> -u <NSX_ALB_USER> -p <NSX_ALB_PASSWORD> -r <Prefix/Run-ID>*

# Migration Workflow

![VxPlanet.com](https://serveritpro.files.wordpress.com/2022/03/flowchart.jpg)

# Contact
Please contact me at https://vxplanet.com for improvising the code, feature enhancements and bugs. Alternatively you can also use Issue Tracker to report any bugs or questions regarding the NSX ALB Cloud Migrator tool. 

![VxPlanet.com](https://serveritpro.files.wordpress.com/2021/09/vxplanet_correct.png)
