import sys
import requests
import getopt
import json
from veracode_api_signing.plugin_requests import RequestsAuthPluginVeracodeHMAC

api_base = "https://api.veracode.com/was/configservice/v1/"
headers = {
    "User-Agent": "Dynamic Analysis API Example Client",
    "Content-Type": "application/json"
}


def print_help():
    """Prints command line options and exits"""
    print("""veracode-da-scan-edit.py -s <scan_name> -a <action> [-d]
        Performs action <action> on scan names <scan_name>
""")
    print("Available actions:")
    print(" Start: starts a scan immediately")
    sys.exit()

def find_exact_match(scan_list, scan_name):
    for index in range(len(scan_list)):
        if scan_list[index]["name"] == scan_name:
            return index    
    return -1

def start_scan(scan_name, verbose):
    path = f"https://api.veracode.com/was/configservice/v1/analyses?name={scan_name}"
    response = requests.get(path, auth=RequestsAuthPluginVeracodeHMAC(), headers=headers)
    data = response.json()

    if verbose:
        print(data)

    print(f"Starting scan for {scan_name}")

    if len(data["_embedded"]["analyses"]) > 1:
        print(f"Warning - multiple applications found for {scan_name}")
        print("Looking for exact match: ")
        selectedIndex = find_exact_match(data["_embedded"]["analyses"], scan_name)        
        if selectedIndex < 0:
            print(f"No scan named {scan_name} found.")
            sys.exit(0)
    elif len(data["_embedded"]["analyses"]) == 0:
        print(f"No scan named {scan_name} found.")
        sys.exit(0)
    else:
        print("Scan found")
        selectedIndex = 0        

    matched_scan_name = data["_embedded"]["analyses"][selectedIndex]["name"]
    analysis_id = data["_embedded"]["analyses"][selectedIndex]["analysis_id"]
    
    print(f"Starting Dynamic Analysis with analysis id '{analysis_id}' and scan name '{matched_scan_name}' for search term '{scan_name}'")
                                           
    scan_request = r'''
    {
        "name": "{matched_scan_name}", 
        "schedule": {
            "now": true,
            "duration": {
                "length": 1,
                "unit": "DAY"
            }
        }    
    }'''
    scan_request = scan_request.replace("{matched_scan_name}", matched_scan_name, 1)
    scan_request = scan_request.replace("{analysis_id}", analysis_id, 2)

    if verbose:
        print(scan_request)
    
    scan_path = f"https://api.veracode.com/was/configservice/v1/analyses/{analysis_id}"
    response = requests.put(scan_path, auth=RequestsAuthPluginVeracodeHMAC(), headers=headers, json=json.loads(scan_request))

    if verbose:
        print(f"status code {response.status_code}")
        body = response.json()
        if body:
            print(body)
    if response.status_code == 204:
        print("Successfully started DAST scan.")
    else:
        print(f"Unable to start DAST scan: {response.status_code}")
    

def is_valid_action(action):
    if(action == "START"):
        return True
    return False

def modify_scan(scan_name, action, verbose):
    if(action == "START"):
        start_scan(scan_name, verbose)

def main(argv):
    """Simple command line support for creating, deleting, and listing DA scanner variables"""
    try:
        verbose = False
        scan_name = ""
        action = ""

        opts, args = getopt.getopt(argv, "hds:a",
                                   ["scan_name=", "action="])
        for opt, arg in opts:
            if opt == '-h':
                print_help()
            if opt == '-d':
                verbose = True
            if opt in ('-s', '--scan_name'):
                scan_name=arg
            if opt in ('-a', '--action'):
                action = arg.upper()
        if scan_name and action and is_valid_action(action):
            modify_scan(scan_name, action, verbose)
        else:
            print_help()

    except requests.RequestException as e:
        print("An error occurred!")
        print(e)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
