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
    print("""veracode-da-app-link.py -a <application_name> -u <target_url> [-d]
        Starts a scan of <target_url> linked to an application identified in the Veracode Platform by <application_name>
""")
    sys.exit()

def create_application(application_name, criticality, verbose):
    if criticality is None:
        print("To create an application, it is necessary to provide a business criticality (--criticality, -c)")
        return False
    print(f"Creating application called: {application_name}")
    data = application_name
    scan_request = r'''{
    "profile":{
        "name":"{application_name}",
        "business_criticality":"{criticality}"
    }
}'''
    path = "https://api.veracode.com/appsec/v1/applications"
    scan_request = scan_request.replace("{application_name}", application_name, 1)
    scan_request = scan_request.replace("{criticality}", criticality, 2)

    if verbose:
        print(scan_request)

    response = requests.post(path, auth=RequestsAuthPluginVeracodeHMAC(), headers=headers, json=json.loads(scan_request))

    if verbose:
        print(f"status code {response.status_code}")
        body = response.json()
        if body:
            print(body)
    if response.status_code == 200:
        print("Successfully created application profile.")
        return True
    else:
        print(f"Unable to create application profile: {response.status_code}")
        return False

def launch_app_linked_scan(application_name, url, verbose, criticality, start_now):
    """Lists the scanner variables that are defined at the organization level. """
    path = api_base + f"platform_applications?application_name={application_name}"
    response = requests.get(path, auth=RequestsAuthPluginVeracodeHMAC(), headers=headers)
    data = response.json()

    if verbose:
        print(data)

    print(f"Initializing scan for url: {url} and search query {application_name}")

    if len(data["_embedded"]["platform_applications"]) == 0:
        print("No applications defined, creating new application.")
        if create_application(application_name, criticality, verbose):
            launch_app_linked_scan(application_name, url, verbose, criticality, start_now)
        return
    
    if len(data["_embedded"]["platform_applications"]) > 1:
        print("Warning - multiple applications found for {application_name}")
        print("Please select one of the following applications: ")
        for index in range(len(data["_embedded"]["platform_applications"])):
            app_name = data["_embedded"]["platform_applications"][index]["name"]
            app_uuid = data["_embedded"]["platform_applications"][index]["uuid"]
            print(f" {index+1} - {app_uuid}: {app_name}")
        selectedIndexStr = input("Insert application index:")
        if selectedIndexStr and selectedIndexStr.isnumeric():
            selectedIndex = int(selectedIndexStr)-1
        print(selectedIndex)
        if selectedIndex < 0 or selectedIndex > len(data["_embedded"]["platform_applications"]):
            print("Invalid application selected, closing application")
            return
    else:
        print("Application found")
        selectedIndex = 0        

    matched_app_name = data["_embedded"]["platform_applications"][selectedIndex]["name"]
    uuid = data["_embedded"]["platform_applications"][selectedIndex]["uuid"]
    
    print(f"Starting Dynamic Analysis for uuid '{uuid}' and application name '{matched_app_name}' for search term '{application_name}'")
                                           
    scan_request = r'''{
          "name": "{scan_name}",
          "scans": [
            {
              "linked_platform_app_uuid": "{uuid}",
              "scan_config_request": {
                "target_url": {
                  "url": "{url}",
                  "http_and_https": true,
                  "directory_restriction_type": "DIRECTORY_AND_SUBDIRECTORY"
                }
              }
            }
          ]{schedule}        
        }'''
    scan_request = scan_request.replace("{uuid}", uuid, 1)
    scan_request = scan_request.replace("{url}", url, 2)
    scan_request = scan_request.replace("{scan_name}", url, 2)
    if start_now:
        schedule=r''', "schedule": {
            "now": true,
            "duration": {
              "length": 1,
              "unit": "DAY"
            }
          }'''
    else:
        schedule = ""
    scan_request = scan_request.replace("{schedule}", schedule)    

    if verbose:
        print(scan_request)
    
    scan_path = api_base + "analyses"
    response = requests.post(scan_path, auth=RequestsAuthPluginVeracodeHMAC(), headers=headers, json=json.loads(scan_request))

    if verbose:
        print(f"status code {response.status_code}")
        body = response.json()
        if body:
            print(body)
    if response.status_code == 201:
        print("Successfully created applinked scan.")
        if start_now:
            print("Successfully started scanning the application")
    else:
        print(f"Unable to create DAST scan: {response.status_code}")

def main(argv):
    """Simple command line support for creating, deleting, and listing DA scanner variables"""
    try:
        application_name = ''
        verbose = False
        start_now = False
        criticality=None

        opts, args = getopt.getopt(argv, "hda:u:c:n",
                                   ["application_name=", "target_url=", "criticality="])
        for opt, arg in opts:
            if opt == '-h':
                print_help()
            if opt == '-d':
                verbose = True
            if opt == '-n':
                start_now = True
            if opt in ('-c', '--criticality'):
                criticality=arg
            if opt in ('-a', '--application_name'):
                application_name = arg
            if opt in ('-u', '--url'):
                target_url = arg


        if application_name and target_url:
            launch_app_linked_scan(application_name, target_url, verbose, criticality, start_now)
        else:
            print_help()

    except requests.RequestException as e:
        print("An error occurred!")
        print(e)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
