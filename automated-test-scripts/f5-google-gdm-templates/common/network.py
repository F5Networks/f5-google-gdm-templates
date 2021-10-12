# Copyright 2021 F5 Networks All rights reserved.
#
# Version 0.1.0

# pylint: disable=W,C,R,duplicate-code,line-too-long

""" This template creates a network with subnets. """


def generate_name(prefix, suffix):
    """Generate unique name."""
    return prefix + "-" + suffix


def generate_config(context):
    """Entry point for the deployment resources."""

    name = context.properties.get('name') or \
        context.env['name']
    net_name = generate_name(context.properties['uniqueString'], name + '-network')
    network_self_link = '$(ref.{}.selfLink)'.format(net_name)
    auto_create_subnetworks = context.properties.get(
        'autoCreateSubnets',
        False
    )

    resources = [
        {
            'type': 'compute.v1.network',
            'name': net_name,
            'properties':
                {
                    'name': net_name,
                    'autoCreateSubnetworks': auto_create_subnetworks
                }
        }
    ]

    # Build Subnet resources:
    outputs = {}
    required_properties = ['network', 'ipCidrRange', 'region']
    optional_properties = [
        'description',
        'enableFlowLogs',
        'logConfig',
        'privateIpGoogleAccess',
        'privateIpv6GoogleAccess',
        'purpose',
        'role',
        'secondaryIpRanges'
    ]
    nats = []
    for subnet in context.properties.get('subnets', []):
        subnet['network'] = network_self_link
        subnet_name = generate_name(context.properties['uniqueString'], subnet['name'] + '-subnet')

        # Setup properties
        properties = {p: subnet[p] for p in required_properties}
        properties.update(
            {
                p: subnet[p]
                for p in optional_properties
                if p in subnet
            }
        )

        resources.append(
            {
                'name': subnet_name,
                'type': 'compute.v1.subnetwork',
                'properties': properties
            }
        )

        if not context.properties['provisionPublicIp']:
            nats.append({
                'name': generate_name(context.properties['uniqueString'], subnet_name + '-nat'),
                'natIpAllocateOption': 'AUTO_ONLY',
                'sourceSubnetworkIpRangesToNat': 'LIST_OF_SUBNETWORKS',
                'subnetworks': [
                    {
                        'name': '$(ref.{}.selfLink)'.format(subnet_name),

                    }
                ]
            })

        outputs[subnet_name] = {
            'selfLink': '$(ref.{}.selfLink)'.format(subnet_name),
            'cidrRange': '$(ref.{}.ipCidrRange)'.format(subnet_name),
            'region': '$(ref.{}.region)'.format(subnet_name),
            'network': '$(ref.{}.network)'.format(subnet_name),
            'gatewayAddress': '$(ref.{}.gatewayAddress)'.format(subnet_name)
        }
    if not context.properties['provisionPublicIp']:
        resources.append({
            'name': generate_name(context.properties['uniqueString'], name + '-router'),
            'type': 'compute.v1.router',
            'properties':
                {
                    'name': generate_name(context.properties['uniqueString'], 'rt'),
                    'network': network_self_link,
                    'region': context.properties['region'],
                    'nats': nats
                }
        })
    return {
        'resources':
            resources,
        'outputs':
            [
                {
                    'name': 'name',
                    'value': net_name
                },
                {
                    'name': 'selfLink',
                    'value': network_self_link
                },
                {
                    'name': 'subnets',
                    'value': outputs
                }
            ]
    }
