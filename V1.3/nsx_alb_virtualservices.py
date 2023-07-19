#Import modules
from urllib import response
import requests
import sys
import pandas
from tabulate import tabulate

#Class for the Virtual Service Object
class NsxAlbVirtualService:
    def __init__(self, url, headers, **kwargs):
        self._url = url + "/api/virtualservice"
        self._headers = headers
        self._dict_cloud_url_name = kwargs.get("dict_cloud_url_name", {})
        self._dict_pool_url_name = kwargs.get("dict_pool_url_name", {})
        self._dict_poolgroup_url_name = kwargs.get("dict_poolgroup_url_name", {})
        self._dict_vsvip_url_name = kwargs.get("dict_vsvip_url_name", {})
        self._run_id = kwargs.get("run_id", "")
        self._migrate_parent_child_vs = kwargs.get("migrate_parent_child_vs", "")
        self._originalvsurl_migratedvsurl = {}

    def print_func(self, item):
        print(item)                
        with open(f"./logs/run-{self._run_id}.log", "a", encoding="utf-8") as outfile:
            print(item, file=outfile)

    #Class Method to get the list of all Virtual Services and to handle API Pagination
    def get_virtualservice(self):
        self._list_virtualservices = [] #Returns a list of dictionaries of all virtual services in the tenant 
        self._list_virtualservices_parentonly = []
        self._list_virtualservices_childonly = []
        self._dict_vs_cloudname = {} #Retuns a dictionary of virtual service (key) and cloud name (value)
        self._dict_vs_cloudname_vstype = {}
        self._dict_vs_originalpoolname = {} #Retuns a dictionary of virtual service (key) and original pool name, original poolgroup name and "POOL_NONE" if no pools/poolgroups found (value)
        self._dict_vs_originalpoolgroupname = {}
        self._dict_vs_pool_none = {} #Returns a dictionary of virtual services with no pools
        self._dict_vs_originalvsvipname = {}
        self._list_vs_poolname_cloudname = [] #Returns a list of list
        self._list_vs_vstype_poolname_cloudname = []
        self._list_vs_poolgroupname_cloudname = [] #Returns a list of list
        self._list_parent_vs = []
        self._list_child_vs = []

        if self._migrate_parent_child_vs is None:
            new_results = True
            page = 1
            while new_results: #Handles API pagination
                response = requests.get(self._url + f"?page={page}", headers=self._headers, verify=False)
                response_body = response.json()
                new_results = response_body.get("results", []) #Returns False if "results" not found
                for vs in new_results:
                    if vs != []:
                        self._list_virtualservices.append(vs)
                        if vs.get("type", "") == "VS_TYPE_VH_PARENT":
                            self._list_parent_vs.append(vs.get("name"))
                        elif vs.get("type", "") == "VS_TYPE_VH_CHILD":
                            self._list_child_vs.append(vs.get("name"))
                        for cloud in self._dict_cloud_url_name:
                            if vs["cloud_ref"] == cloud:
                                self._dict_vs_cloudname[vs["name"]] = self._dict_cloud_url_name[cloud]
                                self._dict_vs_cloudname_vstype[vs["name"]] = [self._dict_cloud_url_name[cloud], vs.get("type", "")]
                        if "vsvip_ref" in vs.keys():
                            for vsvip in self._dict_vsvip_url_name:
                                if vs["vsvip_ref"] == vsvip:
                                    self._dict_vs_originalvsvipname[vs["name"]] = self._dict_vsvip_url_name[vsvip]
                        else:
                            self._dict_vs_originalvsvipname[vs["name"]] = "VSVIP_NONE"
                        if "pool_ref" in vs.keys():
                            for pool in self._dict_pool_url_name:                        
                                if vs["pool_ref"] == pool:
                                    self._dict_vs_originalpoolname[vs["name"]] = self._dict_pool_url_name[pool]
                        elif "pool_group_ref" in vs.keys():
                            for poolgroup in self._dict_poolgroup_url_name:                        
                                if vs["pool_group_ref"] == poolgroup:
                                    self._dict_vs_originalpoolname[vs["name"]] = self._dict_poolgroup_url_name[poolgroup] + " (Pool_Group)"
                                    self._dict_vs_originalpoolgroupname[vs["name"]] = self._dict_poolgroup_url_name[poolgroup]
                        else:
                            self._dict_vs_originalpoolname[vs["name"]] = "POOL_NONE"
                page += 1
            
            if (len(self._list_virtualservices) == 0) and (response == False): #Handle a scenario where error is encountered to display Virtual Services
                self.print_func(f"\nList NSX ALB Virtual Services Unsuccessful ({response.status_code})\n")
                #Print the error details in table using tabulate function
                self.print_func(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
                sys.exit()

            if (len(self._list_virtualservices) == 0): #Handle a scenario where there are no virtual services in NSX ALB tenant
                self.print_func(f"\nNo Virtual Services found in the tenant ({response.status_code})\n")
                #Print the error details in table using tabulate function
                self.print_func(tabulate([["No VS found", "Please check if you are in the correct tenant context."]], headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
                sys.exit()
            
            '''Staging area for reorganizing the objects to display'''
            for vs1,cloud_vstype in self._dict_vs_cloudname_vstype.items():
                for vs2 in self._dict_vs_originalpoolname:
                    if vs1 == vs2:
                        self._list_vs_vstype_poolname_cloudname.append([vs1, cloud_vstype[1], self._dict_vs_originalpoolname[vs2], cloud_vstype[0]])
            if len(self._list_vs_vstype_poolname_cloudname) != 0:
                self.print_func("\nNOTE : You are in NORMAL VS Migration mode. If you want to migrate VS of type \"PARENT - CHILD\" , switch the mode by running the migrator with the \"--virtual_hosted_vs\" parameter.\n\n")
                self.print_func(f"\n\nDiscovered {len(self._list_virtualservices)} Virtual Services in Tenant '{self._headers['X-Avi-Tenant']}'. Virtual Services, their Pools/Pool_Groups and Cloud details are as below:\n")
                self.print_func(tabulate(self._list_vs_vstype_poolname_cloudname, headers=["Virtual Service", "VS_Type", "Pool / Pool_Group", "Cloud"], showindex=True, tablefmt="fancy_grid"))

        elif self._migrate_parent_child_vs is not None:
            self._dict_parentvs_childvs = {}
            new_results = True
            page = 1
            while new_results: #Handles API pagination
                response = requests.get(self._url + f"?page={page}", headers=self._headers, verify=False)
                response_body = response.json()
                new_results = response_body.get("results", []) #Returns False if "results" not found
                for vs in new_results:
                    if vs != []:
                        if vs.get("type", "") == "VS_TYPE_VH_PARENT" or vs.get("type", "") == "VS_TYPE_VH_CHILD":
                            self._list_virtualservices.append(vs)
                            if "vsvip_ref" in vs.keys():
                                for vsvip in self._dict_vsvip_url_name:
                                    if vs["vsvip_ref"] == vsvip:
                                        self._dict_vs_originalvsvipname[vs["name"]] = self._dict_vsvip_url_name[vsvip]
                            else:
                                self._dict_vs_originalvsvipname[vs["name"]] = "VSVIP_NONE"
                            if "pool_ref" in vs.keys():
                                for pool in self._dict_pool_url_name:                        
                                    if vs["pool_ref"] == pool:
                                        self._dict_vs_originalpoolname[vs["name"]] = self._dict_pool_url_name[pool]
                            elif "pool_group_ref" in vs.keys():
                                for poolgroup in self._dict_poolgroup_url_name:                        
                                    if vs["pool_group_ref"] == poolgroup:
                                        self._dict_vs_originalpoolname[vs["name"]] = self._dict_poolgroup_url_name[poolgroup] + " (Pool_Group)"
                                        self._dict_vs_originalpoolgroupname[vs["name"]] = self._dict_poolgroup_url_name[poolgroup]
                            else:
                                self._dict_vs_originalpoolname[vs["name"]] = "POOL_NONE"

                        if vs.get("type", "") == "VS_TYPE_VH_PARENT":
                            self._list_virtualservices_parentonly.append(vs)
                            self._list_parent_vs.append(vs.get("name"))
                        elif vs.get("type", "") == "VS_TYPE_VH_CHILD":
                            self._list_virtualservices_childonly.append(vs)
                            self._list_child_vs.append(vs.get("name"))
                page += 1

            for each_parent_vs in self._list_virtualservices_parentonly:
                list_child_names = []
                if not each_parent_vs.get("vh_child_vs_uuid", []):
                    list_child_names.append("CHILD_NONE")
                else:
                    for each_child_uuid in each_parent_vs.get("vh_child_vs_uuid", []):
                        for each_child_vs in self._list_virtualservices_childonly:
                            if each_child_uuid == each_child_vs.get("uuid", ""):
                                list_child_names.append(each_child_vs.get("name"))
                
                self._dict_parentvs_childvs.update(
                    {
                        each_parent_vs.get("name") : list_child_names
                    }
                )

            if (len(self._list_virtualservices) == 0) and (response == False): #Handle a scenario where error is encountered to display Virtual Services
                self.print_func(f"\nList NSX ALB Virtual Services Unsuccessful ({response.status_code})\n")
                #Print the error details in table using tabulate function
                self.print_func(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
                sys.exit()

            if (len(self._list_virtualservices) == 0): #Handle a scenario where there are no virtual services in NSX ALB tenant
                self.print_func(f"\nNo Parent-Child Virtual Services found in the tenant ({response.status_code})\n")
                #Print the error details in table using tabulate function
                self.print_func(tabulate([["No Parent-Child VS found", "Please check if you are in the correct tenant context."]], headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
                sys.exit()

            '''Staging area for reorganizing the objects to display'''
            self._list_parentvs_cloud_childvs = []
            for parent_vs, list_child_vs_names in self._dict_parentvs_childvs.items():
                for vs in self._list_virtualservices:
                    if parent_vs == vs["name"]:
                        for cloud in self._dict_cloud_url_name:
                            if vs["cloud_ref"] == cloud:
                                self._list_parentvs_cloud_childvs.append([parent_vs, self._dict_cloud_url_name[cloud], ("\n").join(list_child_vs_names)])
            self.print_func("\nNOTE : You are in Parent-Child VS Migration mode. If you want to migrate VS of type \"NORMAL\" run the migrator without the \"--virtual_hosted_vs\" parameter.\n\n")
            self.print_func("\nThe below Parent-Child Virtual Services were found in the NSX ALB tenant.\n")
            self.print_func(tabulate(self._list_parentvs_cloud_childvs, headers=["Parent VS", "Cloud", "Child VS"], showindex=True, tablefmt="fancy_grid"))   


    def set_virtualservice(self):
        ''' Method to select the list of virtual services to be migrated and create a dictionary of virtual service and original pool mapping '''
        self.get_virtualservice() #get_virtualservice() method is a pre-requisite for the set_virtualservice method
        self._dict_vs_typo_errors = {} #Dictionary to catch any VS type errors
        self.dict_selectedvs_originalpoolname = {}
        self.dict_selectedvs_originalpoolgroupname = {}
        self.dict_selectedvs_originalvsvipname = {}
        self._dict_excluded_vs_parent = {}
        self._dict_excluded_vs_child = {}
        self._dict_excluded_vs_parent_child = {}
        self._dict_incorrect_selected_vs = {}

        if self._migrate_parent_child_vs is None:
            self.print_func("\nNOTE : The migrator is running in \"NORMAL\" VS migration mode. This mode will only migrate VS of type \"VS_TYPE_NORMAL\". \nTo migrate Parent-Child Virtual Services, run the migrator with the \"--virtual_hosted_vs\" parameter\n\n")
            self._list_vs_selected = input(f"\nEnter Virtual Services (\"NORMAL\") to migrate separated by comma (,) and without quotes. Type 'all' for all VS \n(Eg: VS1,VS2,VS3 or all)\n\n").split(",")
            if self._list_vs_selected == ["all", ]:
                self._list_vs_selected = list(self._dict_vs_originalpoolname.keys())
            for vs_selected in self._list_vs_selected:
                if vs_selected in list(self._dict_vs_originalpoolname.keys()):
                    if vs_selected in self._list_parent_vs:
                        self._dict_excluded_vs_parent.update(
                            {
                                vs_selected : "VS_TYPE_VH_PARENT"
                            }
                        )
                        self._dict_excluded_vs_parent_child.update(
                            {
                                vs_selected : "VS_TYPE_VH_PARENT"
                            }
                        )
                    elif vs_selected in self._list_child_vs:
                        self._dict_excluded_vs_child.update(
                            {
                                vs_selected : "VS_TYPE_VH_CHILD"
                            }
                        )
                        self._dict_excluded_vs_parent_child.update(
                            {
                                vs_selected : "VS_TYPE_VH_CHILD"
                            }
                        )
                    for vs in self._dict_vs_originalpoolname:
                        if vs_selected == vs:
                            self.dict_selectedvs_originalpoolname[vs] = self._dict_vs_originalpoolname[vs]
                    for vs in self._dict_vs_originalpoolgroupname:
                        if vs_selected == vs:
                            self.dict_selectedvs_originalpoolgroupname[vs] = self._dict_vs_originalpoolgroupname[vs]
                    for vs in self._dict_vs_originalvsvipname:
                        if vs_selected == vs:
                            self.dict_selectedvs_originalvsvipname[vs] = self._dict_vs_originalvsvipname[vs]
                else:
                    self._dict_vs_typo_errors[vs_selected] = "VS not found. It's a possible typo, make sure the name is entered correctly"
        
            if self._dict_excluded_vs_parent or self._dict_excluded_vs_child:
                self.print_func(f"\nERROR : The below Virtual Services you entered are part of Parent-Child relationship which is not supported in this workflow. Please run the migrator with \"--virtual_hosted_vs\" parameter\n")
                self.print_func(tabulate(list(map(list, self._dict_excluded_vs_parent_child.items())), headers=["Virtual Service", "VS_TYPE"], showindex=True, tablefmt="fancy_grid"))
                self.print_func(f"\nThe tool will now exit\n")
                sys.exit()

            if len(self._dict_vs_typo_errors) != 0:
                self.print_func(f"\nThe below Virtual Services you entered were not found and will be skipped\n")
                self.print_func(tabulate(list(map(list, self._dict_vs_typo_errors.items())), headers=["Virtual Service", "Error_Details"], showindex=True, tablefmt="fancy_grid"))
            if len(self.dict_selectedvs_originalpoolname) != 0:
                self.print_func(f"\nThe below Virtual Services are selected for migration and their pool/pool_group association is as below. They will now be scanned for any HTTP Policy Sets\n")
                self.print_func(tabulate(list(map(list, self.dict_selectedvs_originalpoolname.items())), headers=["Virtual Service", "Pool / Pool_Group"], showindex=True, tablefmt="fancy_grid"))
            else:
                self.print_func("\nNo Virtual Services selected, Exiting..\n")
                sys.exit()

        elif self._migrate_parent_child_vs is not None:
            self.print_func("\nNOTE : The migrator is running in \"PARENT-CHILD\" VS migration mode. This mode will only migrate VS of type \"VS_TYPE_VH_PARENT\" and \"VS_TYPE_VH_CHILD\". \nTo migrate Normal Virtual Services, run the migrator without the \"--virtual_hosted_vs\" parameter\nEnter names of Parent Virtual Services when prompted. Do not enter Child VS names, they will be automatically migrated.\n\n")
            self._list_parentvs_selected = input(f"\nEnter Virtual Services (\"PARENT only\") to migrate separated by comma (,) and without quotes. Type 'all' for all Parent VS \n(Eg: VS1,VS2,VS3 or all)\n\n").split(",")
            if self._list_parentvs_selected == ["all", ]:
                self._list_parentvs_selected = self._list_parent_vs
            for each_vs in self._list_parentvs_selected:
                if each_vs in self._list_parent_vs:
                    continue
                elif each_vs in self._list_child_vs:
                    self._dict_incorrect_selected_vs.update(
                        {
                            each_vs : "VS_TYPE_VH_CHILD"
                        }
                    )
                else:
                    self._dict_incorrect_selected_vs.update(
                        {
                            each_vs : "Not PARENT/CHILD"
                        }
                    )

            if self._dict_incorrect_selected_vs:
                self.print_func("\nThe below Virtual Services are either not Parent VS or not found, the migrator will now exit: Please provide only the Parent VS in the prompt.\n")
                self.print_func(tabulate(list(map(list, self._dict_incorrect_selected_vs.items())), headers=["Virtual Service", "VS_TYPE"], showindex=True, tablefmt="fancy_grid"))
                sys.exit()

            self.list_selected_parentvs_for_migration = []
            self.list_selected_childvs_for_migration = []

            for each_vs in self._list_parentvs_selected:
                self.list_selected_parentvs_for_migration.append(each_vs)
                for each_childvs in self._dict_parentvs_childvs.get(each_vs, []):
                    self.list_selected_childvs_for_migration.append(each_childvs)
            
            self._list_vs_selected = []
            for each in (self.list_selected_parentvs_for_migration, self.list_selected_childvs_for_migration):
                self._list_vs_selected.extend(each)
 
            for vs_selected in self._list_vs_selected:
                for vs in self._dict_vs_originalpoolname:
                    if vs_selected == vs:
                        self.dict_selectedvs_originalpoolname[vs] = self._dict_vs_originalpoolname[vs]
                for vs in self._dict_vs_originalpoolgroupname:
                    if vs_selected == vs:
                        self.dict_selectedvs_originalpoolgroupname[vs] = self._dict_vs_originalpoolgroupname[vs]
                for vs in self._dict_vs_originalvsvipname:
                    if vs_selected == vs:
                        self.dict_selectedvs_originalvsvipname[vs] = self._dict_vs_originalvsvipname[vs]

            if len(self.dict_selectedvs_originalpoolname) != 0:
                self.print_func(f"\nThe below Virtual Services are selected for migration and their pool/pool_group association is as below. They will now be scanned for any HTTP Policy Sets\n")
                self.print_func(tabulate(list(map(list, self.dict_selectedvs_originalpoolname.items())), headers=["Virtual Service", "Pool / Pool_Group"], showindex=True, tablefmt="fancy_grid"))
            else:
                self.print_func("\nNo Virtual Services selected, Exiting..\n")
                sys.exit()


    def get_virtualservice_policy(self, dict_httppolicyset_url_name):
        ''' Method to scan the selected VirtualServices for any HTTP Policy Sets '''
        self.dict_vs_httppolicysetname = {}
        self._dict_vs_httppolicyset_none = {}
        for selected_vs in self.dict_selectedvs_originalpoolname:
            for vs in self._list_virtualservices:
                if selected_vs == vs["name"]:
                    if "http_policies" in list(vs.keys()):
                        for policy_url in dict_httppolicyset_url_name:
                            if vs["http_policies"][0]["http_policy_set_ref"] == policy_url:
                                self.dict_vs_httppolicysetname[vs["name"]] = dict_httppolicyset_url_name[policy_url]
                    else:
                        self._dict_vs_httppolicyset_none[vs["name"]] = "POLICY_NONE"
        if len(self.dict_vs_httppolicysetname) != 0:
            self.print_func(f"\nThe selected Virtual Services for migration has the below HTTP Policy Sets defined. They will now be scanned for any Content switching Pools / PoolGroups\n")
            self.print_func(tabulate(list(map(list, self.dict_vs_httppolicysetname.items())), headers=["Virtual Service", "HTTPPolicySet_Name"], showindex=True, tablefmt="fancy_grid"))
        else:
            self.print_func(f"\nThe selected Virtual Services for migration has no HTTP Policy Sets defined\n")
            self.print_func(tabulate(list(map(list, self._dict_vs_httppolicyset_none.items())), headers=["Virtual Service", "HTTPPolicySet_Name"], showindex=True, tablefmt="fancy_grid"))

    def create_virtualservice(self, body):
        ''' Class Method to create NSX ALB VS in the Tenant on the selected Cloud Account'''
        response = requests.post(self._url, json=body, headers=self._headers, verify=False)
        if response:
            self.print_func(f"\nVirtual Service '{response.json()['name']}' successfully created ({response.status_code})\n")
        else:
            self.print_func(f"\nVirtual Service '{body['name']}' creation Failed ({response.status_code})\n")
            self.print_func(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            self.print_func("\nExiting, Please cleanup any objects that are created, fix the error and re-run the migrator \n")
            sys.exit()
        return response.json()

    def migrate_virtualservice(self, dict_originalpoolurl_migratedpoolurl, dict_originalpoolgroupurl_migratedpoolgroupurl, dict_vs_migratedhttppolicyseturl, dict_originalvsvipurl_migratedvsvipurl, target_cloud_url, target_vrfcontext_url, target_segroup_url, prefix_tag, tracker_csv):
        '''Class method to migrate Virtual Services to the selected target cloud account'''
        self._dict_migratedvs_name_url = {}
        for selected_vs, originalpool_name in list(self.dict_selectedvs_originalpoolname.items()):
            for vs in self._list_virtualservices:
                if selected_vs == vs["name"]:
                    vs_url = vs["url"]
                    del vs["_last_modified"]
                    del vs["url"]
                    del vs["uuid"]
                    del vs["cloud_type"]
                    if "discovered_networks" in list(vs.keys()):
                        del vs["discovered_networks"]
                    if "first_se_assigned_time" in list(vs.keys()):
                        del vs["first_se_assigned_time"]
                    if "requested_resource" in list(vs.keys()):
                        del vs["requested_resource"]
                    if "se_list" in list(vs.keys()):
                        del vs["se_list"]
                    if "vip_runtime" in list(vs.keys()):
                        del vs["vip_runtime"]
                    if "version" in list(vs.keys()):
                        del vs["version"]
                    if "http_policies" in list(vs.keys()):
                        for original_vs, httppolicyset in list(dict_vs_migratedhttppolicyseturl.items()):
                            if original_vs == vs["name"]:
                                vs["http_policies"][0]["http_policy_set_ref"] = dict_vs_migratedhttppolicyseturl[original_vs]
                    if "pool_ref" in list(vs.keys()):
                        for original_pool, migrated_pool in list(dict_originalpoolurl_migratedpoolurl.items()):
                            if vs["pool_ref"] == original_pool:
                                vs["pool_ref"] = migrated_pool
                    if "pool_group_ref" in list(vs.keys()):
                        for original_poolgroup, migrated_poolgroup in list(dict_originalpoolgroupurl_migratedpoolgroupurl.items()):
                            if vs["pool_group_ref"] == original_poolgroup:
                                vs["pool_group_ref"] = migrated_poolgroup
                    for originalvsvip, migratedvsvip in list(dict_originalvsvipurl_migratedvsvipurl.items()):
                        if vs["vsvip_ref"] == originalvsvip:
                            vs["vsvip_ref"] = migratedvsvip
                    vs["enabled"] = "false"
                    vs["traffic_enabled"] = "false"
                    vs["name"] = prefix_tag + "-" + vs["name"]
                    vs["cloud_ref"] = target_cloud_url
                    vs["se_group_ref"] = target_segroup_url
                    vs["vrf_context_ref"] = target_vrfcontext_url
                    migrated_vs = self.create_virtualservice(vs)
                    migrated_vs_url = self._url + "/" + migrated_vs["uuid"]
                    #Adding to tracker
                    dict_migrated_vs = {
                                "obj_type" : ["virtualservice"],
                                "obj_name" : [migrated_vs["name"]],
                                "uuid" : [migrated_vs["uuid"]],
                                "url" : [migrated_vs_url]
                            }
                    df_migrated_vs = pandas.DataFrame(dict_migrated_vs)
                    df_migrated_vs.to_csv(tracker_csv, mode='a', index=False, header=False)
                    self._dict_migratedvs_name_url[migrated_vs["name"]] = migrated_vs_url
        self.print_func(f"\nThe below Virtual Services are migrated successfully\n")
        self.print_func(tabulate(list(map(list,self._dict_migratedvs_name_url.items())), headers=["Migrated_VS_name", "Migrated_VS_Ref"], showindex=True, tablefmt="fancy_grid"))
    
    def migrate_parent_child_virtualservice(self, dict_originalpoolurl_migratedpoolurl, dict_originalpoolgroupurl_migratedpoolgroupurl, dict_vs_migratedhttppolicyseturl, dict_originalvsvipurl_migratedvsvipurl, target_cloud_url, target_vrfcontext_url, target_segroup_url, prefix_tag, tracker_csv):
        '''Class method to migrate Parent-Child Virtual Services to the selected target cloud account'''
        self._dict_migratedvs_name_url = {}
        for vsname_list in (self.list_selected_parentvs_for_migration, self.list_selected_childvs_for_migration):
            for each_vs_selected in vsname_list:
                for dict_vs in self._list_virtualservices:
                    if each_vs_selected == dict_vs["name"]:
                        vs_url = dict_vs["url"]
                        del dict_vs["_last_modified"]
                        del dict_vs["url"]
                        del dict_vs["uuid"]
                        del dict_vs["cloud_type"]
                        if "discovered_networks" in list(dict_vs.keys()):
                            del dict_vs["discovered_networks"]
                        if "first_se_assigned_time" in list(dict_vs.keys()):
                            del dict_vs["first_se_assigned_time"]
                        if "requested_resource" in list(dict_vs.keys()):
                            del dict_vs["requested_resource"]
                        if "se_list" in list(dict_vs.keys()):
                            del dict_vs["se_list"]
                        if "vip_runtime" in list(dict_vs.keys()):
                            del dict_vs["vip_runtime"]
                        if "version" in list(dict_vs.keys()):
                            del dict_vs["version"]
                        if dict_vs["type"] == "VS_TYPE_VH_PARENT":
                            if "vh_child_vs_uuid" in list(dict_vs.keys()):
                                del dict_vs["vh_child_vs_uuid"]                        
                        if "http_policies" in list(dict_vs.keys()):
                            for original_vs, httppolicyset in list(dict_vs_migratedhttppolicyseturl.items()):
                                if original_vs == dict_vs["name"]:
                                    dict_vs["http_policies"][0]["http_policy_set_ref"] = dict_vs_migratedhttppolicyseturl[original_vs]
                        if "pool_ref" in list(dict_vs.keys()):
                            for original_pool, migrated_pool in list(dict_originalpoolurl_migratedpoolurl.items()):
                                if dict_vs["pool_ref"] == original_pool:
                                    dict_vs["pool_ref"] = migrated_pool
                        if "pool_group_ref" in list(dict_vs.keys()):
                            for original_poolgroup, migrated_poolgroup in list(dict_originalpoolgroupurl_migratedpoolgroupurl.items()):
                                if dict_vs["pool_group_ref"] == original_poolgroup:
                                    dict_vs["pool_group_ref"] = migrated_poolgroup
                        if "vsvip_ref" in list(dict_vs.keys()):
                            for originalvsvip, migratedvsvip in list(dict_originalvsvipurl_migratedvsvipurl.items()):
                                if dict_vs["vsvip_ref"] == originalvsvip:
                                    dict_vs["vsvip_ref"] = migratedvsvip
                        if dict_vs["type"] == "VS_TYPE_VH_CHILD":
                            if "vh_parent_vs_ref" in list(dict_vs.keys()):
                                for each_uuid in self._originalvsurl_migratedvsurl:
                                    if dict_vs["vh_parent_vs_ref"] == each_uuid:
                                        dict_vs["vh_parent_vs_ref"] = self._originalvsurl_migratedvsurl[each_uuid]
                        dict_vs["enabled"] = "false"
                        dict_vs["traffic_enabled"] = "false"
                        dict_vs["name"] = prefix_tag + "-" + dict_vs["name"]
                        dict_vs["cloud_ref"] = target_cloud_url
                        dict_vs["se_group_ref"] = target_segroup_url
                        dict_vs["vrf_context_ref"] = target_vrfcontext_url
                        migrated_vs = self.create_virtualservice(dict_vs)
                        migrated_vs_url = self._url + "/" + migrated_vs["uuid"]
                        self._originalvsurl_migratedvsurl.update(
                            {
                                vs_url : migrated_vs_url
                            }
                        )
                        #Adding to tracker
                        dict_migrated_vs = {
                                    "obj_type" : ["virtualservice"],
                                    "obj_name" : [migrated_vs["name"]],
                                    "uuid" : [migrated_vs["uuid"]],
                                    "url" : [migrated_vs_url]
                                }
                        df_migrated_vs = pandas.DataFrame(dict_migrated_vs)
                        df_migrated_vs.to_csv(tracker_csv, mode='a', index=False, header=False)
                        self._dict_migratedvs_name_url[migrated_vs["name"]] = migrated_vs_url
        self.print_func(f"\nThe below Virtual Services are migrated successfully\n")
        self.print_func(tabulate(list(map(list,self._dict_migratedvs_name_url.items())), headers=["Migrated_VS_name", "Migrated_VS_Ref"], showindex=True, tablefmt="fancy_grid"))


    def slice_virtualservice_name(self, virtualservice_name):
        start_index = virtualservice_name.find(self._run_id) + len(self._run_id) + 1
        return virtualservice_name[start_index:]
        
    def remove_virtualservice_prefix(self, obj_tracker, headers):
        ''' Class Method to remove the prefixes of NSX ALB virtualservices '''
        self.get_virtualservice() #get_virtualservice methos is a pre-requisite for calling migrate_virtualservice method
        df_obj_track_csv = pandas.read_csv(obj_tracker + "/obj_track-" + self._run_id + ".csv")
        for index, row in df_obj_track_csv.iterrows():
            if row["obj_type"] == "virtualservice":
                for virtualservice in self._list_virtualservices:
                    if virtualservice["url"] == row["url"]:
                        if virtualservice["name"][:len(self._run_id)] == self._run_id:
                            virtualservice["name"] = self.slice_virtualservice_name(virtualservice["name"])
                            response = requests.put(virtualservice["url"], json=virtualservice, headers=headers, verify=False )
                            if response:
                                print(f"\nvirtualservice Prefix for {self._run_id + '-' + response.json()['name']} removed successfully ({response.status_code}). New Object name is '{response.json()['name']}'\n")
                                dict_df_obj_remove_prefix_status = {
                                    "obj_type" : ["virtualservice"],
                                    "obj_name_old" : [row["obj_name"]],
                                    "obj_name_new" : [response.json()['name']],
                                    "PREFIX_REMOVAL_STATUS" : ["SUCCESS"],
                                    "Error" : [""]
                                }  
                                df_obj_remove_prefix_status = pandas.DataFrame(dict_df_obj_remove_prefix_status)
                                df_obj_remove_prefix_status.to_csv(obj_tracker + "/obj_prefix_removal_status_" + self._run_id + ".csv", index=False, mode='a', header=False)
                            else:
                                print(f"\nvirtualservice Prefix removal failed for {self._run_id + '-' + virtualservice['name']} - ({response.status_code})\n")
                                dict_df_obj_remove_prefix_status = {
                                    "obj_type" : ["virtualservice"],
                                    "obj_name_old" : [row["obj_name"]],
                                    "obj_name_new" : [row["obj_name"]],
                                    "PREFIX_REMOVAL_STATUS" : ["FAILURE"],
                                    "Error" : [response.json()]
                                }  
                                df_obj_remove_prefix_status = pandas.DataFrame(dict_df_obj_remove_prefix_status)
                                df_obj_remove_prefix_status.to_csv(obj_tracker + "/obj_prefix_removal_status_" + self._run_id + ".csv", index=False, mode='a', header=False)
                        else:
                            print(f"\nPrefix tag missing in {virtualservice['name']}, hence not renamed")
                            dict_df_obj_remove_prefix_status = {
                                    "obj_type" : ["virtualservice"],
                                    "obj_name_old" : [row["obj_name"]],
                                    "obj_name_new" : [virtualservice["name"]],
                                    "PREFIX_REMOVAL_STATUS" : ["FAILURE"],
                                    "Error" : [f"Prefix tag missing in {virtualservice['name']}"]
                                }  
                            df_obj_remove_prefix_status = pandas.DataFrame(dict_df_obj_remove_prefix_status)
                            df_obj_remove_prefix_status.to_csv(obj_tracker + "/obj_prefix_removal_status_" + self._run_id + ".csv", index=False, mode='a', header=False)                
