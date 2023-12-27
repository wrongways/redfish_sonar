import requests
import json
import urllib3

bmc_name_pattern = 'jura*-bmc'
redfish_root = '/redfish/v1'


def bmc_iterator(padding=1):
    min_bmc_id = 10
    max_bmc_id = 500

    for bmc_id in range(min_bmc_id, max_bmc_id + 1):
        yield bmc_name_pattern.replace('*', f'{bmc_id:0{padding}}')


def read_credentials(credentials_file):
    with open(credentials_file) as f:
        return [tuple(user_pass.split()) for user_pass in f.readlines()]


# main
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

bmcs = {}

for bmc in bmc_iterator(padding=3):
    bmc_info = bmcs.get(bmc, {})

    # Determine if there's a redfish server on bmc
    url = f'https://{bmc}{redfish_root}'
    print(f'Connecting to {url}')
    try:
        resp = requests.get(url, verify=False)
        has_redfish = resp.status_code == requests.codes.ok
        bmc_info['redfish'] = has_redfish
        print(f"{bmc} redfish: {has_redfish}")
    except requests.exceptions.ConnectionError:
        continue

    if has_redfish and bmc_info.get('user_pass') is None:
        for user_pass in read_credentials('credentials.txt'):
            chassis_url = url + '/Chassis'
            resp = requests.get(chassis_url, auth=user_pass, verify=False)
            if resp.status_code == requests.codes.ok:
                bmc_info['user_pass'] = user_pass
                print(json.dumps(resp.json(), indent=3, sort_keys=True))
                chassis = [c.get('@odata.id') for c in resp.json().get('Members', {}) if c]
                bmc_info['chassis'] = chassis
                bmcs[bmc] = bmc_info
                break
            elif resp.status_code == requests.codes.unauthorized:
                continue
            else:
                print(f"HTTP Status: {resp.status_code}")


print(f"{'BMC':>11} | Has redfish | Username/password | Chassis")
print(f'{"=" * 12}+{"=" * 13}+{"=" * 19}+{"=" * 8}')
for bmc, info in bmcs.items():
    user_pass = '/'.join(info.get('user_pass', ['** UNKNOWN **']))
    chassis = [c.replace('/redfish/v1/Chassis/', '') for c in info.get('chassis')]
    print(f"{bmc:>10} | {bool(info['redfish']):11} | {user_pass:17} | {', '.join(chassis)}")

with open('bmc_info.json', 'w') as f:
    json.dump(bmcs, f, indent=3, sort_keys=True)

