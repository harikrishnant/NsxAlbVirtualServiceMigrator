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

    def print_func(self, item):
        print(item)                
        with open(f"./logs/run-{self._run_id}.log", "a", encoding="utf-8") as outfile:
            print(item, file=outfile)

    #Class Method to get the list of all Virtual Services and to handle API Pagination
    def get_virtualservice(self):
        self._list_virtualservices = [] #Returns a list of dictionaries of all virtual services in the tenant 
        self._dict_vs_cloudname = {} #Retuns a dictionary of virtual service (key) and cloud name (value)
        self._dict_vs_originalpoolname = {} #Retuns a dictionary of virtual service (key) and original pool name, original poolgroup name and "POOL_NONE" if no pools/poolgroups found (value)
        self._dict_vs_originalpoolgroupname = {}
        self._dict_vs_pool_none = {} #Returns a dictionary of virtual services with no pools
        self._dict_vs_originalvsvipname = {}
        self._list_vs_poolname_cloudname = [] #Returns a list of list
        self._list_vs_poolgroupname_cloudname = [] #Returns a list of list
        new_results = True
        page = 1
        while new_results: #Handles API pagination
            response = requests.get(self._url + f"?page={page}", headers=self._headers, verify=False)
            response_body = response.json()
            new_results = response_body.get("results", []) #Returns False if "results" not found
            for vs in new_results:
                if vs != []:
                    self._list_virtualservices.append(vs)
                    for cloud in self._dict_cloud_url_name:
                        if vs["cloud_ref"] == cloud:
                            self._dict_vs_cloudname[vs["name"]] = self._dict_cloud_url_name[cloud]
                    for vsvip in self._dict_vsvip_url_name:
                        if vs["vsvip_ref"] == vsvip:
                            self._dict_vs_originalvsvipname[vs["name"]] = self._dict_vsvip_url_name[vsvip]
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
        
        if (len(self._list_virtualservices) == 0) and (response == False): #Handle a scenario where there are no virtual services in NSX ALB tenant
            self.print_func(f"\nList NSX ALB Virtual Services Unsuccessful ({response.status_code})\n")
            #Print the error details in table using tabulate function
            self.print_func(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            sys.exit()
        
        '''Staging area for reorganizing the objects to display'''
        for vs1 in self._dict_vs_cloudname:
            for vs2 in self._dict_vs_originalpoolname:
                if vs1 == vs2:
                    self._list_vs_poolname_cloudname.append([vs1, self._dict_vs_originalpoolname[vs2], self._dict_vs_cloudname[vs1]])
        if len(self._list_vs_poolname_cloudname) != 0:
            self.print_func(f"\n\nDiscovered {len(self._list_virtualservices)} Virtual Services in Tenant '{self._headers['X-Avi-Tenant']}'. Virtual Services, their Pools/Pool_Groups and Cloud details are as below:\n")
            self.print_func(tabulate(self._list_vs_poolname_cloudname, headers=["Virtual Service", "Pool / Pool_Group", "Cloud"], showindex=True, tablefmt="fancy_grid"))

    def set_virtualservice(self):
        ''' Method to select the list of virtual services to be migrated and create a dictionary of virtual service and original pool mapping '''
        self.get_virtualservice() #get_virtualservice() method is a pre-requisite for the set_virtualservice method
        self._list_vs_selected = input(f"\nEnter Virtual Services to migrate separated by comma (,) and without quotes. Type 'all' for all VS \n(Eg: VS1,VS2,VS3 or all)\n\n").split(",")
        self._dict_vs_typo_errors = {} #Dictionary to catch any VS type errors
        self.dict_selectedvs_originalpoolname = {}
        self.dict_selectedvs_originalpoolgroupname = {}
        self.dict_selectedvs_originalvsvipname = {}
        if self._list_vs_selected == ["all", ]:
            self._list_vs_selected = list(self._dict_vs_originalpoolname.keys())
        for vs_selected in self._list_vs_selected:
            if vs_selected in list(self._dict_vs_originalpoolname.keys()):
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
        
        if len(self._dict_vs_typo_errors) != 0:
            self.print_func(f"\nThe below Virtual Services you entered were not found and will be skipped\n")
            self.print_func(tabulate(list(map(list, self._dict_vs_typo_errors.items())), headers=["Virtual Service", "Error_Details"], showindex=True, tablefmt="fancy_grid"))
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
