#Import modules
import requests
import sys
from tabulate import tabulate

#Class for the logout object
class NsxAlbLogout():
    def __init__(self, url, headers):
        self._url = url + "/logout"
        self._headers = headers

    def end_session(self):
        ''' Method to Logout from NSX ALB controller '''
        response = requests.post(self._url, headers=self._headers, verify=False)
        if response:
            print(f"\nSuccessfully logged out from NSX ALB controller ({response.status_code})")
        else:
            print("Logout unsuccessful, please exit from the terminal")