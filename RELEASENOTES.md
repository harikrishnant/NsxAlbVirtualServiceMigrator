# NSX ALB Cloud Migrator 1.0 Release Notes
This release notes cover the following topics:
- Document Revision History
- Supported NSX ALB Versions
- What's New
- Known Limitations

**Document Revision History**

First Edition - March 03, 2022

**Supported NSX ALB Versions**

NSX ALB API Versions 18.1.2 till 21.1.2

**Whats's New**
- Ability to migrate Virtual services and dependencies (Pools, PoolGroups, HTTPPolicySets, VSVIPs) across NSX ALB Cloud Accounts:
     - Migration from vCenter Cloud Account to No-Orchestrator Cloud
     - Migration from No-Orchestrator Cloud to vCenter Cloud Account
     - Migration from one vCenter Cloud Account to another vCenter Cloud Account
     - Migration from vCenter Cloud Account to NSX-T VLAN Cloud Account
     - Migration from NSX-T VLAN Cloud Account to vCenter Cloud Account
     - Migration from No-orchestrator Cloud to NSX-T VLAN Cloud Account
     - Migration from NSX-T VLAN Cloud Account to No-orchestrator Cloud
     - Migration from vCenter Cloud Account to NSX-T Overlay Cloud
     - Migration from No-Orchestrator Cloud to NSX-T Overlay Cloud
     - Migration from NSX-T VLAN Cloud Account to NSX-T Overlay Cloud
 - Ability to migrate Virtual services and dependencies (Pools, PoolGroups, HTTPPolicySets, VSVIPs) across VRF Contexts (Routing domains):
      - Migration from one VRF Context to another in vCenter Cloud accounts
      - Migration from one VRF Context to another in No-Orchestrator Cloud accounts
      - Migration from one VRF Context to another in NSX-T VLAN Cloud accounts
      - Migration from one VRF Context (T1 Gateway) to another in NSX-T Overlay Cloud accounts
      - Migration to VRF Contexts within the same or across cloud accounts - vCenter, No-Orchestrator, NSX-T VLAN and Overlay cloud accounts
 - Ability to migrate Virtual services across Service Engine Groups:
      - Migration from one Service Engine Group to another in vCenter Cloud accounts
      - Migration from one Service Engine Group to another in No-Orchestrator Cloud accounts
      - Migration from one Service Engine Group to another in NSX-T VLAN Cloud accounts
      - Migration from one Service Engine Group to another in NSX-T Overlay Cloud accounts

**Known Limitations**

The below NSX ALB features are not yet tested with NSX ALB Cloud Migrator and hence migration of below features may or may not work as expected.
- Virtual Services with VIP sharing
- TLS SNI based Virtual Service Hosting (Parent - Child VS)
- GSLB DNS Virtual Services
- Any datascripts with mention of pools / pool groups need to be manually updated post migration
- GSLB Applications are not updated with migrated virtual services information
- IPAM / DNS profiles
- For NSX-T VLAN backed clouds, the placement networks for each virtual service need to be manually added. This is a NSX ALB Cloud limitation
- Migration from NSX-T Overlay Cloud to vCenter Cloud succeeds but requires additional manual intervention for VIP connectivity.
- Wrong inputs to the tool will abort the execution and requires manual cleanup
- Lack of enhanced logging

![VxPlanet.com](https://serveritpro.files.wordpress.com/2021/09/vxplanet_correct.png)
