#Import modules
import requests
import sys
from tabulate import tabulate
from art import line

class NsxAlbVrfContext:
    def __init__(self, url, headers, target_cloud_url, target_cloud_name, run_id):
        self._url = url + "/api/vrfcontext"
        self._headers = headers
        self._target_cloud_url = target_cloud_url
        self._target_cloud_name = target_cloud_name
        self._run_id = run_id

    def print_func(self, item):
        print(item)                
        with open(f"./logs/run-{self._run_id}.log", "a", encoding="utf-8") as outfile:
            print(item, file=outfile)

    def get_vrfcontext(self): 
        ''' Class Method to get the list of all VRF Contexts under the selected Cloud Account and to handle API Pagination '''
        self.list_vrfcontexts = []
        self._dict_vrfcontext_url_name = {}
        new_results = True
        page = 1
        while new_results:
            response = requests.get(self._url + f"?page={page}", headers=self._headers, verify=False)
            response_body = response.json()
            new_results = response_body.get("results", []) #Returns False if "results" not found
            for vrfcontext in new_results:
                if vrfcontext != []:
                    if (vrfcontext["cloud_ref"] == self._target_cloud_url) and (vrfcontext["name"] != "management"):
                        self._dict_vrfcontext_url_name[vrfcontext["url"]] = vrfcontext["name"]
                        self.list_vrfcontexts.append(vrfcontext)
            page += 1
        if len(self._dict_vrfcontext_url_name) != 0:
            self.print_func(f"\nFound {len(self._dict_vrfcontext_url_name)} VRF Contexts under the target cloud account '{self._target_cloud_name}' for tenant - {self._headers['X-Avi-Tenant']}")
            self.print_func(f"\nVRF Context details below:\n")
            self.print_func(tabulate(list(map(list, self._dict_vrfcontext_url_name.items())), headers=["VRFContext_Ref", "Name"], showindex=True, tablefmt="fancy_grid"))
        else:
            self.print_func(f"\nList VRF Contexts Unsuccessful ({response.status_code})\n")
            self.print_func(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            sys.exit()

    def set_vrfcontext(self, target_vrfcontext_name):
        ''' Class Method to set the destination VRF Context for the selected cloud account '''
        self.get_vrfcontext() #get_vrfcontext() method is a pre-requisite to run the set_vrfcontext() method
        self._target_vrfcontext_name = target_vrfcontext_name
        self.target_vrfcontext_url = "" # Use this VRF Context to migrate to #
        self.target_vrfcontext_tier1path = ""
        if self._target_vrfcontext_name in list(self._dict_vrfcontext_url_name.values()):    
            for vrfcontext in self.list_vrfcontexts:
                if self._target_vrfcontext_name == vrfcontext["name"]:
                    self.target_vrfcontext_url = vrfcontext["url"]
                    if "attrs" in list(vrfcontext.keys()): #For supporting NSX-T T1 Gateways
                        for attr in vrfcontext["attrs"]:
                            if "tier1path" in list(attr.values()):
                                self.target_vrfcontext_tier1path = attr["value"]
        else:
            self.print_func("\n")
            self.print_func(tabulate([[f"VRF Context '{self._target_vrfcontext_name}' not found", "Select the correct VRF Context from the table above"]], ["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            sys.exit()
        self.print_func(f"\nYou selected VRF Context '{self._target_vrfcontext_name}'\n")
        self.print_func(tabulate([[self._target_vrfcontext_name, self.target_vrfcontext_url]], ["Name", "VRFContext_Ref"], showindex=True, tablefmt="fancy_grid"))
        if self.target_vrfcontext_tier1path != "":
            self.print_func(f"\nNSX-T Tier1 Gateway associated with selected VRF Context is '{self.target_vrfcontext_tier1path}'\n")