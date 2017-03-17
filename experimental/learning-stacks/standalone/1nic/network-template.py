# Copyright 2016 F5 Networks All rights reserved.
#
# Add copyright info here

"""Creates the network."""


def GenerateConfig(context):
  """Creates the network."""

  resources = [{
      'name': context.env['name'] + context.env['deployment'],
      'type': 'compute.v1.network',
      'properties': {
          'IPv4Range': '10.0.0.1/24'
      }
  }]
  return {'resources': resources}