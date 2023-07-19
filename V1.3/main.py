#Import Modules
import urllib3
import sys
import titles
import argparse
import pandas
import json
import os
from art import logo, line
from datetime import datetime
from getpass import getpass
from tabulate import tabulate
from nsx_alb_login import NsxAlbLogin
from nsx_alb_tenants import NsxAlbTenant
from nsx_alb_clouds import NsxAlbCloud
from nsx_alb_dnsprofiles import NsxAlbDnsProfile
from nsx_alb_ipamprofiles import NsxAlbIpamProfile
from nsx_alb_vrfcontexts import NsxAlbVrfContext
from nsx_alb_segroups import NsxAlbSeGroup
from nsx_alb_pools import NsxAlbPool
from nsx_alb_poolgroups import NsxAlbPoolGroup
from nsx_alb_httppolicysets import NsxAlbHttpPolicySet
from nsx_alb_vsvips import NsxAlbVsVip
from nsx_alb_virtualservices import NsxAlbVirtualService
from nsx_alb_migration_tracker import NsxAlbMigrationTracker
from nsx_alb_cleanup import NsxAlbCleanup
from nsx_alb_logout import NsxAlbLogout

def main():
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    print(logo)

    #Block for Argparse and subcommands for migrate and cleanup
    parser = argparse.ArgumentParser(description="NSX ALB Virtual Service Migrator v1.2 Flags", epilog="Author : Harikrishnan T (@hari5611). Visit vxplanet.com for more information", add_help=True)
    parser.add_argument("-v", "--version", action="version", version="NSX ALB Virtual Service Migrator version 1.2")
    #parser.add_argument("-U", "--username", action="store", nargs="?", const="admin", type=str, metavar="USERNAME", dest="username", required=False, help="User with system admin privileges to NSX ALB. If not specified, local %(const)s user will be used.")
    subparsers = parser.add_subparsers(title='Valid Subcommands', help="Available Subcommands")
    parser_migrate = subparsers.add_parser("migrate", help='Migrate Virtual Services across Cloud accounts (migrate -h for help)')
    parser_cleanup = subparsers.add_parser("cleanup", help='Cleanup objects from a failed run using the run ID (cleanup -h for help)')
    parser_remove_prefix = subparsers.add_parser("remove_prefix", help='Remove the prefix from objects after a successful migration (remove_prefix -h for help)')    
    parser_migrate.add_argument("-u", "--username", action="store", type=str, metavar="USERNAME", dest="username", required=True, help="User with system admin privileges to NSX ALB")
    parser_migrate.add_argument("-p", "--password", action="store", type=str, metavar="PASSWORD", dest="password", required=False, help="User Password")
    parser_migrate.add_argument("-i", "--controller_ip", action="store", type=str, metavar="CONTROLLER_IP/FQDN", dest="controller_ip", required=True, help="NSX ALB Controller IP or FQDN")
    parser_migrate.add_argument("-t", "--tenant", action="store", type=str, metavar="NSX_ALB_Tenant", dest="nsx_alb_tenant", required=True, help="NSX ALB Tenant. Currently only intra-Tenant migration is supported by this tool")
    parser_migrate.add_argument("-a", "--api-version", action="store", type=str, metavar="API_VERSION", dest="api_version", required=True, help="NSX ALB API version to use for migration. Should be either same or below the controller API version")
    parser_migrate.add_argument("-c", "--target_cloud", action="store", type=str, metavar="TARGET_CLOUD", dest="target_cloud_name", required=True, help="NSX ALB target Cloud account for migration")
    parser_migrate.add_argument("-r", "--target_vrf", action="store", type=str, metavar="TARGET_VRF", dest="target_vrf_name", required=True, help="NSX ALB target VRF Context for migration")
    parser_migrate.add_argument("-s", "--target_seg", action="store", type=str, metavar="TARGET_SERVICE_ENGINE_GROUP", dest="target_seg_name", required=True, help="NSX ALB target Service Engine Group for migration")
    parser_migrate.add_argument("-d", "--target_dns_domain", action="store", type=str, metavar="TARGET_APPLICATION_DNS_DOMAINS", dest="target_dns_domain", required=False, help="NSX ALB target DNS Application Domains")    
    parser_migrate.add_argument("-n", "--target_ipam_network", action="store", type=str, metavar="TARGET_IPAM_NETWORK_NAME", dest="target_ipam_network", required=False, help="NSX ALB target IPAM Network name")
    parser_migrate.add_argument("-S", "--target_ipam_subnet", action="store", type=str, metavar="TARGET IPAM SUBNET", dest="target_ipam_subnet", required=False, help="NSX ALB target IPAM subnet (x.x.x.x/x)")    
    parser_migrate.add_argument("-P", "--prefix", action="store", type=str, metavar="OBJECT_PREFIX", dest="prefix", required=True, help="Prefix for objets migrated by NSX ALB")
    parser_migrate.add_argument("-q", "--virtual_hosted_vs", action="store", type=str, choices=["sni_evh", ], metavar="MIGRATE_PARENT_CHILD_VS", dest="virtual_hosted_vs", required=False, help="Migrate Parent-Child Virtual Services. Supported value is 'sni_evh'")
    parser_migrate.set_defaults(which="migrate")
    parser_cleanup.add_argument("-i", "--controller_ip", action="store", type=str, metavar="CONTROLLER_IP/FQDN", dest="controller_ip", required=True, help="NSX ALB Controller IP or FQDN")
    parser_cleanup.add_argument("-u", "--username", action="store", type=str, metavar="USERNAME", dest="username", required=True, help="User with system admin privileges to NSX ALB")
    parser_cleanup.add_argument("-p", "--password", action="store", type=str, metavar="PASSWORD", dest="password", required=False, help="User Password")
    parser_cleanup.add_argument("-r", "--run_id", action="store", type=str, metavar="RUN_ID", dest="prefix", required=True, help="Run ID (Prefix name) of the previous run")
    parser_cleanup.set_defaults(which="cleanup")
    parser_remove_prefix.add_argument("-i", "--controller_ip", action="store", type=str, metavar="CONTROLLER_IP/FQDN", dest="controller_ip", required=True, help="NSX ALB Controller IP or FQDN")
    parser_remove_prefix.add_argument("-u", "--username", action="store", type=str, metavar="USERNAME", dest="username", required=True, help="User with system admin privileges to NSX ALB")
    parser_remove_prefix.add_argument("-p", "--password", action="store", type=str, metavar="PASSWORD", dest="password", required=False, help="User Password")
    parser_remove_prefix.add_argument("-r", "--run_id", action="store", type=str, metavar="RUN_ID", dest="prefix", required=True, help="Run ID (Prefix name) of the run")
    parser_remove_prefix.add_argument("-q", "--virtual_hosted_vs", action="store", type=str, choices=["sni_evh", ], metavar="REMOVE_PREFIX_FOR_PARENT_CHILD_VS", dest="virtual_hosted_vs", required=False, help="Remove Prefix for Parent-Child Virtual Services. Supported value is 'sni_evh'")
    parser_remove_prefix.set_defaults(which="remove_prefix")
    args = parser.parse_args() #Creates a Namespace Object. The parameters are attributes of this object

    #print(args.which)
    #print(args.target_dns_domain.split(","))
    # print(sys.argv)
    #print(vars(args)) # will convert object to a dictionary
    #print(args.__dict__)
    #if not hasattr(args, "controller_ip"):

    # Checking if subcommands are called with the main script
    if not hasattr(args, "which"):
        print(tabulate([["No Operation requested", "Select from one of the subcommands below:"]], headers=["Error", "Description"], showindex=True, tablefmt="fancy_grid"))
        parser.parse_args(["-h"])

    # #Checking dependency parameters for IPAM
    # if (getattr(args, "target_ipam_network") is not None and getattr(args,"target_ipam_subnet") is None) or (getattr(args,"target_ipam_network") is None and getattr(args,"target_ipam_subnet") is not None):
    #     print(tabulate([["IPAM Parameter dependency error", "Both -n and -S flags are required for IPAM"]], headers=["Error", "Description"], showindex=True, tablefmt="fancy_grid"))
    #     parser.parse_args(["migrate", "-h", "migrate -h"])

    #Custom Print function   
    def print_func(item):
        print(item)                
        with open(f"./logs/run-{args.prefix}.log", "a", encoding="utf-8") as outfile:
            print(item, file=outfile)

    URL = "https://" + args.controller_ip
    
    # Block for setting API Request headers for migrate, cleanup and remove_prefix subcommands
    if args.which == "cleanup":        
        print(f"\nEntering CLEANUP Mode [RUN ID : {args.prefix}]\n")
        if os.path.exists("./Tracker"):
            if ("infra_track" + "-" + args.prefix + ".json" in os.listdir("./Tracker")) and ("obj_track" + "-" + args.prefix + ".csv" in os.listdir("./Tracker")):
                with open("./Tracker/infra_track" + "-" + args.prefix + ".json") as infra_track:
                    dict_infra_track = json.load(infra_track)
                    headers = {
                                "Content-Type": "application/json",
                                "Referer": URL,
                                "Accept-Encoding": "application/json",
                                "X-Avi-Tenant": dict_infra_track["nsx_alb_tenant"],
                                "X-Avi-Version": dict_infra_track["api_version"]
                            }
            else:
                print(tabulate([["Tracking information for Run ID not found", "Please enter a valid Run ID"]], headers=["Error", "Description"], showindex=True, tablefmt="fancy_grid"))
                sys.exit() 
        else:
                print(tabulate([["Tracking directory not found", "Please ensure tracking dir with the Run ID information is available"]], headers=["Error", "Description"], showindex=True, tablefmt="fancy_grid"))  
                sys.exit() 
    
    if args.which == "remove_prefix":        
        print(f"\nEntering Remove_Prefix Mode [RUN ID : {args.prefix}]\n")
        if os.path.exists("./Tracker"):
            if ("infra_track" + "-" + args.prefix + ".json" in os.listdir("./Tracker")) and ("obj_track" + "-" + args.prefix + ".csv" in os.listdir("./Tracker")):
                with open("./Tracker/infra_track" + "-" + args.prefix + ".json") as infra_track:
                    dict_infra_track = json.load(infra_track)
                    headers = {
                                "Content-Type": "application/json",
                                "Referer": URL,
                                "Accept-Encoding": "application/json",
                                "X-Avi-Tenant": dict_infra_track["nsx_alb_tenant"],
                                "X-Avi-Version": dict_infra_track["api_version"]
                            }
            else:
                print(tabulate([["Tracking information for Run ID not found", "Please enter a valid Run ID"]], headers=["Error", "Description"], showindex=True, tablefmt="fancy_grid"))
                sys.exit() 
        else:
                print(tabulate([["Tracking directory not found", "Please ensure tracking dir with the Run ID information is available"]], headers=["Error", "Description"], showindex=True, tablefmt="fancy_grid"))  
                sys.exit()

    if args.which == "migrate":
        #Checking dependency parameters for IPAM
        if (getattr(args, "target_ipam_network") is not None and getattr(args,"target_ipam_subnet") is None) or (getattr(args,"target_ipam_network") is None and getattr(args,"target_ipam_subnet") is not None):
            print(tabulate([["IPAM Parameter dependency error", "Both -n and -S flags are required for IPAM"]], headers=["Error", "Description"], showindex=True, tablefmt="fancy_grid"))
            parser.parse_args(["migrate", "-h", "migrate -h"])
        headers = {
                    "Content-Type": "application/json",
                    "Referer": URL,
                    "Accept-Encoding": "application/json",
                    "X-Avi-Tenant": args.nsx_alb_tenant,
                    "X-Avi-Version": args.api_version
                }
        #Create run log directory if action=migrate
        if not os.path.exists("./logs"):
            os.makedirs("./logs")
        if ("run-" + args.prefix + ".log" in os.listdir("./logs")):
            overwrite_prompt = input(f"\nWARNING : Logs with the same Run ID {[args.prefix]} exists. Overwrite? Y/N ").lower()
            if overwrite_prompt == "n" or overwrite_prompt == "no":
                print(f"\nAborting..... Cleanup the previous Run [{args.prefix}] and Re-run the migrator with a different prefix (Run ID)\n")
                sys.exit()
            elif overwrite_prompt == "y" or overwrite_prompt == "yes":
                pass
            else:
                print("\nInvalid entry.....Aborting")
                sys.exit()
        with open(f"./logs/run-{args.prefix}.log", "w", encoding="utf-8") as outfile:
                print(logo, file=outfile)
                print(f"\nRun ID = {args.prefix}", file=outfile)
                print(f"\nNSX ALB Controller = {args.controller_ip}", file=outfile)
                print(f"\nJob run by = {args.username}", file=outfile)              
                print(f"\nTenant = {args.nsx_alb_tenant}", file=outfile)
                print(f"\nTimestamp = {datetime.now()}", file=outfile)

    LOGIN = {
                 "username": args.username, 
                 "password": args.password if args.password else getpass(prompt="Enter Password: "), 
             }

    #Login, fetch CSRFToken and set Header Cookie
    print_func(titles.login)
    login = NsxAlbLogin(URL, LOGIN, headers, args.prefix)
    login.get_cookie()
    headers["X-CSRFToken"] = login.csrf_token
    headers["Cookie"] = login.cookie

    #Verify Tenant exists and login to tenant is successful
    tenant = NsxAlbTenant(URL, headers, args.prefix)
    tenant.get_tenant()

    #If cleanup mode is selected, call the cleanup class after successful authentication.
    if args.which == "cleanup":
        prompt1 = input(f"\nWARNING : This action will cleanup all objects created for Run ID [{args.prefix}]. Continue? Y/N ").lower()
        if prompt1 == "y" or prompt1 == "yes":
            if "obj_prefix_removal_status_" + args.prefix + ".csv" in os.listdir("./Tracker"):
                prompt2 = input(f"\nWARNING : Looks like you have already run prefix_removal for Run ID [{args.prefix}].\nIt's possible that objects might have been cut over to target cloud already. Continue? Y/N ").lower()
                if prompt2 == "n" or prompt2 == "no":
                    print(f"\nAborting Cleanup for Run [{args.prefix}] .....\n")
                    sys.exit()
                elif prompt2 == "y" or prompt2 == "yes":
                    pass
                else:
                    print("Invalid entry, Aborting ......")
                    sys.exit()
            cleanup = NsxAlbCleanup(headers, "./Tracker", args.prefix)
            cleanup.initiate_cleanup()
            if cleanup.dict_obj_not_deleted:
                print(tabulate([["All or few objects were not cleaned up successfully", f"Review the cleanup logs at {'./Tracker/obj_cleanup_status_' + args.prefix + '.csv'}"]], headers=["Cleanup Status", "Description"], showindex=True, tablefmt="fancy_grid"))
            else:
                print(tabulate([[f"Cleanup of Run ID {args.prefix} is successful", f"Review the logs at {'./Tracker/obj_cleanup_status_' + args.prefix + '.csv'}"]], headers=["Cleanup Status", "Description"], showindex=True, tablefmt="fancy_grid"))
            print(titles.thanks)
            sys.exit()
        elif prompt1 == "n" or prompt1 == "no":
                print(f"\nAborting Cleanup for Run [{args.prefix}] .....\n")
                sys.exit()
        else:
                print("Invalid entry, Aborting ......")
                sys.exit()
    #If remove_prefix mode is selected, call the relevant classes after successful authentication.
    if args.which == "remove_prefix":
        dict_df_obj_remove_prefix_status = {
                "obj_type" : [],
                "obj_name_old" : [],
                "obj_name_new" : [],
                "PREFIX_REMOVAL_STATUS" : [],
                "Error" : []
            }  
        df_obj_remove_prefix_status = pandas.DataFrame(dict_df_obj_remove_prefix_status)
        df_obj_remove_prefix_status.to_csv("./Tracker" + "/obj_prefix_removal_status_" + args.prefix + ".csv", index=False)
        rm_prefix_pool = NsxAlbPool(URL, headers, args.prefix)
        rm_prefix_pool.remove_pool_prefix("./Tracker", headers)
        rm_prefix_poolgroup = NsxAlbPoolGroup(URL, headers, args.prefix)
        rm_prefix_poolgroup.remove_poolgroup_prefix("./Tracker", headers)
        rm_prefix_httppolicyset = NsxAlbHttpPolicySet(URL, headers, args.prefix)
        rm_prefix_httppolicyset.remove_httppolicyset_prefix("./Tracker", headers)
        rm_prefix_vip = NsxAlbVsVip(URL, headers, args.prefix)
        rm_prefix_vip.remove_vsvip_prefix("./Tracker", headers)
        rm_prefix_virtualservice = NsxAlbVirtualService(URL, headers, run_id=args.prefix, migrate_parent_child_vs=args.virtual_hosted_vs)
        rm_prefix_virtualservice.remove_virtualservice_prefix("./Tracker", headers) 
        print(f"\nRemove Prefix for Run ID '{args.prefix}' has been completed.", f"Review the logs at {'./Tracker' + '/obj_prefix_removal_status_' + args.prefix + '.csv'} and manually rename any failed items")       
        print(titles.thanks)
        sys.exit() 

    #Scan for DNS Provider Profiles
    dnsproviderprofile = NsxAlbDnsProfile(URL, headers, args.prefix)
    dnsproviderprofile.get_dnsprofile()

    #Scan for IPAM Provider Profiles
    ipamproviderprofile = NsxAlbIpamProfile(URL, headers, args.prefix)
    ipamproviderprofile.get_network()
    ipamproviderprofile.get_ipamprofile()

    #List all NSX ALB cloud accounts and select the target cloud for migration
    print_func(titles.cloud)
    cloud = NsxAlbCloud(URL, headers, args.prefix)
    cloud.set_cloud(args.target_cloud_name, dnsproviderprofile.dict_dnsprofile_url_name, ipamproviderprofile.dict_ipamprofile_url_name)

    #List all VRFs under the selected NSX ALB cloud account and select the target VRF for migration
    print_func(titles.vrfcontext)
    vrfcontext = NsxAlbVrfContext(URL, headers, cloud.target_cloud_url, cloud.target_cloud_name, args.prefix)
    vrfcontext.set_vrfcontext(args.target_vrf_name)

    #Scan and validate supplied DNS domain list:
    if getattr(args, "target_dns_domain") is not None:
        print_func(titles.dnsprofile)
        dnsproviderprofile.scan_dnsprofile(cloud.target_cloud_dnsprofile_url, getattr(args, "target_dns_domain", "").split(","))

    #Scan and validate supplied IPAM networks:
    if getattr(args, "target_ipam_network") is not None and getattr(args, "target_ipam_subnet") is not None:
        print_func(titles.ipamprofile)
        ipamproviderprofile.scan_ipamprofile(cloud.target_cloud_ipamprofile_url, getattr(args, "target_ipam_network"), getattr(args, "target_ipam_subnet"), vrfcontext.list_vrfcontexts, args.target_vrf_name)
    
    #List all Service Engine Groups (SEG) under the selected NSX ALB cloud account and select the target SEG for migration
    print_func(titles.serviceenginegroup)
    segroup = NsxAlbSeGroup(URL, headers, cloud.target_cloud_url, cloud.target_cloud_name, args.prefix)
    segroup.set_segroup(args.target_seg_name)

    #Initialize migraton tracker object
    migration_tracker = NsxAlbMigrationTracker(URL, args.username, args.nsx_alb_tenant, args.api_version, args.prefix, "./Tracker")
    migration_tracker.set_tracking()

    #Fetch pool information from the NSX ALB Tenant
    pool = NsxAlbPool(URL, headers, args.prefix)
    pool.get_pool()

    #Fetch Pool Group information for virtual services from the NSX ALB Tenant
    poolgroup = NsxAlbPoolGroup(URL, headers, args.prefix)
    poolgroup.get_poolgroup()

    #Fetch VS VIP information for virtual services from the NSX ALB Tenant
    vsvip = NsxAlbVsVip(URL, headers, args.prefix)
    vsvip.get_vsvip()

    #List the Virtual Services under the Tenant and select the Virtual Services for migration
    print_func(titles.vs_selector)
    virtualservice = NsxAlbVirtualService(URL, headers, dict_cloud_url_name=cloud.dict_cloud_url_name, dict_pool_url_name=pool.dict_pool_url_name, dict_poolgroup_url_name=poolgroup.dict_poolgroup_url_name, dict_vsvip_url_name=vsvip.dict_vsvip_url_name, run_id=args.prefix, migrate_parent_child_vs=args.virtual_hosted_vs)
    virtualservice.set_virtualservice()

    #Scan for HTTPPolicySets in the Tenant
    httppolicyset = NsxAlbHttpPolicySet(URL, headers, args.prefix)
    httppolicyset.get_httppolicyset()

    #Scan selected Virtual Services for any HTTP Policy Sets and Content Switching Pools
    print_func(titles.httppolicyset_selector)
    virtualservice.get_virtualservice_policy(httppolicyset.dict_httppolicyset_url_name)
    print_func(titles.httppolicyset_scanner)
    httppolicyset.get_httppolicyset_pool(virtualservice.dict_vs_httppolicysetname, pool.dict_pool_url_name, poolgroup.dict_poolgroup_url_name)

    #Migrate Pools in Content Switching Policies to target NSX ALB Cloud Account
    pool_cs = NsxAlbPool(URL, headers, args.prefix) #Initialize a pool object to migrate pools in content switching policies
    if len(httppolicyset.dict_cs_originalpool_url_name) != 0: 
        print_func(titles.httppolicyset_migrate_pools)
        pool_cs.migrate_pool(httppolicyset.dict_cs_originalpool_url_name, cloud.target_cloud_url, vrfcontext.target_vrfcontext_url, vrfcontext.target_vrfcontext_tier1path, args.prefix, migration_tracker.tracker_csv)
    else:
        pool_cs.dict_originalpoolurl_migratedpoolurl = {}

    #Migrate Pool groups in Content Switching Policies to target NSX ALB Cloud Account    
    poolgroup_cs = NsxAlbPoolGroup(URL, headers, args.prefix)
    poolgroup_cs.get_poolgroup()
    if len(httppolicyset.dict_cs_originalpoolgroup_url_name) != 0:
        print_func(titles.httppolicyset_migratepoolgroups)       
        poolgroup_cs.get_poolgroup_member(httppolicyset.dict_cs_originalpoolgroup_url_name, pool.dict_pool_url_name)
        pool_pg_cs = NsxAlbPool(URL, headers, args.prefix) #Initialize a pool object to migrate pools in Pool Groups assocaited with Content Switching Policies
        if len(poolgroup_cs.dict_poolgroupmembers_url_name) != 0:            
            pool_pg_cs.migrate_pool(poolgroup_cs.dict_poolgroupmembers_url_name, cloud.target_cloud_url, vrfcontext.target_vrfcontext_url, vrfcontext.target_vrfcontext_tier1path, args.prefix, migration_tracker.tracker_csv)
        else:
            pool_pg_cs.dict_originalpoolurl_migratedpoolurl = {}
        poolgroup_cs.migrate_poolgroup(httppolicyset.dict_cs_originalpoolgroup_url_name, pool_pg_cs.dict_originalpoolurl_migratedpoolurl, cloud.target_cloud_url, args.prefix, migration_tracker.tracker_csv)   
    else:
        poolgroup_cs.dict_originalpoolgroupurl_migratedpoolgroupurl = {}
    
    #Migrate HTTP Policy Sets to target NSX ALB Cloud Account
    if len(httppolicyset.dict_cs_originalpool_url_name) != 0 or len(httppolicyset.dict_cs_originalpoolgroup_url_name) != 0: 
        print_func(titles.httppolicyset_migrate)
        httppolicyset.migrate_httppolicyset(pool_cs.dict_originalpoolurl_migratedpoolurl, poolgroup_cs.dict_originalpoolgroupurl_migratedpoolgroupurl, args.prefix, migration_tracker.tracker_csv)
    else:
        httppolicyset.dict_vs_httppolicysetmigratedurl = {}

    #Migrate Pool Groups directly associated with Virtual Services to target NSX ALB Cloud
    poolgroup_vs = NsxAlbPoolGroup(URL, headers, args.prefix)
    poolgroup_vs.get_poolgroup()
    poolgroup_vs.set_poolgroup(virtualservice.dict_selectedvs_originalpoolgroupname)
    if len(poolgroup_vs.dict_selectedpoolgroup_url_name) != 0:
        print_func(titles.vs_migratepoolgroups)
        poolgroup_vs.get_poolgroup_member(poolgroup_vs.dict_selectedpoolgroup_url_name, pool.dict_pool_url_name)
        pool_pg_vs = NsxAlbPool(URL, headers, args.prefix) #Initialize a pool object to migrate pools in Pool Groups assocaited with Virtual services
        if len(poolgroup_vs.dict_poolgroupmembers_url_name) != 0:
            pool_pg_vs.migrate_pool(poolgroup_vs.dict_poolgroupmembers_url_name, cloud.target_cloud_url, vrfcontext.target_vrfcontext_url, vrfcontext.target_vrfcontext_tier1path, args.prefix, migration_tracker.tracker_csv)
        else:
            pool_pg_vs.dict_originalpoolurl_migratedpoolurl = {}
        poolgroup_vs.migrate_poolgroup(poolgroup_vs.dict_selectedpoolgroup_url_name, pool_pg_vs.dict_originalpoolurl_migratedpoolurl, cloud.target_cloud_url, args.prefix, migration_tracker.tracker_csv)
    else:
        poolgroup_vs.dict_originalpoolgroupurl_migratedpoolgroupurl = {}     
   
    #Migrate Pools directly associated with Virtual Services to target NSX ALB Cloud
    pool_vs = NsxAlbPool(URL, headers, args.prefix) 
    pool_vs.set_pool(virtualservice.dict_selectedvs_originalpoolname)
    if len(pool_vs.dict_selectedpool_url_name) != 0:
        print_func(titles.vs_migratepools)
        pool_vs.migrate_pool(pool_vs.dict_selectedpool_url_name, cloud.target_cloud_url, vrfcontext.target_vrfcontext_url, vrfcontext.target_vrfcontext_tier1path, args.prefix, migration_tracker.tracker_csv)
    else:
        pool_vs.dict_originalpoolurl_migratedpoolurl = {}

    #Migrate VS VIPs of selected Virtual Services to target NSX ALB Cloud
    vsvip.set_vsvip(virtualservice.dict_selectedvs_originalvsvipname)
    if len(vsvip.dict_selectedvsvip_url_name) != 0:
        print_func(titles.vsvip_migrate)
        target_dns_domain = getattr(args, "target_dns_domain").split(",") if getattr(args, "target_dns_domain") is not None else []
        target_ipam_network = getattr(args, "target_ipam_network") if getattr(args, "target_ipam_network") is not None else ""
        target_ipam_subnet =  getattr(args, "target_ipam_subnet") if getattr(args, "target_ipam_subnet") is not None else ""
        vsvip.migrate_vsvip(cloud.target_cloud_url, vrfcontext.target_vrfcontext_url, vrfcontext.target_vrfcontext_tier1path, args.prefix, migration_tracker.tracker_csv, target_dns_domain, target_ipam_network, target_ipam_subnet, ipamproviderprofile.create_ipam_block(target_ipam_network, target_ipam_subnet))
    else:
        vsvip.dict_originalvsvipurl_migratedvsvipurl = {}
    
    #Migrate Virtual Services to the target cloud account
    print_func(titles.vs_migrate)
    if args.virtual_hosted_vs is None:
        virtualservice.migrate_virtualservice(pool_vs.dict_originalpoolurl_migratedpoolurl, poolgroup_vs.dict_originalpoolgroupurl_migratedpoolgroupurl, httppolicyset.dict_vs_httppolicysetmigratedurl, vsvip.dict_originalvsvipurl_migratedvsvipurl, cloud.target_cloud_url, vrfcontext.target_vrfcontext_url, segroup.target_segroup_url, args.prefix, migration_tracker.tracker_csv)
    elif args.virtual_hosted_vs is not None:
        virtualservice.migrate_parent_child_virtualservice(pool_vs.dict_originalpoolurl_migratedpoolurl, poolgroup_vs.dict_originalpoolgroupurl_migratedpoolgroupurl, httppolicyset.dict_vs_httppolicysetmigratedurl, vsvip.dict_originalvsvipurl_migratedvsvipurl, cloud.target_cloud_url, vrfcontext.target_vrfcontext_url, segroup.target_segroup_url, args.prefix, migration_tracker.tracker_csv)
    
    #Logout from NSX ALB Controller
    print_func(titles.logout)
    print_func("\nMigration is successful, now logging out from NSX ALB Controller...")
    logout = NsxAlbLogout(URL, headers, args.prefix)
    logout.end_session()
    print_func(f"\nReview the migration tracker at [{migration_tracker.tracker_csv}] to verify the migration status.\n")
    print_func(titles.thanks)

main()