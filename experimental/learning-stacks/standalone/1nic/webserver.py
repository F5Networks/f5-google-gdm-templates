# Copyright 2016 F5 Networks All rights reserved.
#
# Add copyright info here

"""Creates the virtual machine with environment variables and startup script."""

COMPUTE_URL_BASE = 'https://www.googleapis.com/compute/v1/'


def GenerateConfig(context):
  """Creates the virtual machine."""

  resources = [{
      'name': context.env['name'] + '-' + context.env['deployment'],
      'type': 'compute.v1.instance',
      'properties': {
          'zone': context.properties['zone'],
          'machineType': ''.join([COMPUTE_URL_BASE, 'projects/',
                                  context.env['project'], '/zones/',
                                  context.properties['zone'], '/machineTypes/',
                                  context.properties['machineType']]),
          'disks': [{
              'deviceName': 'boot',
              'type': 'PERSISTENT',
              'boot': True,
              'autoDelete': True,
              'initializeParams': {
                  'sourceImage': ''.join([COMPUTE_URL_BASE, 'projects/',
                                          'debian-cloud/global/',
                                          'images/family/debian-8'])
              }
          }],
          'networkInterfaces': [{
              'network': '$(ref.' + context.properties['network']
                         + '.selfLink)',
              'accessConfigs': [{
                  'name': 'External NAT',
                  'type': 'ONE_TO_ONE_NAT'
              }]
          }],
          'metadata': {
              'items': [{
                  'key': 'startup-script',
                  'value': ''.join(['#!/bin/bash\n',
                                    'INSTANCE=$(curl http://metadata.google.',
                                    'internal/computeMetadata/v1/instance/',
                                    'hostname -H "Metadata-Flavor: Google")\n',
                                    'echo "<html><header><title>Hello from ',
                                    'Deployment Manager!</title></header>',
                                    '<body><h2>Hello from $INSTANCE</h2><p>',
                                    'Deployment Manager bids you good day!</p>',
                                    '</body></html>" > index.html\n',
                                    'sudo python -m SimpleHTTPServer 80\n'])
              }]
          }
      }
  }]
  return {'resources': resources}
 