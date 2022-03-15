#Import Modules
import requests
import sys
from tabulate import tabulate

#Class for the Pool Group object
class NsxAlbPoolGroup:
    def __init__(self, url, headers):
        self._url = url + "/api/poolgroup"
        self._headers = headers

    #Class Method to get the list of all Pools Groups and to handle API Pagination
    def get_poolgroup(self):
        ''' Class Method to fetch the list of all pools groups in the Tenant'''
        self._list_poolgroups = []
        self.dict_poolgroup_url_name = {}
        new_results = True
        page = 1
        while new_results:
            response = requests.get(self._url + f"?page={page}", headers=self._headers, verify=False)
            response_body = response.json()
            new_results = response_body.get("results", [])#Returns False if "results" not found
            for poolgroup in new_results:
                if poolgroup != []:
                    self._list_poolgroups.append(poolgroup)
                    self.dict_poolgroup_url_name[poolgroup["url"]] = poolgroup["name"]
            page += 1
        if (len(self.dict_poolgroup_url_name) == 0) and (response == False): #Handle a scenario where there are no pool groups in NSX ALB tenant
            print(f"List NSX ALB Pool Groups Unsuccessful ({response.status_code})\n")
            print(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            sys.exit()

    def set_poolgroup(self, dict_selectedvs_originalpoolgroupname):
        '''Class method to get the original pool group ref and name in required dict format for migration'''
        self.get_poolgroup() #get_pool method is a pre-requisite for calling set_pool method
        self.dict_selectedpoolgroup_url_name = {}
        if len(dict_selectedvs_originalpoolgroupname) != 0:
            for selectedvs, selectedvs_poolgroupname in list(dict_selectedvs_originalpoolgroupname.items()):
                for poolgroup_url, poolgroup_name in list(self.dict_poolgroup_url_name.items()):
                    if selectedvs_poolgroupname == poolgroup_name:
                        self.dict_selectedpoolgroup_url_name[poolgroup_url] = poolgroup_name
        else:
            self.dict_selectedpoolgroup_url_name = {}

    def get_poolgroup_member(self, dict_poolgroup_url_name, dict_pool_url_name):    
        self.dict_poolgroupmembers_url_name = {}
        self._list_poolname_poolgroupname = []
        if len(dict_poolgroup_url_name) != 0:
            for url,name in list(dict_poolgroup_url_name.items()):
                for poolgroup in self._list_poolgroups:
                    if name == poolgroup["name"]:
                        if "members" in poolgroup.keys():
                            for member in poolgroup["members"]:
                                for pool_url,pool_name in list(dict_pool_url_name.items()):
                                    if member["pool_ref"] == pool_url:
                                        self.dict_poolgroupmembers_url_name[pool_url] = dict_pool_url_name[pool_url]
                                        self._list_poolname_poolgroupname.append([dict_pool_url_name[pool_url], poolgroup["name"]])
            if len(self._list_poolname_poolgroupname) != 0:
                print(f"\nSelected Pool Groups has the below pools as members which will be migrated next:\n")
                print(tabulate(self._list_poolname_poolgroupname, headers=["Pool", "Pool_Group"], showindex=True, tablefmt="fancy_grid"))
            else:
                print("\nSuccessfully scanned the Pool Groups and no pool members found\n")
        else:
            self.dict_poolgroupmembers_url_name = {}

    def create_poolgroup(self, body):
        ''' Class Method to create NSX ALB Pool Groups in the Tenant on the selected Cloud Account'''
        response = requests.post(self._url, json=body, headers=self._headers, verify=False )
        if response:
            print(f"\nPool Group '{response.json()['name']}' successfully created ({response.status_code})\n")
        else:
            print(f"\nPool Group'{body['name']}' creation Failed ({response.status_code})\n")
            print(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            print("\nExiting, Please cleanup any objects that are created, fix the error and re-run the migrator \n")
            sys.exit()
        return response.json()   

    def migrate_poolgroup(self, dict_poolgroup2migrate_url_name, dict_originalpoolurl_migratedpoolurl, target_cloud_url, suffix_tag):   
        '''Class Method to migrate pool groups from one NSX ALB cloud to another in the same Tenant''' 
        self.get_poolgroup() #get_poolgroup method is a pre-requisite for calling migrate_poolgroup method
        self.dict_originalpoolgroupurl_migratedpoolgroupurl = {}
        self._dict_migratedpoolgroup_name_url = {}
        self._dict_previously_migrated_poolgroup_oldname_newname = {}
        if len(dict_poolgroup2migrate_url_name) != 0:
            for poolgroup_url, poolgroup_name in list(dict_poolgroup2migrate_url_name.items()):
                if not (poolgroup_name + "-" + suffix_tag) in list(self.dict_poolgroup_url_name.values()): #Checking if the pools to migrate were previously migrated For eg, as part of content switching policies            for poolgroup in self.list_poolgroups:
                    for poolgroup in self._list_poolgroups:
                        if poolgroup_name == poolgroup["name"]:
                            del poolgroup["url"]
                            del poolgroup["uuid"]
                            del poolgroup["_last_modified"]
                            poolgroup["name"] = poolgroup["name"] + "-" + suffix_tag
                            poolgroup["cloud_ref"] = target_cloud_url
                            if "members" in list(poolgroup.keys()):
                                for member in poolgroup["members"]:
                                    for originalpoolurl, migratedpoolurl in list(dict_originalpoolurl_migratedpoolurl.items()):
                                        if member["pool_ref"] == originalpoolurl:
                                            member["pool_ref"] = migratedpoolurl
                            migrated_poolgroup = self.create_poolgroup(poolgroup)
                            migrated_poolgroup_url = self._url + "/" + migrated_poolgroup["uuid"]
                            self.dict_originalpoolgroupurl_migratedpoolgroupurl[poolgroup_url] = migrated_poolgroup_url
                            self._dict_migratedpoolgroup_name_url[migrated_poolgroup["name"]] = migrated_poolgroup_url
                else:
                    self._dict_previously_migrated_poolgroup_oldname_newname[poolgroup_name] = poolgroup_name + "-" + suffix_tag
                    for url, name in list(self.dict_poolgroup_url_name.items()):
                        if (poolgroup_name + "-" + suffix_tag) == name:
                            self.dict_originalpoolgroupurl_migratedpoolgroupurl[poolgroup_url] = url
        else:
            self.dict_originalpoolgroupurl_migratedpoolgroupurl = {}
        if len(self._dict_migratedpoolgroup_name_url) != 0:
            print(f"\nThe below Pool Groups are migrated successfully to the new cloud account\n")
            print(tabulate(list(map(list, self._dict_migratedpoolgroup_name_url.items())), headers=["Migrated_PoolGroup", "Migrated_PoolGroup_Ref"], showindex=True, tablefmt="fancy_grid"))
        if len(self._dict_previously_migrated_poolgroup_oldname_newname) != 0:
            print(f"\nThe below Pool Groups were previously migrated successfully as part of a different workflow (Eg: Content switching policies) and hence not re-attempted\n")
            print(tabulate(list(map(list, self._dict_previously_migrated_poolgroup_oldname_newname.items())), headers=["Original_PoolGroup", "Migrated_PoolGroup"], showindex=True, tablefmt="fancy_grid"))
    


