#Import modules
import requests
import sys
from tabulate import tabulate
from art import line

class NsxAlbSeGroup:
    def __init__(self, url, headers, target_cloud_url, target_cloud_name):
        self._url = url + "/api/serviceenginegroup"
        self._headers = headers
        self._target_cloud_url = target_cloud_url
        self._target_cloud_name = target_cloud_name

    def get_segroup(self): 
        ''' Class Method to get the list of all Service Engine Groups under the selected Cloud Account and to handle API Pagination '''
        self._dict_segroup_url_name = {}
        new_results = True
        page = 1
        while new_results:
            response = requests.get(self._url + f"?page={page}", headers=self._headers, verify=False)
            response_body = response.json()
            new_results = response_body.get("results", []) #Returns False if "results" not found
            for segroup in new_results:
                if segroup != []:
                    if segroup["cloud_ref"] == self._target_cloud_url:
                        self._dict_segroup_url_name[segroup["url"]] = segroup["name"]
            page += 1
        if len(self._dict_segroup_url_name) != 0:
            print(f"\nFound {len(self._dict_segroup_url_name)} Service Engine Groups under the target cloud account '{self._target_cloud_name}' for tenant - {self._headers['X-Avi-Tenant']}")
            print(f"\nService Engine Group details below:\n")
            print(tabulate(list(map(list, self._dict_segroup_url_name.items())), headers=["SEGroup_Ref", "Name"], showindex=True, tablefmt="fancy_grid"))
        else:
            print(f"\nList Service Engine Groups Unsuccessful ({response.status_code})\n")
            #Print the error details in table using tabulate function
            print(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            sys.exit()
    
    def set_segroup(self):
        ''' Class Method to set the destination Service Engine Group for the selected cloud account '''
        self.get_segroup() #get_segroup() method is a pre-requisite to run the set_segroup() method
        self._target_segroup_name = input(f"\nEnter the Destination Service Engine Group to migrate applications to (Enter Name without quotes) - ")
        self.target_segroup_url = "" # Use this SE Group to migrate to #
        if self._target_segroup_name in list(self._dict_segroup_url_name.values()):    
            for url,name in self._dict_segroup_url_name.items():
                if name == self._target_segroup_name:
                    self.target_segroup_url = url
        else:
            print("\n")
            print(tabulate([[f"Service Engine Group '{self._target_segroup_name}' not found", "Please select the correct Service Engine Group from the table above"]], ["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            sys.exit()
        print(f"\nYou selected Service Engine Group '{self._target_segroup_name}'\n")
        print(tabulate([[self._target_segroup_name, self.target_segroup_url]], ["Name", "SEGroup_Ref"], showindex=True, tablefmt="fancy_grid"))