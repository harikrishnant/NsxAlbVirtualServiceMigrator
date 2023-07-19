#Import modules
import requests
import sys
from tabulate import tabulate

class NsxAlbCloud:
    def __init__(self, url, headers, run_id):
        self._url = url + "/api/cloud"
        self._headers = headers
        self._run_id = run_id

    def print_func(self, item):
        print(item)                
        with open(f"./logs/run-{self._run_id}.log", "a", encoding="utf-8") as outfile:
            print(item, file=outfile)

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
            self.print_func(f"\nFound {len(self._list_clouds)} NSX ALB Cloud Accounts under the Tenant - {self._headers['X-Avi-Tenant']}")
            self.print_func(f"\nCloud details below:\n")
            self.print_func(tabulate(list(map(list, self.dict_cloud_url_name.items())), headers=["Cloud_Ref", "Name"], showindex=True, tablefmt="fancy_grid"))
        else:
            self.print_func(f"\nList NSX ALB Cloud Accounts Unsuccessful ({response.status_code})\n")
            #Print the error details in table using tabulate function
            self.print_func(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            sys.exit()
 
    def set_cloud(self, target_cloud_name, dict_dnsproviderprofile_url_name, dict_ipamproviderprofile_url_name):
        ''' Class Method to set the destination cloud account to migrate virtual services to '''
        self.get_cloud() #get_cloud() method is a pre-requisite to run the set_cloud() method
        self.target_cloud_name = target_cloud_name
        self.target_cloud_url = "" # Use this Cloud URL to migrate to #
        if self.target_cloud_name in list(self.dict_cloud_url_name.values()):    
            for cloud in self._list_clouds:
                if cloud.get("name") == self.target_cloud_name:
                    self.target_cloud_url = cloud.get("url")
                    self.target_cloud_dnsprofile_url = cloud.get("dns_provider_ref", "")
                    self.target_cloud_ipamprofile_url = cloud.get("ipam_provider_ref", "")
                    if self.target_cloud_dnsprofile_url:
                        for dnsprofile_url,dnsprofile_name in dict_dnsproviderprofile_url_name.items():
                            if dnsprofile_url == self.target_cloud_dnsprofile_url:
                                self.target_cloud_dnsprofile_name = dnsprofile_name
                    else:
                        self.target_cloud_dnsprofile_name = "NONE"
                    if self.target_cloud_ipamprofile_url:
                        for ipamprofile_url,ipamprofile_name in dict_ipamproviderprofile_url_name.items():
                            if ipamprofile_url == self.target_cloud_ipamprofile_url:
                                self.target_cloud_ipamprofile_name = ipamprofile_name
                    else:
                        self.target_cloud_ipamprofile_name = "NONE"
        else:
            self.print_func("\n")
            self.print_func(tabulate([[f"Cloud Account '{self.target_cloud_name}' not found", "Please select the correct cloud account from the table above"]], ["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            sys.exit()
        self.print_func(f"\nYou selected '{self.target_cloud_name}' Cloud Account\n")
        self.print_func(tabulate([[self.target_cloud_name, self.target_cloud_url, self.target_cloud_dnsprofile_name, self.target_cloud_ipamprofile_name]], ["Name", "Cloud_Ref", "DNS Profile", "IPAM_Profile"], showindex=True, tablefmt="fancy_grid"))
