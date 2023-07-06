#import modules
import requests
import sys
from tabulate import tabulate

class NsxAlbDnsProfile:
    def __init__(self, url, headers, run_id):
        self._url = url + "/api/ipamdnsproviderprofile"
        self._headers = headers
        self._run_id = run_id
    
    def print_func(self, item):
        print(item)                
        with open(f"./logs/run-{self._run_id}.log", "a", encoding="utf-8") as outfile:
            print(item, file=outfile)
    
    def get_dnsprofile(self):
        ''' Class Method to get the list of DNS Profiles and to handle API Pagination '''
        self._list_dnsprofile = []
        self.dict_dnsprofile_url_name = {}
        new_results = True
        page = 1
        while new_results:
            response = requests.get(self._url + f"?page={page}", headers=self._headers, verify=False)
            response_body = response.json()
            new_results = response_body.get("results", []) #Returns False if "results" not found
            for dnsprofile in new_results:
                if dnsprofile != []:
                    if dnsprofile.get("type", {}) == "IPAMDNS_TYPE_INTERNAL_DNS":
                        self._list_dnsprofile.append(dnsprofile)
                        self.dict_dnsprofile_url_name.update(
                            {
                                dnsprofile.get("url") : dnsprofile.get("name")
                            }
                    )
            page += 1

    def scan_dnsprofile(self, target_cloud_dnsprofile_url, selected_dns_domain=[]):
        self.list_domains_selecteddnsprofile = []
        self._domainmapping_dnsprofile = []
        self._selecteddnsprofile_name = ""
        for dnsprofile in self._list_dnsprofile:
            if dnsprofile.get("url") == target_cloud_dnsprofile_url:
                self._selecteddnsprofile_name = dnsprofile.get("name")
                dns_domain = dnsprofile.get("internal_profile", {}).get("dns_service_domain", [])
                for each in dns_domain:
                    self.list_domains_selecteddnsprofile.append(each.get("domain_name"))
                    self._domainmapping_dnsprofile.append([each.get("domain_name"), self._selecteddnsprofile_name])
        if self._domainmapping_dnsprofile:
            self.print_func(f"\nFound {len(self.list_domains_selecteddnsprofile)} domains under the DNS Profile \"{self._selecteddnsprofile_name}\". Details below: \n")
            self.print_func(tabulate(self._domainmapping_dnsprofile, ["Domain", "DNS Profile"], showindex=True, tablefmt="fancy_grid"))
        else:
            self.print_func(f"\nDNS Profile in Cloud Connector doesn't have DNS domains associated. Tool will now Exit \n") 
            self.print_func(tabulate([["No DNS domains found", "Check the DNS profile / Cloud connector settings"]], ["Error", "Description"], showindex=True, tablefmt="fancy_grid"))             
            sys.exit()

        #Scan supplied DNS domains with the domains associated with cloud account and validate
        list_incorrect_selected_domain = []
        list_domain_select_status = []
        for each_selected_domain in selected_dns_domain:
            if each_selected_domain in self.list_domains_selecteddnsprofile:
                list_domain_select_status.append([each_selected_domain, "AVAILABLE in Cloud"])
            else:
                list_domain_select_status.append([each_selected_domain, "UNAVAILABLE in Cloud"])
                list_incorrect_selected_domain.append(each_selected_domain)
        if list_incorrect_selected_domain:
            self.print_func(f"\n{len(list_incorrect_selected_domain)} DNS domains supplied as arguments are not available in Cloud connector, details below: Tool will now exit.\n")
            self.print_func(tabulate(list_domain_select_status, ["DNS Domain", "Status"], showindex=True, tablefmt="fancy_grid"))
            sys.exit()
        else:
            self.print_func(f"\nSuccessfully scanned the {len(selected_dns_domain)} supplied DNS domains against Cloud connector. You are good to proceed:\n")
            self.print_func(tabulate(list_domain_select_status, ["DNS Domain", "Status"], showindex=True, tablefmt="fancy_grid"))
            


