import requests


def get_subnets(gate_url='http://gate-api.build.example.com:8084', target='ec2'):
    """ Gets all availability zones for a given target
        Params: 
            gate_url: The URL to hit for gate API access
            target: the type of subnets to look up (ec2 or elb)
        Return:
            az_dict: dictionary of  availbility zones, structured like 
            { $account: { $region: [ $avaibilityzones ] } } """
    az_dict = {}
    subnet_url = gate_url + "/subnets/aws"
    r =  requests.get(subnet_url)
    
    for item in r.json():
        if item['target'] == target:
            az = item['availabilityZone']
            account = item['account']
            region = item['region']
            try:
                if az not in az_dict[account][region]:
                    az_dict[account][region].append(az)
            except KeyError:
                try:
                    az_dict[account][region].append(az)
                except KeyError:
                    az_dict[account] = {region: [az] }
  
    return az_dict


if __name__ == "__main__":
    print(get_subnets())
