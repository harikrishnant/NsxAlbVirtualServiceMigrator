#Import modules
import requests
import sys
from tabulate import tabulate

#Class for the logout object
class NsxAlbLogout():
    def __init__(self, url, headers, run_id):
        self._url = url + "/logout"
        self._headers = headers
        self._run_id = run_id

    def print_func(self, item):
        print(item)                
        with open(f"./logs/run-{self._run_id}.log", "a", encoding="utf-8") as outfile:
            print(item, file=outfile)

    def end_session(self):
        ''' Method to Logout from NSX ALB controller '''
        response = requests.post(self._url, headers=self._headers, verify=False)
        if response:
            self.print_func(f"\nSuccessfully logged out from NSX ALB controller ({response.status_code})")
        else:
            self.print_func("Logout unsuccessful, please exit from the terminal")