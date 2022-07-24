#Import modules
import requests
import sys
import pandas
from tabulate import tabulate
from art import line

class NsxAlbHttpPolicySet:
    def __init__(self, url, headers, run_id):
        self._url = url + "/api/httppolicyset"
        self._headers = headers
        self._run_id = run_id

    def print_func(self, item):
        print(item)                
        with open(f"./logs/run-{self._run_id}.log", "a", encoding="utf-8") as outfile:
            print(item, file=outfile)

    def get_httppolicyset(self):
        ''' Class Method to get the list of all HTTP Policy Sets under the Tenant and to handle API Pagination '''
        self.dict_httppolicyset_url_name = {}
        self._list_httppolicysets = []
        new_results = True
        page = 1
        while new_results:
            response = requests.get(self._url + f"?page={page}", headers=self._headers, verify=False)
            response_body = response.json()
            new_results = response_body.get("results", []) #Returns False if "results" not found
            for httppolicyset in new_results:
                if httppolicyset != []:
                    self._list_httppolicysets.append(httppolicyset)
                    self.dict_httppolicyset_url_name[httppolicyset["url"]] = httppolicyset["name"]
            page += 1
        if (len(self.dict_httppolicyset_url_name) == 0) and (response == False): #Handle a scenario where there are no HTTP policy sets defined
            self.print_func(f"Unable to scan HTTP Policy Sets ({response.status_code})\n")
            #Print the error details in table using tabulate function
            self.print_func(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            sys.exit()

    def get_httppolicyset_pool(self, dict_vs_httppolicysetname, dict_pool_url_name, dict_poolgroup_url_name):
        ''' Scan for content switching pools in the selected HTTP Policy Sets'''
        if len(dict_vs_httppolicysetname) != 0:
            self.dict_cs_originalpool_url_name = {}
            self.dict_cs_originalpoolgroup_url_name = {}
            self._list_httppolicysetname_poolname_vsname = []
            self._dict_vs_httppolicy_having_pools = {}
            for vs_selected,policy_selected in list(dict_vs_httppolicysetname.items()):
                for http_policy in self._list_httppolicysets:
                    if policy_selected == http_policy["name"]:
                        if "http_request_policy" in list(http_policy.keys()):
                            for rule in http_policy["http_request_policy"]["rules"]:
                                if "switching_action" in list(rule.keys()):
                                    if "pool_ref" in list(rule["switching_action"].keys()):
                                        self._dict_vs_httppolicy_having_pools[vs_selected] = policy_selected #Used as input for migrating HTTPPolicySets
                                        for pool in dict_pool_url_name:
                                            if rule["switching_action"]["pool_ref"] == pool:
                                                self.dict_cs_originalpool_url_name[pool] = dict_pool_url_name[pool]
                                                self._list_httppolicysetname_poolname_vsname.append([dict_pool_url_name[pool], policy_selected, vs_selected])
                                    if "pool_group_ref" in list(rule["switching_action"].keys()):
                                        self._dict_vs_httppolicy_having_pools[vs_selected] = policy_selected #Used as input for migrating HTTPPolicySets
                                        for poolgroup in dict_poolgroup_url_name:
                                            if rule["switching_action"]["pool_group_ref"] == poolgroup:
                                                self.dict_cs_originalpoolgroup_url_name[poolgroup] = dict_poolgroup_url_name[poolgroup]
                                                self._list_httppolicysetname_poolname_vsname.append([dict_poolgroup_url_name[poolgroup] + "(Pool_Group)", policy_selected, vs_selected])
            if len(self._list_httppolicysetname_poolname_vsname) != 0:
                self.print_func(f"\nThe below HTTP Policy Sets have content switching rules with pools / poolgroups defined\n")
                self.print_func(tabulate(list(map(list, self._dict_vs_httppolicy_having_pools.items())), headers=["Virtual Service", "HTTP Policy Set"], showindex=True, tablefmt="fancy_grid"))
                self.print_func(f"\nThe below Pools / PoolGroups are discovered in content switching rules and will be migrated in subsequent workflows:\n")
                self.print_func(tabulate(self._list_httppolicysetname_poolname_vsname, headers=["Pool / Pool_Group", "HTTP Policy Set", "Virtual Service"], showindex=True, tablefmt="fancy_grid"))
            else:
                self.print_func("\nSuccessfully scanned the HTTP Policy Sets of selected virtual services for migration and no content switching pools or pool groups found:")
        else:
            self.dict_cs_originalpool_url_name = {}
            self.dict_cs_originalpoolgroup_url_name = {}

    def create_httppolicyset(self, body):
        ''' Class Method to create an HTTPPolicySet in the specified Tenant'''
        response = requests.post(self._url, json=body, headers=self._headers, verify=False)
        if response:
            self.print_func(f"\nHTTP Policy Set '{response.json()['name']}' successfully created ({response.status_code})")
        else:
            self.print_func(f"\nHTTP Policy Set '{body['name']}' creation failed ({response.status_code})\n")
            self.print_func(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            self.print_func("\nExiting, Please cleanup any objects that are created, fix the error and re-run the migrator \n")
            sys.exit()
        return response.json()
    
    def migrate_httppolicyset(self, dict_cs_originalpoolurl_migratedpoolurl, dict_cs_originalpoolgroupurl_migratedpoolgroupurl, prefix_tag, tracker_csv):
        ''' Class Method to migrate HTTP Policy Sets to target cloud account '''
        self.dict_vs_httppolicysetmigratedurl = {}
        self._dict_httppolicysetmigrated_name_url = {}
        for vs_selected, httppolicyset_selected in list(self._dict_vs_httppolicy_having_pools.items()):
            for httppolicyset in self._list_httppolicysets:
                if httppolicyset_selected == httppolicyset["name"]:
                    del httppolicyset["uuid"]
                    del httppolicyset["url"]
                    del httppolicyset["_last_modified"]
                    for rule in httppolicyset["http_request_policy"]["rules"]:
                        if "switching_action" in list(rule.keys()):
                            if "pool_ref" in list(rule["switching_action"].keys()):
                                for pool in dict_cs_originalpoolurl_migratedpoolurl:
                                    if rule["switching_action"]["pool_ref"] == pool:
                                        rule["switching_action"]["pool_ref"] = dict_cs_originalpoolurl_migratedpoolurl[pool]
                            if "pool_group_ref" in list(rule["switching_action"].keys()):
                                for poolgroup in dict_cs_originalpoolgroupurl_migratedpoolgroupurl:
                                    if rule["switching_action"]["pool_group_ref"] == poolgroup:
                                        rule["switching_action"]["pool_group_ref"] = dict_cs_originalpoolgroupurl_migratedpoolgroupurl[poolgroup]
                    httppolicyset["name"] = prefix_tag + "-" + httppolicyset["name"]
                    migrated_httppolicyset = self.create_httppolicyset(httppolicyset)
                    migrated_httppolicyset_url = self._url + "/" + migrated_httppolicyset["uuid"]
                    #Append to tracker
                    dict_migrated_httppolicyset = {
                        "obj_type" : ["httppolicyset"],
                        "obj_name" : [migrated_httppolicyset["name"]],
                        "uuid" : [migrated_httppolicyset["uuid"]],
                        "url" : [migrated_httppolicyset_url]
                    }                            
                    df_migrated_httppolicyset = pandas.DataFrame(dict_migrated_httppolicyset)
                    df_migrated_httppolicyset.to_csv(tracker_csv, mode='a', index=False, header=False)
                    self.dict_vs_httppolicysetmigratedurl[vs_selected] = migrated_httppolicyset_url
                    self._dict_httppolicysetmigrated_name_url[migrated_httppolicyset["name"]] = migrated_httppolicyset_url
        if len(self._dict_httppolicysetmigrated_name_url) != 0:
            self.print_func("\nThe below HTTP Policy Sets are migrated successfully\n")
            self.print_func(tabulate(list(map(list, self._dict_httppolicysetmigrated_name_url.items())), headers=["HTTPPolicySet_Name", "HTTPPolicySet_Ref"], showindex=True, tablefmt="fancy_grid"))

    def slice_httppolicyset_name(self, httppolicyset_name):
        start_index = httppolicyset_name.find(self._run_id) + len(self._run_id) + 1
        return httppolicyset_name[start_index:]
        
    def remove_httppolicyset_prefix(self, obj_tracker, headers):
        ''' Class Method to remove the prefixes of NSX ALB httppolicysets '''
        self.get_httppolicyset() #get_pool methos is a pre-requisite for calling migrate_pool method
        df_obj_track_csv = pandas.read_csv(obj_tracker + "/obj_track-" + self._run_id + ".csv")
        for index, row in df_obj_track_csv.iterrows():
            if row["obj_type"] == "httppolicyset":
                for httppolicyset in self._list_httppolicysets:
                    if httppolicyset["url"] == row["url"]:
                        if httppolicyset["name"][:len(self._run_id)] == self._run_id:
                            httppolicyset["name"] = self.slice_httppolicyset_name(httppolicyset["name"])
                            response = requests.put(httppolicyset["url"], json=httppolicyset, headers=headers, verify=False )
                            if response:
                                print(f"\nhttppolicyset Prefix for {self._run_id + '-' + response.json()['name']} removed successfully ({response.status_code}). New Object name is '{response.json()['name']}'\n")
                                dict_df_obj_remove_prefix_status = {
                                    "obj_type" : ["httppolicyset"],
                                    "obj_name_old" : [row["obj_name"]],
                                    "obj_name_new" : [response.json()['name']],
                                    "PREFIX_REMOVAL_STATUS" : ["SUCCESS"],
                                    "Error" : [""]
                                }  
                                df_obj_remove_prefix_status = pandas.DataFrame(dict_df_obj_remove_prefix_status)
                                df_obj_remove_prefix_status.to_csv(obj_tracker + "/obj_prefix_removal_status_" + self._run_id + ".csv", index=False, mode='a', header=False)
                            else:
                                print(f"\nhttppolicyset Prefix removal failed for {self._run_id + '-' + httppolicyset['name']} - ({response.status_code})\n")
                                dict_df_obj_remove_prefix_status = {
                                    "obj_type" : ["httppolicyset"],
                                    "obj_name_old" : [row["obj_name"]],
                                    "obj_name_new" : [row["obj_name"]],
                                    "PREFIX_REMOVAL_STATUS" : ["FAILURE"],
                                    "Error" : [response.json()]
                                }  
                                df_obj_remove_prefix_status = pandas.DataFrame(dict_df_obj_remove_prefix_status)
                                df_obj_remove_prefix_status.to_csv(obj_tracker + "/obj_prefix_removal_status_" + self._run_id + ".csv", index=False, mode='a', header=False)
                        else:
                            print(f"\nPrefix tag missing in {httppolicyset['name']}, hence not renamed")
                            dict_df_obj_remove_prefix_status = {
                                    "obj_type" : ["httppolicyset"],
                                    "obj_name_old" : [row["obj_name"]],
                                    "obj_name_new" : [httppolicyset["name"]],
                                    "PREFIX_REMOVAL_STATUS" : ["FAILURE"],
                                    "Error" : [f"Prefix tag missing in {httppolicyset['name']}"]
                                }  
                            df_obj_remove_prefix_status = pandas.DataFrame(dict_df_obj_remove_prefix_status)
                            df_obj_remove_prefix_status.to_csv(obj_tracker + "/obj_prefix_removal_status_" + self._run_id + ".csv", index=False, mode='a', header=False)

    









