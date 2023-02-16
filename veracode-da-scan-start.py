import sys
import requests
import getopt
import json
from veracode_api_signing.plugin_requests import RequestsAuthPluginVeracodeHMAC

from veracode_api_signing.credentials import get_credentials

api_base = "https://api.veracode.{instance}/"
headers = {
    "User-Agent": "Dynamic Analysis API Example Client",
    "Content-Type": "application/json"
}


def print_help(status):
    """Prints command line options and exits"""
    print("""veracode-da-scan-edit.py -s <scan_name> -w <when_to_scan> [-d] [-l] [length] [-u] [unit] [scan schedule definition]
        Starts a scan for a DAST scan named <scan_name>
        -w determines when the scan should start:
          now
          once
          scheduled
        -Once:
         - --start_date/-b:
            date to start scan, formatted as 2019-09-27T16:49:00-04:00
""")
    sys.exit(status)

def find_exact_match(scan_list, scan_name):
    for index in range(len(scan_list)):
        if scan_list[index]["name"] == scan_name:
            return index    
    return -1

def start_scan(scan_name, schedule, verbose, action):
    path = f"{api_base}/was/configservice/v1/analyses?name={scan_name}"
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
            {schedule}
        }
    }'''
    scan_request = scan_request.replace("{matched_scan_name}", matched_scan_name, 1)
    scan_request = scan_request.replace("{schedule}", schedule, 2)

    if verbose:
        print(scan_request)
    
    scan_path = f"{api_base}/was/configservice/v1/analyses/{analysis_id}?method=PATCH"
    response = requests.put(scan_path, auth=RequestsAuthPluginVeracodeHMAC(), headers=headers, json=json.loads(scan_request))

    if verbose:
        print(f"status code {response.status_code}")
    if response.status_code == 204:
        print(f"Successfully {action} for {matched_scan_name}.")
    else:
        print(f"Unable to start DAST scan: {response.status_code}")
        body = response.json()
        if body:
            print(body)

def get_schedule_parameter_value(schedule, start_date, end_date, recurrence_type, schedule_end_after, recurrence_interval, day_of_week, length, unit):
    schedule_string = ""
    if schedule == "NOW":
        schedule_string = r'''"now": true'''
    elif schedule == "ONCE":
        schedule_string = r'''"start_date": "{start_date}"'''
        schedule_string = schedule_string.replace("{start_date}", start_date, 1)
    elif schedule == "SCHEDULE":
        schedule_string = r'''"start_date": "{start_date}"
        "end_date": "{end_date}",
        "scan_recurrence_schedule": {
            "recurrence_type": "{recurrence_type}",
            "schedule_end_after": {schedule_end_after},
            "recurrence_interval": {recurrence_interval},
            "day_of_week": "{day_of_week}"
        }'''
        schedule_string = schedule_string.replace("{start_date}", start_date, 1)
        schedule_string = schedule_string.replace("{end_date}", end_date, 1)
        schedule_string = schedule_string.replace("{recurrence_type}", recurrence_type, 1)
        schedule_string = schedule_string.replace("{schedule_end_after}", schedule_end_after, 1)
        schedule_string = schedule_string.replace("{recurrence_interval}", recurrence_interval, 1)
        schedule_string = schedule_string.replace("{day_of_week}", day_of_week, 1)
    else:
        print_help(1)
        
    schedule_string = schedule_string + r''',
            "duration": {
                "length": {length},
                "unit": "{unit}"
            }'''
    schedule_string = schedule_string.replace("{length}", str(length), 1)
    schedule_string = schedule_string.replace("{unit}", str(unit), 1)
    return schedule_string

def get_schedule_action(schedule):
    if schedule == "NOW":
        return "started scan"
    elif schedule == "ONCE":
        return "scheduled single scan"
    elif schedule == "SCHEDULE":
        return "set up scan schedule"
    return ""

def update_api_base():
    api_key_id, api_key_secret = get_credentials()
    if api_key_id.startswith("vera01"):
        api_base = api_base.replace("{intance}", "eu", 1)
    else:
        api_base = api_base.replace("{intance}", "com", 1)

def main(argv):
    """Simple command line support for creating, deleting, and listing DA scanner variables"""
    try:
        verbose = False
        scan_name = ""
        start_date = ""
        end_date = ""
        recurrence_type = "WEEKLY"
        schedule_end_after = 2
        recurrence_interval = 1
        day_of_week = "FRIDAY"
        length = 1
        unit = "DAY"

        opts, args = getopt.getopt(argv, "hdn:s:b:e:t:a:i:w:l:u",
                                   ["name=", "schedule=", "start_date=", "end_date=",
                                   "recurrence_type=", "schedule_end_after=", "recurrence_interval=",
                                   "day_of_week=", "length=", "unit="])
        for opt, arg in opts:
            if opt == '-h':
                print_help(0)
            if opt == '-d':
                verbose = True
            if opt in ('-n', '--name'):
                scan_name=arg                
            if opt in ('-s', "--schedule"):
                schedule=arg.upper()
            if opt in ('-b', '--start_date'):
                start_date=arg
            if opt in ('-e', '--end_date'):
                end_date=arg
            if opt in ('-t', '--recurrence_type'):
                recurrence_type=arg
            if opt in ('-a', '--schedule_end_after'):
                schedule_end_after=arg
            if opt in ('-i', '--recurrence_interval'):
                recurrence_interval=arg
            if opt in ('-w', '--day_of_week'):
                day_of_week=arg
            if opt in ('-l', '--length'):
                length=arg
            if opt in ('-u', '--unit'):
                unit=arg

        update_api_base()
        if scan_name:
            start_scan(scan_name, get_schedule_parameter_value(schedule, 
                start_date, end_date, recurrence_type, schedule_end_after, 
                recurrence_interval, day_of_week, length, unit), 
                verbose, get_schedule_action(schedule))
        else:
            print_help(1)

    except requests.RequestException as e:
        print("An error occurred!")
        print(e)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
