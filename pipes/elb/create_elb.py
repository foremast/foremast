import requests
import argparse
import json
from jinja2 import Template

elb_json = '''
{
   "job":[
      {
         "stack":"{{ app_stack }}",
         "isInternal":{{ isInternal }},
         "credentials":"{{ env }}",
        "region":"us-east-1",
         "vpcId":"{{ vpc_id }}",
         "healthCheckProtocol":"{{ health_protocol }}",
         "healthCheckPort":{{ health_port }},
         "healthCheckPath":"{{ health_path }}",
         "healthTimeout":{{ health_timeout}},
         "healthInterval":{{ health_interval }},
         "healthyThreshold":{{ healthy_threshold }},
         "unhealthyThreshold":{{ unhealthy_threshold }},
         "regionZones":[
            "us-east-1b",
            "us-east-1c",
            "us-east-1d",
            "us-east-1e"
         ],
         "securityGroups":[
            "{{ security_groups }}"
         ],
         "listeners":[
            {
               "internalProtocol":"{{ int_listener_protcol }}",
               "internalPort":{{ int_listener_port }},
               "externalProtocol":"{{ ext_listener_protocol}}",
               "externalPort":{{ext_listener_port}}
            }
         ],
         "name":"{{ elb_name }}",
         "usePreferredZones":true,
         "subnetType":"{{ subnet_type}}",
         "healthCheck":"{{ hc_string }}",
         "type":"upsertLoadBalancer",
         "availabilityZones":{
            "us-east-1":[
               "us-east-1b",
               "us-east-1c",
               "us-east-1d",
               "us-east-1e"
            ]
         },
         "user":"[anonymous]"
      }
   ],
   "application":"{{ app_name }}",
   "description":"Create Load Balancer: {{ app_name }}-{{ app_stack }}"
}

'''
class CreateELB:
    '''
    In: application, stack, internal/external, environments, healthcheck protocol, healthcheck path, healthcheck port,
    health timeout, health Interval, healthy threshold, unhealthyThreshold, securityGroups, InternalListenrPort, internalLitenerProtocol,
    externalListenerPrtocol, externalListenerProtocol, elbName,
    '''
    def __init__(self):
        return 'place holder'

    def get_vpc_id(self, account):
        return 'palce holder'






#python create_elb.py --app testapp --stack teststack --elb_type internal --env prod,stage --health_protocol HTTP --health_port 80 --health_path /health --security_groups sg_apps,sg_offices --int_listener_port 80 --int_listener_protocol HTTP --ext_listener_port 8080 --ext_listener_protocol HTTP --elb_name test_elb --elb_subnet internal --health_timeout=10 --health_interval=2 --healthy_threshold=4 --unhealthy_threshold=6


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Example with non-optional arguments')

    parser.add_argument('--app', action="store", help="application name", required=True)
    parser.add_argument('--stack', action="store", help="application stack", required=True)
    parser.add_argument('--elb_type', action="store", help="elb type: internal/external", required=True)
    parser.add_argument('--env', action="store", help="environment: dev, stage, prod", required=True)
    parser.add_argument('--health_protocol', action="store", help="health check protocol: http/tcp", required=True)
    parser.add_argument('--health_port', action="store", help="health check port", required=True)
    parser.add_argument('--health_path', action="store", help="health check path stack", required=False, default="/health")
    parser.add_argument('--health_timeout', action="store", help="health check timeout in seconds", required=True, default=10)
    parser.add_argument('--health_interval', action="store", help="health check interval in seconds", required=True, default=20)
    parser.add_argument('--healthy_threshold', action="store", help="healthy threshold", required=True, default=2)
    parser.add_argument('--unhealthy_threshold', action="store", help="unhealthy threshold", required=True, default=5)
    parser.add_argument('--security_groups', action="store", help="security groups", required=True, default="sg_apps", nargs="+")
    parser.add_argument('--int_listener_port', action="store", help="internal listener port", required=True, default=8080)
    parser.add_argument('--int_listener_protocol', action="store", help="internal listener protocol", required=True, default="HTTP")
    parser.add_argument('--ext_listener_port', action="store", help="internal listener port", required=True, default=80)
    parser.add_argument('--ext_listener_protocol', action="store", help="external listener protocol", required=True, default="HTTP")
    parser.add_argument('--elb_name', action="store", help="elb name", required=True)
    parser.add_argument('--elb_subnet', action="store", help="elb subnet", required=True, default="internal")

    args = parser.parse_args()
    print args.app, args.elb_name
    template = Template(elb_json)
    print template.render(app_stack=args.stack,
                          app_name=args.app,
                          isInternal='True',
                          vpc_id='vpc-xxxx',
                          health_protocol=args.health_protocol,
                          health_port=args.health_port,
                          health_path=args.health_path,
                          health_timeout=args.health_timeout,
                          health_interval=args.health_interval,
                          unhealthy_threshold=args.unhealthy_threshold,
                          healthy_threshold=args.healthy_threshold,
                          security_groups=args.security_groups,
                          int_listener_protcol=args.int_listener_protocol,
                          ext_listener_protcol=args.ext_listener_protocol,
                          int_listener_port=args.int_listener_port,
                          ext_listener_port=args.ext_listener_port,
                          elb_name=args.elb_name,
                          elb_subnet=args.elb_subnet,
                          hc_string='blah:700/health')




