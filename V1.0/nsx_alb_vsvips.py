#Import modules
import requests
import sys
from tabulate import tabulate

class NsxAlbVsVip:
    def __init__(self, url, headers):
        self._url = url + "/api/vsvip"
        self._headers = headers

    #Class Method to get the list of all VS Vips and to handle API Pagination
    def get_vsvip(self):
        ''' Class Method to fetch the list of all VS VIPs in the Tenant'''
        self._list_vsvips = []
        self.dict_vsvip_url_name = {}
        new_results = True
        page = 1
        while new_results: 
            response = requests.get(self._url + f"?page={page}", headers=self._headers, verify=False)
            response_body = response.json()
            new_results = response_body.get("results", []) #Returns False if "results" not found
            for vsvip in new_results:
                if vsvip != []:
                    self._list_vsvips.append(vsvip)
                    self.dict_vsvip_url_name[vsvip["url"]] = vsvip["name"]
            page += 1
        if (len(self.dict_vsvip_url_name) == 0) and (response == False): #Handle a scenario where there are no VS VIPs in NSX ALB tenant
            print(f"\nList NSX ALB VS VIPs Unsuccessful ({response.status_code})\n")
            print(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            sys.exit()

    def set_vsvip(self, dict_selectedvs_originalvsvipname):
        '''Class method to get the original VS VIP ref and name in required dict format for migration'''
        self.get_vsvip() #get_vsvip method is a pre-requisite for calling set_vsvip method
        self.dict_selectedvsvip_url_name = {}
        if len(dict_selectedvs_originalvsvipname) != 0:
            for selectedvs, selectedvs_vsvipname in list(dict_selectedvs_originalvsvipname.items()):
                for vsvip_url, vsvip_name in list(self.dict_vsvip_url_name.items()):
                    if selectedvs_vsvipname == vsvip_name:
                        self.dict_selectedvsvip_url_name[vsvip_url] = vsvip_name
        else:
            self.dict_selectedvsvip_url_name = {}

    def create_vsvip(self, body):
        ''' Class Method to create NSX ALB VS VIPs in the Tenant on the selected Cloud Account'''
        response = requests.post(self._url, json=body, headers=self._headers, verify=False )
        if response:
            print(f"\nVS-VIP '{response.json()['name']}' successfully created ({response.status_code})\n")
        else:
            print(f"\nVS-VIP '{body['name']}' creation Failed ({response.status_code})\n")
            print(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            print("\nExiting, Please cleanup any objects that are created, fix the error and re-run the migrator \n")
            sys.exit()
        return response.json()
    
    def migrate_vsvip(self, target_cloud_url, target_vrfcontext_url, target_vrfcontext_tier1path, suffix_tag):
        ''' Class Method to migrate VS VIPs to target cloud account '''
        self._dict_vsvipmigrated_name_url = {}
        self.dict_originalvsvipurl_migratedvsvipurl = {}
        for selectedvsvip_url, selectedvsvip_name in list(self.dict_selectedvsvip_url_name.items()):
            for vsvip in self._list_vsvips:
                if selectedvsvip_name == vsvip["name"]:
                    del vsvip["uuid"]
                    del vsvip["url"]
                    del vsvip["_last_modified"]
                    if "tier1_lr" in vsvip:
                        del vsvip["tier1_lr"]
                    vsvip["cloud_ref"] = target_cloud_url
                    vsvip["vrf_context_ref"] = target_vrfcontext_url
                    if target_vrfcontext_tier1path != "":
                        vsvip["tier1_lr"] = target_vrfcontext_tier1path                    
                    for item in vsvip["vip"]:
                        if "discovered_networks" in item.keys():
                            del item["discovered_networks"]
                        if "placement_networks" in item.keys():
                            del item["placement_networks"]
                    vsvip["name"] = vsvip["name"] + "-" + suffix_tag
                    migrated_vsvip = self.create_vsvip(vsvip)
                    migrated_vsvip_url = self._url + "/" + migrated_vsvip["uuid"]
                    self._dict_vsvipmigrated_name_url[migrated_vsvip["name"]] = migrated_vsvip_url
                    self.dict_originalvsvipurl_migratedvsvipurl[selectedvsvip_url] = migrated_vsvip_url
        if len(self._dict_vsvipmigrated_name_url) != 0:
            print("\nThe below VS-VIPs are migrated successfully\n")
            print(tabulate(list(map(list, self._dict_vsvipmigrated_name_url.items())), headers=["VS-VIP_Name", "VS-VIP_Ref"], showindex=True, tablefmt="fancy_grid"))