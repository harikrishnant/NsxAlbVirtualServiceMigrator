#Import Modules
import urllib3
import sys
import titles
from art import logo, line
from getpass import getpass
from tabulate import tabulate
from nsx_alb_login import NsxAlbLogin
from nsx_alb_tenants import NsxAlbTenant
from nsx_alb_clouds import NsxAlbCloud
from nsx_alb_vrfcontexts import NsxAlbVrfContext
from nsx_alb_segroups import NsxAlbSeGroup
from nsx_alb_pools import NsxAlbPool
from nsx_alb_poolgroups import NsxAlbPoolGroup
from nsx_alb_httppolicysets import NsxAlbHttpPolicySet
from nsx_alb_vsvips import NsxAlbVsVip
from nsx_alb_virtualservices import NsxAlbVirtualService
from nsx_alb_logout import NsxAlbLogout

def main():
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    print(logo)

    URL = input("Enter NSX ALB controller login URL (Eg: https://controller.corp.local): ")
    LOGIN = {
                "username": input("Username: "), 
                "password": getpass(prompt="Password: "), 
            }
    headers = {
                "Content-Type": "application/json",
                "Referer": URL,
                "Accept-Encoding": "application/json",
                "X-Avi-Tenant": input("Enter the NSX ALB Tenant: "),
                "X-Avi-Version": input("Enter the NSX ALB Controller Version: ")
            }

    #Login, fetch CSRFToken and set Header Cookie
    print(titles.login)
    login = NsxAlbLogin(URL, LOGIN, headers)
    login.get_cookie()
    headers["X-CSRFToken"] = login.csrf_token
    headers["Cookie"] = login.cookie

    #Verify Tenant exists and login to tenant is successful
    tenant = NsxAlbTenant(URL, headers)
    tenant.get_tenant()

    #List all NSX ALB cloud accounts and select the target cloud for migration
    print(titles.cloud)
    cloud = NsxAlbCloud(URL, headers)
    cloud.set_cloud()

    #List all VRFs under the selected NSX ALB cloud account and select the target VRF for migration
    print(titles.vrfcontext)
    vrfcontext = NsxAlbVrfContext(URL, headers, cloud.target_cloud_url, cloud.target_cloud_name)
    vrfcontext.set_vrfcontext()

    #List all Service Engine Groups (SEG) under the selected NSX ALB cloud account and select the target SEG for migration
    print(titles.serviceenginegroup)
    segroup = NsxAlbSeGroup(URL, headers, cloud.target_cloud_url, cloud.target_cloud_name)
    segroup.set_segroup()

    #Fetch pool information from the NSX ALB Tenant
    pool = NsxAlbPool(URL, headers)
    pool.get_pool()

    #Fetch Pool Group information for virtual services from the NSX ALB Tenant
    poolgroup = NsxAlbPoolGroup(URL, headers)
    poolgroup.get_poolgroup()

    #Fetch VS VIP information for virtual services from the NSX ALB Tenant
    vsvip = NsxAlbVsVip(URL, headers)
    vsvip.get_vsvip()

    #List the Virtual Services under the Tenant and select the Virtual Services for migration
    print(titles.vs_selector)
    virtualservice = NsxAlbVirtualService(URL, headers, cloud.dict_cloud_url_name, pool.dict_pool_url_name, poolgroup.dict_poolgroup_url_name, vsvip.dict_vsvip_url_name)
    virtualservice.set_virtualservice()

    #Scan for HTTPPolicySets in the Tenant
    httppolicyset = NsxAlbHttpPolicySet(URL, headers)
    httppolicyset.get_httppolicyset()

    #Scan selected Virtual Services for any HTTP Policy Sets and Content Switching Pools
    print(titles.httppolicyset_selector)
    virtualservice.get_virtualservice_policy(httppolicyset.dict_httppolicyset_url_name)
    print(titles.httppolicyset_scanner)
    httppolicyset.get_httppolicyset_pool(virtualservice.dict_vs_httppolicysetname, pool.dict_pool_url_name, poolgroup.dict_poolgroup_url_name)

    #Enter suffix to denote the migrated objects of the run 
    suffix_tag = input("\nEnter name suffix to identify migrated objects: ")

    #Migrate Pools in Content Switching Policies to target NSX ALB Cloud Account
    pool_cs = NsxAlbPool(URL, headers) #Initialize a pool object to migrate pools in content switching policies
    if len(httppolicyset.dict_cs_originalpool_url_name) != 0: 
        print(titles.httppolicyset_migrate_pools)
        pool_cs_migrate_prompt = input(f"\nMigrating pools in content switching policies to Cloud Account '{cloud.target_cloud_name}'\nWARNING - This is a WRITE Operation. Press Y to continue ").lower()
        if pool_cs_migrate_prompt == "y":
            pool_cs.migrate_pool(httppolicyset.dict_cs_originalpool_url_name, cloud.target_cloud_url, vrfcontext.target_vrfcontext_url, vrfcontext.target_vrfcontext_tier1path, suffix_tag)
        else:
            print(f"\n Invalid input, exiting \n")
            sys.exit()
    else:
        pool_cs.dict_originalpoolurl_migratedpoolurl = {}

    #Migrate Pool groups in Content Switching Policies to target NSX ALB Cloud Account    
    poolgroup_cs = NsxAlbPoolGroup(URL, headers)
    poolgroup_cs.get_poolgroup()
    if len(httppolicyset.dict_cs_originalpoolgroup_url_name) != 0:
        print(titles.httppolicyset_migratepoolgroups)
        poolgroup_migrate_prompt = input(f"\nMigrating Pool Groups of Content Switching Policies to Cloud Account '{cloud.target_cloud_name}'\nWARNING - This is a WRITE Operation. Press Y to continue ").lower()
        if poolgroup_migrate_prompt == "y":        
            poolgroup_cs.get_poolgroup_member(httppolicyset.dict_cs_originalpoolgroup_url_name, pool.dict_pool_url_name)
            pool_pg_cs = NsxAlbPool(URL, headers) #Initialize a pool object to migrate pools in Pool Groups assocaited with Content Switching Policies
            if len(poolgroup_cs.dict_poolgroupmembers_url_name) != 0:            
                pool_pg_cs.migrate_pool(poolgroup_cs.dict_poolgroupmembers_url_name, cloud.target_cloud_url, vrfcontext.target_vrfcontext_url, vrfcontext.target_vrfcontext_tier1path, suffix_tag)
            else:
                pool_pg_cs.dict_originalpoolurl_migratedpoolurl = {}
            poolgroup_cs.migrate_poolgroup(httppolicyset.dict_cs_originalpoolgroup_url_name, pool_pg_cs.dict_originalpoolurl_migratedpoolurl, cloud.target_cloud_url, suffix_tag)
        else:
            print(f"\n Invalid input, exiting \n")
            sys.exit()     
    else:
        poolgroup_cs.dict_originalpoolgroupurl_migratedpoolgroupurl = {}
    
    #Migrate HTTP Policy Sets to target NSX ALB Cloud Account
    if len(httppolicyset.dict_cs_originalpool_url_name) != 0 or len(httppolicyset.dict_cs_originalpoolgroup_url_name) != 0: 
        print(titles.httppolicyset_migrate)
        httppolicyset_migrate_prompt = input(f"\nMigrating HTTP Policy Sets with new Pool / Pool Group association\nWARNING - This is a WRITE Operation. Press Y to continue ").lower()
        if httppolicyset_migrate_prompt == "y":
            httppolicyset.migrate_httppolicyset(pool_cs.dict_originalpoolurl_migratedpoolurl, poolgroup_cs.dict_originalpoolgroupurl_migratedpoolgroupurl, suffix_tag)
        else:
            print(f"\n Invalid input, exiting \n")
            sys.exit()
    else:
        httppolicyset.dict_vs_httppolicysetmigratedurl = {}

    #Migrate Pool Groups directly associated with Virtual Services to target NSX ALB Cloud
    poolgroup_vs = NsxAlbPoolGroup(URL, headers)
    poolgroup_vs.get_poolgroup()
    poolgroup_vs.set_poolgroup(virtualservice.dict_selectedvs_originalpoolgroupname)
    if len(poolgroup_vs.dict_selectedpoolgroup_url_name) != 0:
        print(titles.vs_migratepoolgroups)
        poolgroup_migrate_prompt = input(f"\nMigrating Pool Groups associated to selected Virtual services to Cloud Account '{cloud.target_cloud_name}'\nWARNING - This is a WRITE Operation. Press Y to continue ").lower()
        if poolgroup_migrate_prompt == "y":
            poolgroup_vs.get_poolgroup_member(poolgroup_vs.dict_selectedpoolgroup_url_name, pool.dict_pool_url_name)
            pool_pg_vs = NsxAlbPool(URL, headers) #Initialize a pool object to migrate pools in Pool Groups assocaited with Virtual services
            if len(poolgroup_vs.dict_poolgroupmembers_url_name) != 0:
                pool_pg_vs.migrate_pool(poolgroup_vs.dict_poolgroupmembers_url_name, cloud.target_cloud_url, vrfcontext.target_vrfcontext_url, vrfcontext.target_vrfcontext_tier1path, suffix_tag)
            else:
                pool_pg_vs.dict_originalpoolurl_migratedpoolurl = {}
            poolgroup_vs.migrate_poolgroup(poolgroup_vs.dict_selectedpoolgroup_url_name, pool_pg_vs.dict_originalpoolurl_migratedpoolurl, cloud.target_cloud_url, suffix_tag)
        else:
            print(f"\n Invalid input, exiting \n")
            sys.exit()
    else:
        poolgroup_vs.dict_originalpoolgroupurl_migratedpoolgroupurl = {}     
   
    #Migrate Pools directly associated with Virtual Services to target NSX ALB Cloud
    pool_vs = NsxAlbPool(URL, headers) 
    pool_vs.set_pool(virtualservice.dict_selectedvs_originalpoolname)
    if len(pool_vs.dict_selectedpool_url_name) != 0:
        print(titles.vs_migratepools)
        pool_vs_migrate_prompt = input(f"\nMigrating Pools associated to selected Virtual Services to Cloud Account '{cloud.target_cloud_name}'\nWARNING - This is a WRITE Operation. Press Y to continue ").lower()
        if pool_vs_migrate_prompt == "y":
            pool_vs.migrate_pool(pool_vs.dict_selectedpool_url_name, cloud.target_cloud_url, vrfcontext.target_vrfcontext_url, vrfcontext.target_vrfcontext_tier1path, suffix_tag)
        else:
            print(f"\n Invalid input, exiting \n")
            sys.exit()
    else:
        pool_vs.dict_originalpoolurl_migratedpoolurl = {}

    #Migrate VS VIPs of selected Virtual Services to target NSX ALB Cloud
    vsvip.set_vsvip(virtualservice.dict_selectedvs_originalvsvipname)
    if len(vsvip.dict_selectedvsvip_url_name) != 0:
        print(titles.vsvip_migrate)
        vsvip_migrate_prompt = input(f"\nMigrating VS VIPs associated with selected Virtual Services to Cloud Account '{cloud.target_cloud_name}'\nWARNING - This is a WRITE Operation. Press Y to continue ").lower()
        if vsvip_migrate_prompt == "y":
            vsvip.migrate_vsvip(cloud.target_cloud_url, vrfcontext.target_vrfcontext_url, vrfcontext.target_vrfcontext_tier1path, suffix_tag)
        else:
            print(f"\n Invalid input, exiting \n")
            sys.exit()
    else:
        vsvip.dict_originalvsvipurl_migratedvsvipurl = {}

    #Migrate Virtual Services to the target cloud account
    print(titles.vs_migrate)
    vs_migrate_prompt = input(f"\nMigrating selected Virtual Services to Cloud Account '{cloud.target_cloud_name}'\nWARNING - This is a WRITE Operation. Press Y to continue ").lower()
    if vs_migrate_prompt == "y":
        virtualservice.migrate_virtualservice(pool_vs.dict_originalpoolurl_migratedpoolurl, poolgroup_vs.dict_originalpoolgroupurl_migratedpoolgroupurl, httppolicyset.dict_vs_httppolicysetmigratedurl, vsvip.dict_originalvsvipurl_migratedvsvipurl, cloud.target_cloud_url, vrfcontext.target_vrfcontext_url, segroup.target_segroup_url, suffix_tag)
    else:
        print(f"\n Invalid input, exiting \n")
        sys.exit()
    
    #Logout from NSX ALB Controller
    print(titles.logout)
    print("\nMigration is successful, now logging out from NSX ALB Controller...")
    logout = NsxAlbLogout(URL, headers)
    logout.end_session()
    print(titles.thanks)

main()