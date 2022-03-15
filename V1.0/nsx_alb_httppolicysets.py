#Import modules
import requests
import sys
from tabulate import tabulate
from art import line

class NsxAlbHttpPolicySet:
    def __init__(self, url, headers):
        self._url = url + "/api/httppolicyset"
        self._headers = headers

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
            print(f"Unable to scan HTTP Policy Sets ({response.status_code})\n")
            #Print the error details in table using tabulate function
            print(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
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
                print(f"\nThe below HTTP Policy Sets have content switching rules with pools / poolgroups defined\n")
                print(tabulate(list(map(list, self._dict_vs_httppolicy_having_pools.items())), headers=["Virtual Service", "HTTP Policy Set"], showindex=True, tablefmt="fancy_grid"))
                print(f"\nThe below Pools / PoolGroups are discovered in content switching rules and will be migrated in subsequent workflows:\n")
                print(tabulate(self._list_httppolicysetname_poolname_vsname, headers=["Pool / Pool_Group", "HTTP Policy Set", "Virtual Service"], showindex=True, tablefmt="fancy_grid"))
            else:
                print("\nSuccessfully scanned the HTTP Policy Sets of selected virtual services for migration and no content switching pools or pool groups found:")
        else:
            self.dict_cs_originalpool_url_name = {}
            self.dict_cs_originalpoolgroup_url_name = {}

    def create_httppolicyset(self, body):
        ''' Class Method to create an HTTPPolicySet in the specified Tenant'''
        response = requests.post(self._url, json=body, headers=self._headers, verify=False)
        if response:
            print(f"\nHTTP Policy Set '{response.json()['name']}' successfully created ({response.status_code})")
        else:
            print(f"\nHTTP Policy Set '{body['name']}' creation failed ({response.status_code})\n")
            print(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            print("\nExiting, Please cleanup any objects that are created, fix the error and re-run the migrator \n")
            sys.exit()
        return response.json()
    
    def migrate_httppolicyset(self, dict_cs_originalpoolurl_migratedpoolurl, dict_cs_originalpoolgroupurl_migratedpoolgroupurl, suffix_tag):
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
                    httppolicyset["name"] = httppolicyset["name"] + "-" + suffix_tag
                    migrated_httppolicyset = self.create_httppolicyset(httppolicyset)
                    migrated_httppolicyset_url = self._url + "/" + migrated_httppolicyset["uuid"]
                    self.dict_vs_httppolicysetmigratedurl[vs_selected] = migrated_httppolicyset_url
                    self._dict_httppolicysetmigrated_name_url[migrated_httppolicyset["name"]] = migrated_httppolicyset_url
        if len(self._dict_httppolicysetmigrated_name_url) != 0:
            print("\nThe below HTTP Policy Sets are migrated successfully\n")
            print(tabulate(list(map(list, self._dict_httppolicysetmigrated_name_url.items())), headers=["HTTPPolicySet_Name", "HTTPPolicySet_Ref"], showindex=True, tablefmt="fancy_grid"))



    









