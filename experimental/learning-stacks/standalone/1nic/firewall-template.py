# Copyright 2016 F5 Networks All rights reserved.
#
# Add copyright info here

"""Creates the firewall."""


def GenerateConfig(context):
  """Creates the firewall with environment variables."""

  resources = [{
      'name': context.env['name'] + context.env['deployment'],
      'type': 'compute.v1.firewall',
      'properties': {
          'network': '$(ref.' + context.properties['network'] + '.selfLink)',
          'sourceRanges': ['0.0.0.0/0'],
          'allowed': [{
              'IPProtocol': 'TCP',
              'ports': [80,22,443,8443]
          }]
      }
  }]
  return {'resources': resources}