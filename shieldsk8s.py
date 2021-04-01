import sys
import json
import yaml

from collections import OrderedDict

import click
import kubernetes
from kubernetes.client.rest import ApiException
import requests
import re

from flask import Flask
import urllib3


DEFAULT_CONSUL_URL = 'http://localhost:8500'
DEFAULT_INTERVAL = '30s'
DEFAULT_CHECK_IP = '127.0.0.1'
# DEFAULT_CONSUL_SINK_URL = '127.0.0.1:8500'
# DEFAULT_CONSUL_SINK_DOMAIN = '.consul'
# DEFAULT_CONSUL_SINK_PATH = '/v1/agent/service/register'
# DEFAULT_SVC_FILE = '/etc/consul.d/consulk8s_services.json'
# DEFAULT_BACKEND_PORT = 80

yaml.warnings({'YAMLLoadWarning': False})

@click.group(invoke_without_command=True)
@click.option('--k8s-config', '-k', default=None, metavar='PATH',
              help='Path to kubeconfig file (default: <kubectl behavior>)')
@click.option('--k8s-context', '-c', default=None, metavar='NAME',
              help='Kubeconfig context to use (default: <current-context>)')
def cli(k8s_config, k8s_context):
    kubernetes.config.load_kube_config(config_file=k8s_config,
                                       context=k8s_context)


@cli.command(name='expose')
# @click.option('--service-file', '-s', default=DEFAULT_SVC_FILE, metavar='PATH',
#               help='File to write (default: {})'.format(DEFAULT_SVC_FILE))
# @click.option('--default-ip', '--check-ip',
#               default=DEFAULT_CHECK_IP, metavar='IP',
#               help='Default Ingress IP (default: {})'.format(DEFAULT_CHECK_IP))
# @click.option('--consul-sink-url', '-c',
#               default=None, metavar='STRING',
#               help='Consul Sink url to upload services to (default: {})'.format(DEFAULT_CONSUL_SINK_URL))
# @click.option('--consul-sink-domain', '-d',
#               default=DEFAULT_CONSUL_SINK_DOMAIN, metavar='STRING',
#               help='Consul Sink domain, used to upload services to (default: {})'.format(DEFAULT_CONSUL_SINK_DOMAIN))
# @click.option('--consul-sink-path', default=DEFAULT_CONSUL_SINK_PATH, metavar='PATH',
#               help='Path on Consul Sink (default: {})'.format(DEFAULT_CONSUL_SINK_PATH))
# @click.option('--host-as-name', '-h', default=False, is_flag=True, metavar='BOOL', type=click.BOOL,
#               help='Use the ingress host as service name to help dns query (default: False)')
@click.option('--verbose', '-v', default=False, is_flag=True, metavar='BOOL', type=click.BOOL,
              help='Show output (default: False)')
# @click.option('--skip-checks', default=False, is_flag=True, metavar='BOOL', type=click.BOOL,
#               help='Skip checks (default: False)')
@click.option('--check-interval', '-i', default='30s', metavar='INTERVAL',
              help='HTTP check interval (default: {})'.format(DEFAULT_INTERVAL))
# @click.option('--code-when-changed', default=0, metavar='NUM', type=click.INT,
#               help='Exit code to return when services file is changed')
# @click.option('--change-command', '-C', default=None, metavar='CMD',
#               help='Command to run if service file is changed')


def expose(verbose, check_interval):
    print("Starting to expose")

    app = Flask(__name__)
    routes_pattern = "`([A-Za-z0-9]*)"

    @app.route('/')
    def hello_world():
        return 'Available services: /service/servicename/shieldstatus '

    @app.route('/service/<service>/shieldstatus')
    def get_shield_service_status(service):
        [domain, extension] = service.rsplit('.', 1)
        service_found = False
        try:
            ingress_routes = get_k8s_ingress_routes()
            for ingress in ingress_routes:
                host_route = ingress['spec']['routes'][0]['match']
                result = re.findall(routes_pattern, host_route)[0]
                if domain == result:
                    service_found = True
        except e:
            print(e)
            pass
        
        output_label = "undefined"
        label_color = "lightgrey"
        if service_found == True:
            output_label = "defined"
            label_color = "grey"
        


        request_success = False
        urllib3.disable_warnings()
        try:
            response = requests.get('https://' + str(domain) + "." + str(extension), verify=False)
            if response.status_code == 200:
                request_success = True
        except:
            pass
        
        message = "offline"
        message_color = "red"
        if request_success == True:
            message = "online"
            message_color = "green"
        
        return {
            "schemaVersion": 1,
            "label": output_label,
            "labelColor" : label_color,
            "message": message,
            "color": message_color
        }

    app.run(host="0.0.0.0", port=44444)

    return


def get_k8s_ingress_routes():
    crd_name = 'ingressroutes.traefik.containo.us'
    crd_group = 'traefik.containo.us'
    crd_version = 'v1alpha1'
    crd_plural = 'ingressroutes'
    ingress_routes = []
    try:
        custom_api_instance = kubernetes.client.CustomObjectsApi()
        api_response = custom_api_instance.list_cluster_custom_object(group=crd_group, version=crd_version, plural=crd_plural)
        ingress_routes = api_response['items']
    except ApiException:
        print("No resource %s found\n" % crd_name)
    return ingress_routes


if __name__ == '__main__':
    cli()
