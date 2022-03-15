#Import modules
import requests
import sys
from tabulate import tabulate

#Class for the Tenant object
class NsxAlbTenant():
    def __init__(self, url, headers):
        self._url = url + "/api/tenant"
        self._headers = headers

    def get_tenant(self): #Class Method to get the list of all Tenants and to handle API Pagination
        self._list_tenants = []
        new_results = True
        page = 1
        while new_results:
            response = requests.get(self._url + f"?page={page}", headers=self._headers, verify=False)
            response_body = response.json()
            new_results = response_body.get("results", []) #Returns False if "results" not found
            for tenant in new_results:
                if tenant != []:
                    self._list_tenants.append(tenant)
            page += 1
        if len(self._list_tenants) != 0:
            print(f"\nYou are successfully authenticated against Tenant - {self._headers['X-Avi-Tenant']}\n")
        else:
            print(f"\nLogin Failed ({response.status_code})\n")
            #Print the error details in table using tabulate function
            print(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            sys.exit()