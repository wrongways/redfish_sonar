import requests
import json

bmc_name_pattern = 'jura*-bmc'
redfish_root = '/redfish/v1'

def bmc_iterator():
    min_bmc_num = 1
    max_bmc_num = 500

    for bmc_num in range(min_bmc_num, max_bmc_num + 1):
        yield bmc_name_pattern.replace('*', f'{bmc_num:03}')


def read_credentials(credentials_file):
    with open(credentials_file) as f:
        return [tuple(user_pass.split()) for user_pass in f.readlines()]

bmcs = {}

for bmc in bmc_iterator():
    bmc_info = bmcs.get(bmc, {})

    # Determine if there's a redfish server on bmc
    url = f'https://{bmc}{redfish_root}'
    print(f'Connecting to {url}')
    try:
        resp = requests.get(url)
        has_redfish = resp.status_code == requests.codes.ok
        bmc_info['redfish'] = has_redfish
        print(f"{bmc} redfish: {has_redfish}")
    except requests.exceptions.ConnectionError as e:
        print(f">>>>  No such bmc: {bmc}")
        continue

    if has_redfish and bmc_info.get('user_pass') is None:
        for user_pass in read_credentials('credentials.txt'):
            chassis_url = url + '/Chassis'
            resp = requests.get(chassis_url, auth=user_pass)
            if resp.status_code == requests.codes.ok:
                bmc_info['user_pass'] = user_pass
                print(json.dumps(resp.json(), indent=3, sort_keys=True))
                bmcs[bmc] = bmc_info
                break
            print(f"HTTP Status: {resp.status_code}")


print(f"{'BMC':>10} Has redfish Username/password")
print('=' * 38)
for bmc, info in bmcs.items():
    user_pass = '/'.join(info.get('user_pass', ['** UNKNOWN **']))
    print(f"{bmc:>10} {info.get('redfish'):11} {user_pass}")

with open('bmc_info.json', 'w') as f:
    json.dump(bmcs, f, indent=3, sort_keys=True)

