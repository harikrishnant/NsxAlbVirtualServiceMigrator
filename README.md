# NSX ALB Cloud Migrator
NSX ALB Cloud Migrator will migrate Virtual Services (and it's dependencies - pools, poolgroups, HTTPPolicySets and VSVIPs) across NSX ALB Cloud Accounts, VRFs, Service Engine Groups and NSX-T T1 gateways. Currently the below NSX ALB cloud accounts are supported:
- vCenter Cloud
- NSX-T VLAN cloud
- NSX-T Overlay cloud
- No-Orchestrator cloud

This NSX ALB Cloud Migrator is currently in version 1.0 and the capabilities & limitations are available in the release notes.
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
1. Make sure that the target cloud account to which the Virtual Services need to be migrated is configured. This includes the connector configuration, VRF Contexts, networks & routing configuration and service engine confguration under the Service Engine Group.
2. The necessary routes (default routes / static routes to the pool members) need to b avaialble on the target VRF context before migrating the VS / Pools. 
3. A linux VM with connectivity to NSX ALB controllers
4.  Install Python3 on the linux VM. On CentOS or RHEL systems, run -> *yum install -y python3*
5.  Install git -> *yum install -y git*
6.  Install the below python modules:
     - requests -> *python3 -m pip install requests*
     - urllib3 -> *python3 -m pip install urllib3* 
     - tabulate -> *python3 -m pip install tabulate*
7. Clone the repository and navigate to NsxAlbCloudMigrator -> *git clone https://github.com/harikrishnant/NsxAlbCloudMigrator.git && cd NsxAlbCloudMigrator*
8. Set the bash script migrator.sh to execute -> *chmod +x migrator.sh*
9. Execute migrator.sh -> *./migrator.sh* This will launch NSX ALB Cloud Migrator. Follow instructions on the screen.

# Migration Workflow

![VxPlanet.com](https://serveritpro.files.wordpress.com/2022/03/flowchart.jpg)

# Contact
Please contact me at https://vxplanet.com for improvising the code, feature enhancements and bugs. Alternatively you can also use Issue Tracker to report any bugs or questions regarding the NSX ALB Cloud Migrator tool. 

![VxPlanet.com](https://serveritpro.files.wordpress.com/2021/09/vxplanet_correct.png)
