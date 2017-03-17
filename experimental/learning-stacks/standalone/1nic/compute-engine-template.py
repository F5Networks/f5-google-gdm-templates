# Copyright 2016 F5 Networks All rights reserved.
#
# Add copyright info here

"""Creates the Compute Engine."""

NETWORK_NAME = 'f5-network' + '-'


def GenerateConfig(context):
  """Creates the Compute Engine with multiple templates."""

  resources = [{
      'name': 'big-ip1',
      'type': 'gs://f5-gdt/bigip1.py',
      'properties': {
          'machineType': context.properties ['machineType'],
          'zone': context.properties ['zone'],
          'licKey1': context.properties['licKey1'],
          'adminUsername': context.properties ['adminUsername'],
          'adminPassword': context.properties ['adminPassword'],
          'build': context.properties ['build'],          
          'network': NETWORK_NAME + context.env['deployment']
      }
  }, {
      'name': 'webserver',
      'type': 'gs://f5-gdt/webserver.py',
      'properties': {
          'machineType': 'n1-standard-2',
          'zone': 'us-west1-a',
          'network': NETWORK_NAME + context.env['deployment']
      }
  }, {
      'name': NETWORK_NAME,
      'type': 'gs://f5-gdt/network-template.py'
  }, {
      'name': NETWORK_NAME + 'firewall' + '-',
      'type': 'gs://f5-gdt/firewall-template.py',
      'properties': {
          'network': NETWORK_NAME + context.env['deployment']
      }
  }]
  outputs = [{
      'name': 'bigipIP',
      'value': ''.join(['$(ref.' + context.env['name'] + '-' + context.env['deployment'] + '.bigipIP)'])
  }] 
  return {'resources': resources}