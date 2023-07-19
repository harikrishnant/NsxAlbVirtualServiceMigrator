''' Class for NSX ALB IPAM Profile '''
#import modules
import requests
import sys
from tabulate import tabulate

class NsxAlbIpamProfile:
    def __init__(self, url, headers, run_id):
        self._url1 = url + "/api/ipamdnsproviderprofile"
        self._url2 = url + "/api/network"
        self._headers = headers
        self._run_id = run_id
    
    def print_func(self, item):
        print(item)                
        with open(f"./logs/run-{self._run_id}.log", "a", encoding="utf-8") as outfile:
            print(item, file=outfile)
    
    def get_network(self):
        ''' Class Method to get the list of Networks and to handle API Pagination '''
        self._list_networks = []
        self.dict_network_url_name = {}        
        new_results = True
        page = 1
        while new_results:
            response = requests.get(self._url2 + f"?page={page}", headers=self._headers, verify=False)
            response_body = response.json()
            new_results = response_body.get("results", []) #Returns False if "results" not found
            for network in new_results:
                if network != []:
                    self._list_networks.append(network)
                    self.dict_network_url_name.update({
                        network.get("url") : network.get("name")
                    })
            page +=1 

    def get_ipamprofile(self):
        ''' Class Method to get the list of IPAM Profiles and to handle API Pagination '''
        self._list_ipamprofile = []
        self.dict_ipamprofile_url_name = {}
        new_results = True
        page = 1
        while new_results:
            response = requests.get(self._url1 + f"?page={page}", headers=self._headers, verify=False)
            response_body = response.json()
            new_results = response_body.get("results", []) #Returns False if "results" not found
            for ipamprofile in new_results:
                if ipamprofile != []:
                    if ipamprofile.get("type", {}) == "IPAMDNS_TYPE_INTERNAL":
                        self._list_ipamprofile.append(ipamprofile)
                        self.dict_ipamprofile_url_name.update(
                            {
                                ipamprofile.get("url") : ipamprofile.get("name")
                            }
                    )
            page += 1

    def scan_ipamprofile(self, target_cloud_ipamprofile_url, target_ipam_network, target_ipam_subnet, list_vrfcontexts, target_vrf_name):
        ipam_profile_name = ""
        self.dict_network_subnet = {}
        if target_cloud_ipamprofile_url:
            for each_ipamprofile in self._list_ipamprofile:
                if each_ipamprofile.get("url") == target_cloud_ipamprofile_url:
                    ipam_profile_name = each_ipamprofile.get("name")
                    list_usable_networks = each_ipamprofile.get("internal_profile", {}).get("usable_networks", [])
                    if list_usable_networks:
                        for each_vip_network in list_usable_networks:
                            for each_network in self._list_networks:
                                if each_network.get("url") == each_vip_network.get("nw_ref", ""):
                                    configured_subnets = each_network.get("configured_subnets", [])
                                    list_subnet = []
                                    for each_vrf in list_vrfcontexts:
                                        if each_vrf.get("url") == each_network.get("vrf_context_ref", ""):
                                            vrf_name = each_vrf.get("name")
                                    if configured_subnets:
                                        for each_subnet in configured_subnets:
                                            subnet_host = each_subnet.get("prefix", {}).get("ip_addr", {}).get("addr", "")
                                            subnet_mask = str(each_subnet.get("prefix", {}).get("mask", "")) if each_subnet.get("prefix", {}) and each_subnet.get("prefix", {}).get("mask", "") else ""
                                            subnet = subnet_host + "/" + subnet_mask
                                            list_subnet.append(subnet)
                                        self.dict_network_subnet.update(
                                            {
                                                each_network.get("name") : [list_subnet, vrf_name]
                                            }
                                        )
                                    else:
                                        self.dict_network_subnet.update(
                                            {
                                                each_network.get("name") : [["NO SUBNET"], vrf_name]
                                            }
                                        )                               
                    else:
                        self.print_func(f"\nWARNING: IPAM profile in Target Cloud account doesn't have valid networks associated. Tool will now Exit\n")
                        self.print_func(tabulate([["IPAM Networks missing", "IPAM Profile is missing VIP networks. Please check IPAM profile settings"]], ["Error", "Description"], showindex=True, tablefmt="fancy_grid"))
                        sys.exit()
            #Flatten for Tabulate view
            list_ipam_network_subnet_vrf = []
            for network, subnet_vrf in self.dict_network_subnet.items():
                list_ipam_network_subnet_vrf.append([ipam_profile_name, network, ("\n").join(subnet_vrf[0]), subnet_vrf[1]])
        else:
            self.print_func(f"\nWARNING: Target Cloud account doesn't have IPAM profile attached. Tool will now Exit \n")
            self.print_func(tabulate([["IPAM profile missing", "Target Cloud connector doesn't have IPAM profile attached"]], ["Error", "Description"], showindex=True, tablefmt="fancy_grid"))
            sys.exit()

        if self.dict_network_subnet:
            self.print_func(f"\nFound {len(self.dict_network_subnet)} networks under the IPAM Profile \"{ipam_profile_name}\". Details below: \n")
            self.print_func(tabulate(list_ipam_network_subnet_vrf, ["IPAM", "Networks", "Subnets", "VRF_Context"], showindex=True, tablefmt="fancy_grid"))

        #Validate supplied IPAM settings
        if target_ipam_network not in self.dict_network_subnet.keys():
            self.print_func(f"\nERROR: Selected IPAM Network '{target_ipam_network}' not found in Cloud Connector\n")
            self.print_func(tabulate([["IPAM Network not found", f"Selected IPAM Network '{target_ipam_network}' is missing in IPAM Profile"]], ["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            sys.exit()
        if target_ipam_subnet not in self.dict_network_subnet.get(target_ipam_network, "")[0]:
            self.print_func(f"\nERROR: Selected IPAM Subnet '{target_ipam_subnet}' not found in IPAM Network '{target_ipam_network}'\n")
            self.print_func(tabulate([["IPAM Subnet not found", f"Selected IPAM Subnet '{target_ipam_subnet}' is missing in IPAM Network '{target_ipam_network}'"]], ["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            sys.exit()
        if target_vrf_name != self.dict_network_subnet.get(target_ipam_network, "")[1]:
            prompt = input(f"\nWARNING : IPAM Network '{target_ipam_network}' doesn't belong to the supplied target VRF Context '{target_vrf_name}'. Proceed? Y/N? ").lower()
            if prompt != "y":
                print(tabulate([["VRF Mismatch", "Exiting as per user input"]], ["Error", "Description"], showindex=True, tablefmt="fancy_grid"))
                sys.exit()
        if target_ipam_network in self.dict_network_subnet.keys() and target_ipam_subnet in self.dict_network_subnet.get(target_ipam_network, "")[0]:
            self.print_func(f"\nSuccessfully scanned the supplied IPAM Network and Subnet against Cloud connector and IPAM profile. You are good to proceed:\n")
            self.print_func(tabulate([[f"{target_ipam_network} (IPAM Network)", "SUCCESS"], [f"{target_ipam_subnet} (IPAM Subnet)", "SUCCESS"]], ["Item", "Status"], showindex=True, tablefmt="fancy_grid"))
    
    def create_ipam_block(self, target_ipam_network, target_ipam_subnet):
        if not target_ipam_network and not target_ipam_subnet:
            return {}
        else:
            self._target_ipam_network = target_ipam_network
            self._target_ipam_subnet = target_ipam_subnet
            for net_url, net_name in self.dict_network_url_name.items():
                    if net_name == self._target_ipam_network:
                        self.target_ipam_network_url = net_url        
            ipam_network_subnet = {
                    "network_ref": self.target_ipam_network_url,
                    "subnet": {
                        "ip_addr": {
                            "addr": self._target_ipam_subnet[:self._target_ipam_subnet.find("/")],
                            "type": "V4"
                        },
                        "mask": self._target_ipam_subnet[self._target_ipam_subnet.find("/") + 1:]
                    }
            }
            return ipam_network_subnet


                


    