#Import modules
import requests
import sys
from tabulate import tabulate

#Class for the login object
class NsxAlbLogin:
    def __init__(self, url, creds, headers):
        self._url = url + "/login"
        self._credentials = creds
        self._headers = headers

    def get_cookie(self):
        ''' Method to Login to NSX ALB controller and return the CSRFToken and Cookie '''
        print(f"\nLogging to NSX ALB Controller at {self._url}")
        try:
            response = requests.post(self._url, json=self._credentials, headers=self._headers, verify=False)
        except requests.exceptions.RequestException as exception:
            print("\n")
            print(tabulate([["NSX ALB Controller not reachable", exception]], headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            sys.exit()
        if response:
            self.csrf_token = response.cookies["csrftoken"]
            self._avi_sessionid = response.cookies["avi-sessionid"]
            self.cookie = "avi-sessionid=" + self._avi_sessionid + ";" + " " + "csrftoken=" + self.csrf_token + ";" + " " + "sessionid=" + self._avi_sessionid
        else:
            print(f"\n\nAuthentication Failure ({response.status_code})\n")
            print(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            sys.exit()
