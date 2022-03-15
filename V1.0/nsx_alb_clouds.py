#Import modules
import requests
import sys
from tabulate import tabulate

class NsxAlbCloud:
    def __init__(self, url, headers):
        self._url = url + "/api/cloud"
        self._headers = headers

    def get_cloud(self): 
        ''' Class Method to get the list of all Cloud Accounts and to handle API Pagination '''
        self._list_clouds = []
        self.dict_cloud_url_name = {}
        new_results = True
        page = 1
        while new_results:
            response = requests.get(self._url + f"?page={page}", headers=self._headers, verify=False)
            response_body = response.json()
            new_results = response_body.get("results", []) #Returns False if "results" not found
            for cloud in new_results:
                if cloud != []:
                    self._list_clouds.append(cloud)
                    self.dict_cloud_url_name[cloud["url"]] = cloud["name"]
            page += 1
        if len(self._list_clouds) != 0:
            print(f"\nFound {len(self._list_clouds)} NSX ALB Cloud Accounts under the Tenant - {self._headers['X-Avi-Tenant']}")
            print(f"\nCloud details below:\n")
            print(tabulate(list(map(list, self.dict_cloud_url_name.items())), headers=["Cloud_Ref", "Name"], showindex=True, tablefmt="fancy_grid"))
        else:
            print(f"\nList NSX ALB Cloud Accounts Unsuccessful ({response.status_code})\n")
            #Print the error details in table using tabulate function
            print(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            sys.exit()
 
    def set_cloud(self):
        ''' Class Method to set the destination cloud account to migrate virtual services to '''
        self.get_cloud() #get_cloud() method is a pre-requisite to run the set_cloud() method
        self.target_cloud_name = input(f"\nEnter the Destination NSX ALB Cloud Account to migrate applications to (Enter Name without quotes) - ")
        self.target_cloud_url = "" # Use this Cloud URL to migrate to #
        if self.target_cloud_name in list(self.dict_cloud_url_name.values()):    
            for url,name in self.dict_cloud_url_name.items():
                if name == self.target_cloud_name:
                    self.target_cloud_url = url
        else:
            print("\n")
            print(tabulate([[f"Cloud Account '{self.target_cloud_name}' not found", "Please select the correct cloud account from the table above"]], ["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            sys.exit()
        print(f"\nYou selected '{self.target_cloud_name}' Cloud Account\n")
        print(tabulate([[self.target_cloud_name, self.target_cloud_url]], ["Name", "Cloud_Ref"], showindex=True, tablefmt="fancy_grid"))