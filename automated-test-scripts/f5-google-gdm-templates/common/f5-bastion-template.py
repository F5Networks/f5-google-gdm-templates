# Copyright 2021 F5 Networks All rights reserved.
#
# Version v2.2.0

COMPUTE_URL_BASE = 'https://www.googleapis.com/compute/v1/'


def Instance(context, network1SharedVpc):
    instance = {
        'name': context.env['deployment'],
        'type': 'compute.v1.instance',
        'properties': {
            'canIpForward': True,
            'metadata': Metadata(context),
            'description': 'bastion host inteded for serving as jumpbox for no public cases',
            'zone': context.properties['zone'],
            'machineType': ''.join(['zones/', context.properties['zone'],
                                    '/machineTypes/', context.properties['instanceType']]),
            'disks': [{
                'deviceName': 'boot',
                'type': 'PERSISTENT',
                'boot': True,
                'autoDelete': True,
                'initializeParams': {
                    'sourceImage':
                        context.properties['osImage']
                }
            }],
            'networkInterfaces': [
                {
                    'network': ''.join([COMPUTE_URL_BASE, 'projects/',
                                        network1SharedVpc, '/global/networks/',
                                        context.properties['network1']]),
                    'subnetwork': ''.join([COMPUTE_URL_BASE, 'projects/',
                                           network1SharedVpc, '/regions/',
                                           context.properties['region'], '/subnetworks/',
                                           context.properties['subnet1']]),
                    'accessConfigs': [
                        {
                            'name': 'External NAT',
                            'type': 'ONE_TO_ONE_NAT'
                        }
                    ]
                },
                {
                    'network': ''.join([COMPUTE_URL_BASE, 'projects/',
                                        context.env['project'], '/global/networks/',
                                        context.properties['mgmtNetwork']]),
                    'subnetwork': ''.join([COMPUTE_URL_BASE, 'projects/',
                                           context.env['project'], '/regions/',
                                           context.properties['region'], '/subnetworks/',
                                           context.properties['mgmtSubnet']]),
                    'accessConfigs': []
                }
            ]
        }
    }
    return instance


def Metadata(context):
    metadata = {
        'items': [{
            'key': 'startup-script',
            'value': '#!/bin/bash\necho \"Starting VM...\"'
        }]
    }
    return metadata


def GenerateConfig(context):
    network1SharedVpc = context.env['project']
    if str(context.properties['network1SharedVpc']).lower() != 'none':
        network1SharedVpc = context.properties['network1SharedVpc']
    resources = [
        Instance(context, network1SharedVpc)
    ]

    return {'resources': resources}
