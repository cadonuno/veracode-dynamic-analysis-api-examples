# Veracode Python Dynamic Analysis API Examples

## Overview

This project contains command line utilites that illustrate the use of Veracode's Dynamic Analysis REST APIs.

#### Scanner Variables

veracode-da-app-link.py illustrates the automation of setting DAST scanner variables.

#### Scan Start

veracode-da-scan-start.py illustrates how to automate starting DAST scans.

#### App Link

veracode-da-app-link.py illustrates how to create a DAST scan and link it to an application profile.

## Installation

Clone this repository:

    git clone https://github.com/cadonuno/veracode-dynamic-analysis-api-examples

Install dependencies:

    cd veracode-dynamic-analysis-api-examples
    pip install -r requirements.txt

## Usage

### Getting Started

It is highly recommended that you store veracode API credentials on disk, in a secure file that has 
appropriate file protections in place.

(Optional) Save Veracode API credentials in `~/.veracode/credentials`

    [default]
    veracode_api_key_id = <YOUR_API_KEY_ID>
    veracode_api_key_secret = <YOUR_API_KEY_SECRET>

Otherwise you will need to set environment variables:

    export VERACODE_API_KEY_ID=<YOUR_API_KEY_ID>
    export VERACODE_API_KEY_SECRET=<YOUR_API_KEY_SECRET>

### Scanner Variables

    scanner-variables-example.py [-x <variable_name>] [-k <variable_name> -v <variable_value>] [-l]
            -l          List all variables defined at account level.
            -d          Debug mode, prints out requests / response JSON.
            -k          Variable key to add, can be referenced in selenium scripts with ${variable_name}
            -v          Value of variable
            -x          Variable id to delete (id can be obtained from -l)

#### Scan Start

    veracode-da-scan-start.py -s <scan_name> -w <when_to_scan> [-d] [-l] [length] [-u] [unit] [scan schedule definition]
        Starts a scan for a DAST scan named <scan_name>
        -w determines when the scan should start:
          now
          once
          scheduled
        -Once:
         - --start_date/-b:
            date to start scan, formatted as 2019-09-27T16:49:00-04:00

#### App Link
    veracode-da-app-link.py -a <application_name> -u <target_url> [-d] [-n (Flag to tell the scanner to start a scan right away. Disabled by default)] [-c "<business_criticality>" (Mandatory if no application profile exists for <application_name>)]
        Starts a scan of <target_url> linked to an application identified in the Veracode Platform by <application_name>

## License

[![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

See the [LICENSE](LICENSE) file for details
