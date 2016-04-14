import requests
from collections import defaultdict 

def get_subnets(gate_url='http://gate-api.build.example.com:8084', target='ec2'):
    """ Gets all availability zones for a given target
        Params:
            gate_url: The URL to hit for gate API access
            target: the type of subnets to look up (ec2 or elb)
        Return:
            az_dict: dictionary of  availbility zones, structured like
            { $account: { $region: [ $avaibilityzones ] } } """
    az_dict = {}
    az_list = []
    account_az_dict = defaultdict(defaultdict)
    subnet_url = gate_url + "/subnets/aws"
    r = requests.get(subnet_url)

    for subnet in r.json():
        if subnet['target'] == target:
            az = subnet['availabilityZone']

            account = subnet['account']
            region = subnet['region']
            if account == 'pci':
                print(az)
            try:
                if az not in account_az_dict[account][region]:
                    account_az_dict[account][region].append(az)
            except KeyError:
                account_az_dict[account][region] = [az]

    return account_az_dict


if __name__ == "__main__":
    print(get_subnets())
