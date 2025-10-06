import requests, yaml
import credentials
import argparse

CLIPBOARD_SUPPORT = True
if CLIPBOARD_SUPPORT:
    import pyperclip

base_url = "https://support.fortinet.com/ES/api/fortiflex/v2/"

def get_oauth_token(api_username: str, api_password: str, client_id: str = "assetmanagement", base_url: str = "https://customerapiauth.fortinet.com/api/v1/oauth/token/") -> dict:
    body = {"username": api_username,
      "password": api_password,
      "client_id": client_id,
      "grant_type": "password"}
    
    response = requests.post(base_url, json=body).json()
    return response

def get_configuration_mappings(yaml_config: str="config.yaml") -> dict:
    with open(yaml_config, 'r') as file:
        config = yaml.safe_load(file)
    return config


def get_fortiflex_programs(oauth_token: str) -> dict:
    response = requests.post(f"{base_url}programs/list", headers={"Authorization": f"Bearer {oauth_token}"}).json()
    return response

def get_fortiflex_configurations(oauth_token: str, program_serial: str, account_id: str=None) -> dict:
    body = {"programSerialNumber": program_serial}
    if account_id:
        body["accountId"] = account_id
    response = requests.post(f"{base_url}configs/list", headers={"Authorization": f"Bearer {oauth_token}"}, json=body)
    response = response.json()
    return response

def get_fortiflex_entitlements(oauth_token: str, program_serial: str, config_id: str) -> dict:
    body = {"programSerialNumber": program_serial,
            "configId": config_id}
    response = requests.post(f"{base_url}entitlements/list", headers={"Authorization": f"Bearer {oauth_token}"}, json=body).json()
    return response


def get_first_stopped_or_inactive_entitlement(oauth_token: str, program_serial: str, config_id: str) -> dict:
    entitlements = get_fortiflex_entitlements(oauth_token, program_serial, config_id)
    for entitlement in entitlements['entitlements']:
        if entitlement['status'] in ['STOPPED', 'PENDING']:
            return entitlement
    return None

def reactivate_fortiflex_entitlement(oauth_token: str, program_serial: str, entitlement: dict) -> dict:
    body = {"serialNumber": entitlement['serialNumber']}
    response = requests.post(f"{base_url}entitlements/reactivate", headers={"Authorization": f"Bearer {oauth_token}"}, json=body)
    return response.json()

def regenerate_fortiflex_entitlement(oauth_token: str, program_serial: str, entitlement: dict) -> dict:
    body = {"serialNumber": entitlement['serialNumber']}
    response = requests.post(f"{base_url}entitlements/vm/token", headers={"Authorization": f"Bearer {oauth_token}"}, json=body)
    return response.json()

def regenerate_or_reactivate_fortiflex_entitlement(oauth_token: str, program_serial: str, entitlement: dict) -> dict:
    body = {"programSerialNumber": program_serial,
            "serialNumber": entitlement['serialNumber'],}
    modified_entitlement = entitlement.copy()
    if entitlement["status"] == "STOPPED":
        modified_entitlement = reactivate_fortiflex_entitlement(oauth_token, program_serial, entitlement)
    elif entitlement["status"] == "PENDING":
        modified_entitlement = regenerate_fortiflex_entitlement(oauth_token, program_serial, entitlement)
    
    return modified_entitlement

def create_fortiflex_entitlement(oauth_token: str, program_serial: str, config_id: str, count: int=1, description: str="My Flex Provisioned VM", folder_id: str=None) -> dict:
    body = {"configId": config_id,
            "count": count,
            "description": description,
            "endDate": None
            }
    if folder_id:
        body["folderId"] = folder_id
    response = requests.post(f"{base_url}entitlements/vm/create", headers={"Authorization": f"Bearer {oauth_token}"}, json=body).json()

    if count == 1:
        return response["entitlements"][0]
    return response


def main():
    token = get_oauth_token(credentials.api_username, credentials.api_token, client_id="flexvm")
    config = get_configuration_mappings()
    program_serial = config['general']['flex_serial']

    parser = argparse.ArgumentParser(description="Flex Provisioner Script")
    parser.add_argument("config_name", choices=["fortigate"], help="Name of the configuration to use")
    
    args = parser.parse_args()
    if args.config_name == "fortigate":
        configurations = get_fortiflex_configurations(token['access_token'], program_serial)
        selected_configuration = [x["id"] for x in configurations["configs"] if x["name"] == config['fortigate']['configuration']]
        if selected_configuration:
            selected_configuration = selected_configuration[0]
        first_available_asset = get_first_stopped_or_inactive_entitlement(token['access_token'], program_serial, selected_configuration)
        if first_available_asset:
            updated_entitlement = regenerate_or_reactivate_fortiflex_entitlement(token['access_token'], program_serial, first_available_asset)
            print(updated_entitlement["entitlements"][0]['token'])
        else:
            #No Assets - lets make a new one
            asset = create_fortiflex_entitlement(token['access_token'], program_serial, selected_configuration, count=1, description="Provisioned by Flex Provisioner")
            print(asset["token"])
            if CLIPBOARD_SUPPORT:
                pyperclip.copy(asset["token"])
    



if __name__ == "__main__":
    main()