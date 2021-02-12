# Copyright 2019 F5 Networks All rights reserved.
#
# Version 3.11.0


"""Creates BIG-IP"""
COMPUTE_URL_BASE = 'https://www.googleapis.com/compute/v1/'
def Storage(context,storageName):
    # Build storage container
    storage = {
        'name': storageName,
        'type': 'storage.v1.bucket',
        'properties': {
            'project': context.env['project'],
            'name': storageName,
        }
    }
    return storage
def Instance(context,storageName,deployment):
    # Build instance template
    instance = {
        'name': 'bigip-' + deployment,
        'type': 'compute.v1.instanceTemplate',
        'properties': {
            'properties': {
                'canIpForward': True,
                'tags': {
                    'items': ['mgmtfw-' + context.env['deployment'],'appfw-' + context.env['deployment'],'syncfw-' + context.env['deployment'],]
                },
                'labels': {
                    'f5_deployment': context.env['deployment']
                },
                'machineType': context.properties['instanceType'],
                'serviceAccounts': [{
                    'email': context.properties['serviceAccount'],
                    'scopes': ['https://www.googleapis.com/auth/compute','https://www.googleapis.com/auth/devstorage.read_write','https://www.googleapis.com/auth/pubsub']
                }],
                'disks': [{
                    'deviceName': 'boot',
                    'type': 'PERSISTENT',
                    'boot': True,
                    'autoDelete': True,
                    'initializeParams': {
                        'sourceImage': ''.join([COMPUTE_URL_BASE, 'projects/f5-7626-networks-public',
                                        '/global/images/',
                                        context.properties['imageName'],
                                        ])
                    }
                }],
                'networkInterfaces': [{
                    'network': ''.join([COMPUTE_URL_BASE, 'projects/',
                                    context.env['project'], '/global/networks/',
                                    context.properties['mgmtNetwork']]),
                    'subnetwork': ''.join([COMPUTE_URL_BASE, 'projects/',
                                    context.env['project'], '/regions/',
                                    context.properties['region'], '/subnetworks/',
                                    context.properties['mgmtSubnet']]),
                    'accessConfigs': [{
                        'name': 'Management NAT',
                        'type': 'ONE_TO_ONE_NAT'
                    }],
                }],
                'metadata': Metadata(context,storageName,deployment)
            }
        }
    }
    return instance
def Igm(context,deployment):
    # Build instance group manager
    igm = {
        'name': deployment + '-igm',
        'type': 'compute.v1.instanceGroupManager',
        'properties': {
            'baseInstanceName': deployment + '-bigip',
            'instanceTemplate': ''.join(['$(ref.', 'bigip-' + deployment,
                                       '.selfLink)']),
            'targetSize': int(context.properties['targetSize']),
            'targetPools': ['$(ref.' + deployment + '-tp.selfLink)'],
            'zone': context.properties['availabilityZone1'],
        }
    }
    return igm
def Autoscaler(context,deployment):
    # Build autoscaler
    autoscaler = {
        'name': deployment + 'big-ip-as',
        'type': 'compute.v1.autoscalers',
        'properties': {
            'zone': context.properties['availabilityZone1'],
            'target': '$(ref.' + deployment + '-igm.selfLink)',
            'autoscalingPolicy': {
                "minNumReplicas": int(context.properties['minReplicas']),
                'maxNumReplicas': int(context.properties['maxReplicas']),
                'cpuUtilization': {
                    'utilizationTarget': float(context.properties['cpuUtilization'])
                },
                'coolDownPeriodSec': int(context.properties['coolDownPeriod'])
            }
        },
    }
    return autoscaler
def HealthCheck(context,deployment):
    # Build health autoscaler health check
    healthCheck = {
        'name': deployment,
        'type': 'compute.v1.httpHealthCheck',
        'properties': {
            'port': int(context.properties['applicationPort']),
            'host': str(context.properties['applicationDnsName']),
        }
    }
    return healthCheck
def TargetPool(context,deployment):
    # Build lb target pool
    targetPool = {
        'name': deployment + '-tp',
        'type': 'compute.v1.targetPool',
        'properties': {
            'region': context.properties['region'],
            'healthChecks': ['$(ref.' + deployment + '.selfLink)'],
            'sessionAffinity': 'CLIENT_IP',
        }
    }
    return targetPool
def ForwardingRule(context,deployment):
    # Build forwarding rule
    forwardingRule = {
        'name': deployment + '-fr',
        'type': 'compute.v1.forwardingRule',
        'properties': {
            'region': context.properties['region'],
            'IPProtocol': 'TCP',
            'target': '$(ref.' + deployment + '-tp.selfLink)',
            'loadBalancingScheme': 'EXTERNAL',
        }
    }
    return forwardingRule
def FirewallRuleSync(context):
    # Build Sync traffic firewall rule
    firewallRuleSync = {
        'name': 'syncfw-' + context.env['deployment'],
        'type': 'compute.v1.firewall',
        'properties': {
            'network': ''.join([COMPUTE_URL_BASE, 'projects/',
                                context.env['project'], '/global/networks/',
                                context.properties['mgmtNetwork']]),
            'targetTags': ['syncfw-'+ context.env['deployment']],
            'sourceTags': ['syncfw-'+ context.env['deployment']],
            'allowed': [{
                'IPProtocol': 'TCP',
                'ports': ['4353']
                },{
                'IPProtocol': 'UDP',
                'ports': ['1026'],
                },{
                "IPProtocol": "TCP",
                "ports": ['6123-6128'],
                },
            ]
        }
    }
    return firewallRuleSync
def FirewallRuleApp(context):
    # Build Application firewall rule
    firewallRuleApp = {
        'name': 'appfw-' + context.env['deployment'],
        'type': 'compute.v1.firewall',
        'properties': {
            'network': ''.join([COMPUTE_URL_BASE, 'projects/',
                                context.env['project'], '/global/networks/',
                                context.properties['mgmtNetwork']]),
            'sourceRanges': ['0.0.0.0/0'],
            'targetTags': ['appfw-'+ context.env['deployment']],
            'allowed': [{
                "IPProtocol": "TCP",
                "ports": [str(context.properties['applicationPort'])],
                },
            ]
        }
    }
    return firewallRuleApp
def FirewallRuleMgmt(context):
    # Build Management firewall rule
    firewallRuleMgmt = {
        'name': 'mgmtfw-' + context.env['deployment'],
        'type': 'compute.v1.firewall',
        'properties': {
            'network': ''.join([COMPUTE_URL_BASE, 'projects/',
                                context.env['project'], '/global/networks/',
                                context.properties['mgmtNetwork']]),
            'sourceRanges': ['0.0.0.0/0'],
            'targetTags': ['mgmtfw-'+ context.env['deployment']],
            'allowed': [{
                "IPProtocol": "TCP",
                "ports": ['8443','22'],
                },
            ]
        }
    }
    return firewallRuleMgmt
def Metadata(context,storageName,deployment):
    # Build metadata
    ALLOWUSAGEANALYTICS = str(context.properties['allowUsageAnalytics'])
    if ALLOWUSAGEANALYTICS == "yes":
        CUSTHASH = 'CUSTOMERID=`curl -s "http://metadata.google.internal/computeMetadata/v1/project/numeric-project-id" -H "Metadata-Flavor: Google" |sha512sum|cut -d " " -f 1`;\nDEPLOYMENTID=`curl -s "http://metadata.google.internal/computeMetadata/v1/instance/id" -H "Metadata-Flavor: Google"|sha512sum|cut -d " " -f 1`;'
        SENDANALYTICS = ' --metrics "cloudName:google,region:' + context.properties['region'] + ',bigipVersion:' + context.properties['imageName'] + ',customerId:${CUSTOMERID},deploymentId:${DEPLOYMENTID},templateName:f5-payg-autoscale-bigip-waf.py,templateVersion:3.11.0,licenseType:payg"'
    else:
        CUSTHASH = 'echo "No analytics."'
        SENDANALYTICS = ''

    # Provisioning modules
    PROVISIONING_MODULES = ','.join(context.properties['bigIpModules'].split('-'))

    ## generate metadata
    metadata = {
                'items': [{
                    'key': 'startup-script',
                    'value': ('\n'.join(['#!/bin/bash',
                                    'if [ -f /config/startupFinished ]; then',
                                    '    exit',
                                    'fi',
                                    'mkdir -p /config/cloud/gce',
                                    'cat <<\'EOF\' > /config/installCloudLibs.sh',
                                    '#!/bin/bash',
                                    'echo about to execute',
                                    'checks=0',
                                    'while [ $checks -lt 120 ]; do echo checking mcpd',
                                    '    tmsh -a show sys mcp-state field-fmt | grep -q running',
                                    '    if [ $? == 0 ]; then',
                                    '        echo mcpd ready',
                                    '        break',
                                    '    fi',
                                    '    echo mcpd not ready yet',
                                    '    let checks=checks+1',
                                    '    sleep 10',
                                    'done',
                                    'echo loading verifyHash script',
                                    'if ! tmsh load sys config merge file /config/verifyHash; then',
                                    '    echo cannot validate signature of /config/verifyHash',
                                    '    exit',
                                    'fi',
                                    'echo loaded verifyHash',
                                    'declare -a filesToVerify=(\"/config/cloud/f5-cloud-libs.tar.gz\" \"/config/cloud/f5-cloud-libs-gce.tar.gz\" \"/var/config/rest/downloads/f5-appsvcs-3.25.0-3.noarch.rpm\")',
                                    '#declare -a filesToVerify=()',
                                    'for fileToVerify in \"${filesToVerify[@]}\"',
                                    'do',
                                    '    echo verifying \"$fileToVerify\"',
                                    '    if ! tmsh run cli script verifyHash \"$fileToVerify\"; then',
                                    '        echo \"$fileToVerify\" is not valid',
                                    '        exit 1',
                                    '    fi',
                                    '    echo verified \"$fileToVerify\"',
                                    'done',
                                    'mkdir -p /config/cloud/gce/node_modules/@f5devcentral',
                                    'echo expanding f5-cloud-libs.tar.gz',
                                    'tar xvfz /config/cloud/f5-cloud-libs.tar.gz -C /config/cloud/gce/node_modules/@f5devcentral',
                                    'echo expanding f5-cloud-libs-gce.tar.gz',
                                    'tar xvfz /config/cloud/f5-cloud-libs-gce.tar.gz -C /config/cloud/gce/node_modules/@f5devcentral',
                                    'echo "expanding waf policies"',
                                    'tar xvfz /config/cloud/asm-policy-linux.tar.gz -C /config/cloud',
                                    'echo cloud libs install complete',
                                    'touch /config/cloud/cloudLibsReady',
                                    'EOF',
                                    'echo \'Y2xpIHNjcmlwdCAvQ29tbW9uL3ZlcmlmeUhhc2ggewpwcm9jIHNjcmlwdDo6cnVuIHt9IHsKICAgICAgICBpZiB7W2NhdGNoIHsKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS1jbG91ZC1saWJzLnRhci5neikgZGU2MTk1YTBhN2ZhMThlZWM1YzkzMGNhMTIzZmNmM2NjZGJjMzgwZmJhODk5OTM1MGRhZDhkZTA0OTljM2Q1YjQyYzJiOWQ5MGE1ZDRkMTk3MzQ0NjdmZDljMDJjMGI3NDdkYjA4YWE0MWQ5YTkzMzZkOWQ2MzUwOGVmZGU5ZGYKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS1jbG91ZC1saWJzLWF3cy50YXIuZ3opIDI0ZDBkYmMzYTJlYzZhNDIwZGEzNDE5OThkYWU0Y2Y2NGY5YmE4NmVjOGFmZGVkN2RhNjcwMzFhYTg5N2IyYTI4ZWYxYzc3YTJhYjFhZDI3MDUyN2JkNmExNWFhZDE5NjQyYjBjOTdjY2I5YTQ4ZTU4ZTdiMzVhMWU5MjBjYTU0CiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUtY2xvdWQtbGlicy1henVyZS50YXIuZ3opIDQ3N2E2MTE1NDkwYTMxMTMwYzFlZjE0NTA3MmZlMzhhODI2NzYyZDBkNjA0ODVjMTIyYTMyMzAzNTIyM2ZkNTEyZWMwNTYzM2MxMDBhNDBkZjJjMjNlNzNlMzUxMWZmMDFlZTgxMWU0OWEzODUwZjljZmFiZDYyY2E1NTE5YWEwCiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUtY2xvdWQtbGlicy1nY2UudGFyLmd6KSA0NjBmNGIyNjNhYmU4OTc4ZjIwYzg2ZTIzYTJhNmE5MjJhNmRiMzNhZDhmZTY4ZTNjMWQ1ZGZiZWQxYTg5NTEyYjlhNDQxY2U0ODVjZDRiMjBhOWQyMDBkZmI5NjJhZTA4YTJjMGQzZGY4N2Q3ZmIwYzYzZDI5ZmQwNDY3NDJlMgogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LWNsb3VkLWxpYnMtb3BlbnN0YWNrLnRhci5neikgNWM4M2ZlNmE5M2E2ZmNlYjVhMmU4NDM3YjVlZDhjYzlmYWY0YzE2MjFiZmM5ZTZhMDc3OWY2YzIxMzdiNDVlYWI4YWUwZTdlZDc0NWM4Y2Y4MjFiOTM3MTI0NWNhMjk3NDljYTBiN2U1NjYzOTQ5ZDc3NDk2Yjg3MjhmNGIwZjkKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS1jbG91ZC1saWJzLWNvbnN1bC50YXIuZ3opIGEzMmFhYjM5NzA3M2RmOTJjYmJiYTUwNjdlNTgyM2U5YjVmYWZjYTg2MmEyNThiNjBiNmI0MGFhMDk3NWMzOTg5ZDFlMTEwZjcwNjE3N2IyZmZiZTRkZGU2NTMwNWEyNjBhNTg1NjU5NGNlN2FkNGVmMGM0N2I2OTRhZTRhNTEzCiAgICAgICAgICAgIHNldCBoYXNoZXMoYXNtLXBvbGljeS1saW51eC50YXIuZ3opIDYzYjVjMmE1MWNhMDljNDNiZDg5YWYzNzczYmJhYjg3YzcxYTZlN2Y2YWQ5NDEwYjIyOWI0ZTBhMWM0ODNkNDZmMWE5ZmZmMzlkOTk0NDA0MWIwMmVlOTI2MDcyNDAyNzQxNGRlNTkyZTk5ZjRjMjQ3NTQxNTMyM2UxOGE3MmUwCiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUuaHR0cC52MS4yLjByYzQudG1wbCkgNDdjMTlhODNlYmZjN2JkMWU5ZTljMzVmMzQyNDk0NWVmODY5NGFhNDM3ZWVkZDE3YjZhMzg3Nzg4ZDRkYjEzOTZmZWZlNDQ1MTk5YjQ5NzA2NGQ3Njk2N2IwZDUwMjM4MTU0MTkwY2EwYmQ3Mzk0MTI5OGZjMjU3ZGY0ZGMwMzQKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS5odHRwLnYxLjIuMHJjNi50bXBsKSA4MTFiMTRiZmZhYWI1ZWQwMzY1ZjAxMDZiYjVjZTVlNGVjMjIzODU2NTVlYTNhYzA0ZGUyYTM5YmQ5OTQ0ZjUxZTM3MTQ2MTlkYWU3Y2E0MzY2MmM5NTZiNTIxMjIyODg1OGYwNTkyNjcyYTI1NzlkNGE4Nzc2OTE4NmUyY2JmZQogICAgICAgICAgICBzZXQgaGFzaGVzKGY1Lmh0dHAudjEuMi4wcmM3LnRtcGwpIDIxZjQxMzM0MmU5YTdhMjgxYTBmMGUxMzAxZTc0NWFhODZhZjIxYTY5N2QyZTZmZGMyMWRkMjc5NzM0OTM2NjMxZTkyZjM0YmYxYzJkMjUwNGMyMDFmNTZjY2Q3NWM1YzEzYmFhMmZlNzY1MzIxMzY4OWVjM2M5ZTI3ZGZmNzdkCiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUuYXdzX2FkdmFuY2VkX2hhLnYxLjMuMHJjMS50bXBsKSA5ZTU1MTQ5YzAxMGMxZDM5NWFiZGFlM2MzZDJjYjgzZWMxM2QzMWVkMzk0MjQ2OTVlODg2ODBjZjNlZDVhMDEzZDYyNmIzMjY3MTFkM2Q0MGVmMmRmNDZiNzJkNDE0YjRjYjhlNGY0NDVlYTA3MzhkY2JkMjVjNGM4NDNhYzM5ZAogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LmF3c19hZHZhbmNlZF9oYS52MS40LjByYzEudG1wbCkgZGUwNjg0NTUyNTc0MTJhOTQ5ZjFlYWRjY2FlZTg1MDYzNDdlMDRmZDY5YmZiNjQ1MDAxYjc2ZjIwMDEyNzY2OGU0YTA2YmUyYmJiOTRlMTBmZWZjMjE1Y2ZjMzY2NWIwNzk0NWU2ZDczM2NiZTFhNGZhMWI4OGU4ODE1OTAzOTYKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS5hd3NfYWR2YW5jZWRfaGEudjEuNC4wcmMyLnRtcGwpIDZhYjBiZmZjNDI2ZGY3ZDMxOTEzZjlhNDc0YjFhMDc4NjA0MzVlMzY2YjA3ZDc3YjMyMDY0YWNmYjI5NTJjMWYyMDdiZWFlZDc3MDEzYTE1ZTQ0ZDgwZDc0ZjMyNTNlN2NmOWZiYmUxMmE5MGVjNzEyOGRlNmZhY2QwOTdkNjhmCiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUuYXdzX2FkdmFuY2VkX2hhLnYxLjQuMHJjMy50bXBsKSAyZjIzMzliNGJjM2EyM2M5Y2ZkNDJhYWUyYTZkZTM5YmEwNjU4MzY2ZjI1OTg1ZGUyZWE1MzQxMGE3NDVmMGYxOGVlZGM0OTFiMjBmNGE4ZGJhOGRiNDg5NzAwOTZlMmVmZGNhN2I4ZWZmZmExYTgzYTc4ZTVhYWRmMjE4YjEzNAogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LmF3c19hZHZhbmNlZF9oYS52MS40LjByYzQudG1wbCkgMjQxOGFjOGIxZjE4ODRjNWMwOTZjYmFjNmE5NGQ0MDU5YWFhZjA1OTI3YTZhNDUwOGZkMWYyNWI4Y2M2MDc3NDk4ODM5ZmJkZGE4MTc2ZDJjZjJkMjc0YTI3ZTZhMWRhZTJhMWUzYTBhOTk5MWJjNjVmYzc0ZmMwZDAyY2U5NjMKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS5hd3NfYWR2YW5jZWRfaGEudjEuNC4wcmM1LnRtcGwpIDVlNTgyMTg3YWUxYTYzMjNlMDk1ZDQxZWRkZDQxMTUxZDZiZDM4ZWI4M2M2MzQ0MTBkNDUyN2EzZDBlMjQ2YThmYzYyNjg1YWIwODQ5ZGUyYWRlNjJiMDI3NWY1MTI2NGQyZGVhY2NiYzE2Yjc3MzQxN2Y4NDdhNGExZWE5YmM0CiAgICAgICAgICAgIHNldCBoYXNoZXMoYXNtLXBvbGljeS50YXIuZ3opIDJkMzllYzYwZDAwNmQwNWQ4YTE1NjdhMWQ4YWFlNzIyNDE5ZThiMDYyYWQ3N2Q2ZDlhMzE2NTI5NzFlNWU2N2JjNDA0M2Q4MTY3MWJhMmE4YjEyZGQyMjllYTQ2ZDIwNTE0NGY3NTM3NGVkNGNhZTU4Y2VmYThmOWFiNjUzM2U2CiAgICAgICAgICAgIHNldCBoYXNoZXMoZGVwbG95X3dhZi5zaCkgMWEzYTNjNjI3NGFiMDhhN2RjMmNiNzNhZWRjOGQyYjJhMjNjZDllMGViMDZhMmUxNTM0YjM2MzJmMjUwZjFkODk3MDU2ZjIxOWQ1YjM1ZDNlZWQxMjA3MDI2ZTg5OTg5Zjc1NDg0MGZkOTI5NjljNTE1YWU0ZDgyOTIxNGZiNzQKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS5wb2xpY3lfY3JlYXRvci50bXBsKSAwNjUzOWUwOGQxMTVlZmFmZTU1YWE1MDdlY2I0ZTQ0M2U4M2JkYjFmNTgyNWE5NTE0OTU0ZWY2Y2E1NmQyNDBlZDAwYzdiNWQ2N2JkOGY2N2I4MTVlZTlkZDQ2NDUxOTg0NzAxZDA1OGM4OWRhZTI0MzRjODk3MTVkMzc1YTYyMAogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LnNlcnZpY2VfZGlzY292ZXJ5LnRtcGwpIDQ4MTFhOTUzNzJkMWRiZGJiNGY2MmY4YmNjNDhkNGJjOTE5ZmE0OTJjZGEwMTJjODFlM2EyZmU2M2Q3OTY2Y2MzNmJhODY3N2VkMDQ5YTgxNGE5MzA0NzMyMzRmMzAwZDNmOGJjZWQyYjBkYjYzMTc2ZDUyYWM5OTY0MGNlODFiCiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUuY2xvdWRfbG9nZ2VyLnYxLjAuMC50bXBsKSA2NGEwZWQzYjVlMzJhMDM3YmE0ZTcxZDQ2MDM4NWZlOGI1ZTFhZWNjMjdkYzBlODUxNGI1MTE4NjM5NTJlNDE5YTg5ZjRhMmE0MzMyNmFiYjU0M2JiYTliYzM0Mzc2YWZhMTE0Y2VkYTk1MGQyYzNiZDA4ZGFiNzM1ZmY1YWQyMAogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LWFwcHN2Y3MtMy41LjEtNS5ub2FyY2gucnBtKSBiYTcxYzZlMWM1MmQwYzcwNzdjZGIyNWE1ODcwOWI4ZmI3YzM3YjM0NDE4YTgzMzhiYmY2NzY2ODMzOTY3NmQyMDhjMWE0ZmVmNGU1NDcwYzE1MmFhYzg0MDIwYjRjY2I4MDc0Y2UzODdkZTI0YmUzMzk3MTEyNTZjMGZhNzhjOAogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LWFwcHN2Y3MtMy4xOC4wLTQubm9hcmNoLnJwbSkgZTcyZWU4MDA1YTI3MDcwYWMzOTlhYjA5N2U4YWE1MDdhNzJhYWU0NzIxZDc0OTE1ODljZmViODIxZGIzZWY4NmNiYzk3OWU3OTZhYjMxOWVjNzI3YmI1MTQwMGNjZGE4MTNjNGI5ZWI0YTZiM2QxMjIwYTM5NmI1ODJmOGY0MDAKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS1hcHBzdmNzLTMuMjAuMC0zLm5vYXJjaC5ycG0pIGQ0YmJhODg5MmEyMDY4YmI1M2Y4OGM2MDkwZGM2NWYxNzcwN2FiY2EzNWE3ZWQyZmZmMzk5ODAwNTdmZTdmN2EyZWJmNzEwYWIyMjg0YTFkODNkNzBiNzc0NmJlYWJhZDlkZjYwMzAxN2MwZmQ4NzI4Zjc0NTc2NjFjOTVhYzhkCiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUtYXBwc3Zjcy0zLjI1LjAtMy5ub2FyY2gucnBtKSAyNmYxOWJkYWFhODFjYmUwNDIxYjNlMDhjMDk5ODdmOWRkMGM1NGIwNWE2MjZkNmEyMWE4MzZiMzQyNDhkMmQ5ZDgzMDk1ZjBkYWFkOGU3YTRhMDY4ZTllZjk5Yjg5ZmJjZDI0NmFlOGI2MTdhYzJiMjQ1NjU5OTE1N2QwZThiMwogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LWNsb3VkLWZhaWxvdmVyLTEuMS4wLTAubm9hcmNoLnJwbSkgMTVhNDQwYzI5OWY5ZTRhZjg2YTNkMGY1YjBkNzViMDA1NDM4NWI5NWU0N2MzZWYxMTZkMmUwYmZiMDA0MWEyNmRjYmY1NDkwMjhlMmEyNmQyYzcxOGVjNjE0NDZiZDY1N2JlMzhmYmJjZDlkYjc4MWVmZTU0MTRjMTc0YWM2OGMKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS1jbG91ZC1mYWlsb3Zlci0xLjMuMC0wLm5vYXJjaC5ycG0pIDE5NjgxZWIzM2Q5ZjkxMGM5MTNmODE4MDE5OTQ4NWViNjUzYjRiNWViZWFhZTBiOTBhNmNlODM0MWQ3YTIyZmVkOGQyMTgxNWI1YmExNDhjNDY4ODUyZDIwY2MyNmZhZDRjNDI0MmU1MGVjYzE4NGYxZjg3NzBkYWNjZWQ2ZjZhCiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUtY2xvdWQtZmFpbG92ZXItMS40LjAtMC5ub2FyY2gucnBtKSA0OWU5MTA4YTA3MGUwYzg3MTNhZWI3YjMzMDY2MjM1ODU0MmU2MWI3YzUzYTlkNDUxMDhkMzdhOWJmNTI0NmY5ZTRhYWFlMTBjYzYxMDY0ODAxZGNjY2QyMGJmZDUxMDgzNDdiMGY2OTQ1MTBlN2VjZTA3Zjk2YzQ1YmE2ODNiMAogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LWNsb3VkLWZhaWxvdmVyLTEuNS4wLTAubm9hcmNoLnJwbSkgMzNhN2UyZDA0NzEwNmJjY2U2ODE3NTdhNjUyNDBiZmFjZWRkNDhlMTM1NjdlMDVmZGIyM2E0YjI2OWQyNjZhYTUwMDFmODExNThjMzk2NGRjMjk3ZjA0MjhkYjMxYzlkZjQyODAwMjg5OGQxOTAyODViMzQ5YzU5NDIyYTU3M2IKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS1jbG91ZC1mYWlsb3Zlci0xLjYuMS0xLm5vYXJjaC5ycG0pIGMxYjg0MmRhMjFiOGQxYmEyMWI2ZWI2M2M4NTk4YTllYTk5ODZkNWRhZGRjMjFlNGQyODBlMWQ2YjA5ZDNkYjFkZThhYzdkZTVjODRlZGYwN2I0M2U0YWYwM2RhZjhmZTc0N2E0MDQ4ZjY1NzNkOTU1MjA2MzUyY2RlMmNlYzY1CiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUtY2xvdWQtZmFpbG92ZXItMS43LjEtMS5ub2FyY2gucnBtKSAxNGZmMGNkMmJiNDk3ODBjYzBhZTMwMjFjNGZjOGZjYzA5NmUzZmNlMjI1ODA5NmE0YWEwMjZkNmQzN2RlNzI4Y2E3MzQ1YmZlM2E3OTAzMWUzMzZlNzRkMjVhMmI0MGZmMjgzMjRjMmM3NTJiZjBlZTcxYjdmYzg5YjZmYzhmZQoKICAgICAgICAgICAgc2V0IGZpbGVfcGF0aCBbbGluZGV4ICR0bXNoOjphcmd2IDFdCiAgICAgICAgICAgIHNldCBmaWxlX25hbWUgW2ZpbGUgdGFpbCAkZmlsZV9wYXRoXQoKICAgICAgICAgICAgaWYgeyFbaW5mbyBleGlzdHMgaGFzaGVzKCRmaWxlX25hbWUpXX0gewogICAgICAgICAgICAgICAgdG1zaDo6bG9nIGVyciAiTm8gaGFzaCBmb3VuZCBmb3IgJGZpbGVfbmFtZSIKICAgICAgICAgICAgICAgIGV4aXQgMQogICAgICAgICAgICB9CgogICAgICAgICAgICBzZXQgZXhwZWN0ZWRfaGFzaCAkaGFzaGVzKCRmaWxlX25hbWUpCiAgICAgICAgICAgIHNldCBjb21wdXRlZF9oYXNoIFtsaW5kZXggW2V4ZWMgL3Vzci9iaW4vb3BlbnNzbCBkZ3N0IC1yIC1zaGE1MTIgJGZpbGVfcGF0aF0gMF0KICAgICAgICAgICAgaWYgeyAkZXhwZWN0ZWRfaGFzaCBlcSAkY29tcHV0ZWRfaGFzaCB9IHsKICAgICAgICAgICAgICAgIGV4aXQgMAogICAgICAgICAgICB9CiAgICAgICAgICAgIHRtc2g6OmxvZyBlcnIgIkhhc2ggZG9lcyBub3QgbWF0Y2ggZm9yICRmaWxlX3BhdGgiCiAgICAgICAgICAgIGV4aXQgMQogICAgICAgIH1dfSB7CiAgICAgICAgICAgIHRtc2g6OmxvZyBlcnIge1VuZXhwZWN0ZWQgZXJyb3IgaW4gdmVyaWZ5SGFzaH0KICAgICAgICAgICAgZXhpdCAxCiAgICAgICAgfQogICAgfQogICAgc2NyaXB0LXNpZ25hdHVyZSBIcGl5bGZEa29rVWtob0FsSmlkb2psZ0ZHZVNWdXpvcHNoU0NpODQwZE40N2U1ZnYvYVliYXFXWDRLN2J5VmFQclc1d1JUMkFCbUtrR254Uy9iaHJLcFFRbTJKUXR2ZVVrMGduRmk0dXRQaFFtVGJGUEpKU2VRRy9EWXlSYS9WZmltWHlCdklMSjlkbUtWZ3ZSdENPdGlaN2FSbldMcXVRTFkwcll1UzdCemRkR3J3NWxWcEF4ZndwTHlwMFRhYWhQQVFjMDZRYjY0ZDdQU003N2Q0cy9pUTFBR0pGbU1iQ1FKR0hvS3d6V1JFYUZyRmlpOGU0YW95WjNkbVJGVElYa25LSjFtVkFuU2FRVEpyaHhoMzVZOE9CUVdHTmlTTkpMTXBnYktmRkNyNkVybksyV3J5aHJJdW1oc0I1Q2duR3pJdHQ4UmVwcFdiY0xuWTdPMTRkY2c9PQogICAgc2lnbmluZy1rZXkgL0NvbW1vbi9mNS1pcnVsZQp9Cg==\' | base64 -d > /config/verifyHash',
                                    'cat <<\'EOF\' > /config/waitThenRun.sh',
                                    '#!/bin/bash',
                                    'while true; do echo \"waiting for cloud libs install to complete\"',
                                    '    if [ -f /config/cloud/cloudLibsReady ]; then',
                                    '        break',
                                    '    else',
                                    '        sleep 10',
                                    '    fi',
                                    'done',
                                    '\"$@\"',
                                    'EOF',
                                    'cat <<\'EOF\' > /config/cloud/gce/run_autoscale_update.sh',
                                    '#!/bin/bash',
                                    'f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/autoscale.js --cloud gce --provider-options \'storageBucket:' + storageName + ',mgmtPort:' + str(context.properties['manGuiPort']) + ',serviceAccount:' + context.properties['serviceAccount'] + ',instanceGroup:' + deployment + '-igm\' --host localhost --port 8443 --user cluster_admin --password-url file:///config/cloud/gce/.adminPassword --password-encrypted --device-group autoscale-group --cluster-action update --log-level silly --output /var/log/cloud/google/autoscale.log',
                                    'EOF',
                                    'cat <<\'EOF\' > /config/cloud/gce/run_autoscale_backup.sh',
                                    '#!/bin/bash',
                                    'f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/autoscale.js --cloud gce --provider-options \'storageBucket:' + storageName + ',mgmtPort:' + str(context.properties['manGuiPort']) + ',serviceAccount:' + context.properties['serviceAccount'] + ',instanceGroup:' + deployment + '-igm\' --host localhost --port 8443 --user cluster_admin --password-url file:///config/cloud/gce/.adminPassword --password-encrypted --device-group autoscale-group --cluster-action backup-ucs --log-level silly --output /var/log/cloud/google/autoscale.log',
                                    'EOF',
                                    'cat <<\'EOF\' > /config/cloud/gce/custom-config.sh',
                                    '#!/bin/bash',
                                    'function wait_for_ready {',
                                    '   checks=0',
                                    '   ready_response=""',
                                    '   while [ $checks -lt 120 ] ; do',
                                    '      ready_response=$(curl -sku admin:$passwd -w "%{http_code}" -X GET  https://localhost:${mgmtGuiPort}/mgmt/shared/appsvcs/info -o /dev/null)',
                                    '      if [[ $ready_response == *200 ]]; then',
                                    '          echo "AS3 is ready"',
                                    '          break',
                                    '      else',
                                    '         echo "AS3" is not ready: $checks, response: $ready_response',
                                    '         let checks=checks+1',
                                    '         sleep 5',
                                    '      fi',
                                    '   done',
                                    '   if [[ $ready_response != *200 ]]; then',
                                    '      error_exit "$LINENO: AS3 was not installed correctly. Exit."',
                                    '   fi',
                                    '}',
                                    'date',
                                    'echo "starting custom-config.sh"',
                                    'tmsh save /sys config',
                                    'echo "Attempting to Join or Initiate Autoscale Cluster"',
                                    '(crontab -l 2>/dev/null; echo \'*/1 * * * * /config/cloud/gce/run_autoscale_update.sh\') | crontab -',
                                    '(crontab -l 2>/dev/null; echo \'59 23 * * * /config/cloud/gce/run_autoscale_backup.sh\') | crontab -',
                                    'f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/autoscale.js --cloud gce --provider-options \'storageBucket:' + storageName + ',mgmtPort:' + str(context.properties['manGuiPort']) + ',serviceAccount:' + context.properties['serviceAccount'] + ',instanceGroup:' + deployment + '-igm\' --host localhost --port 8443 --user cluster_admin --password-url file:///config/cloud/gce/.adminPassword --password-encrypted --device-group autoscale-group --block-sync -c join --log-level silly -o /var/log/cloud/google/autoscale.log',
                                    'if [ -f /config/cloud/master ];then',
                                    '  if $(jq \'.ucsLoaded\' < /config/cloud/master);then',
                                    '    echo "UCS backup loaded from backup folder in storage: ' + storageName + '."',
                                    '  else',
                                    '    echo "SELF-SELECTED as Primary ... Initiated Autoscale Cluster ... Loading default config"',
                                    '    tmsh modify cm device-group autoscale-group asm-sync enabled',
                                    '    source /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/waitForBigip.sh;wait-for-bigip',
                                    '                                                                   ',
                                    '    ### START CUSTOM CONFIGURATION:  Policy Name/Policy URL, etc. ',
                                    '    applicationDnsName="' + str(context.properties['applicationDnsName']) + '"',
                                    '    applicationPort="' + str(context.properties['applicationPort']) + '"',
                                    '    asm_policy="/config/cloud/asm-policy-linux-' + context.properties['policyLevel'] + '.xml"',
                                    '    manGuiPort="' + str(context.properties['manGuiPort']) + '"',
                                    '    passwd=$(f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/decryptDataFromFile.js --data-file /config/cloud/gce/.adminPassword)',
                                    '    deployed="no"',
                                    '    file_loc="/config/cloud/custom_config"',
                                    '    url_regex="(http:\/\/|https:\/\/)[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$"',
                                    '    if [[ ' + str(context.properties['declarationUrl']) + ' =~ $url_regex ]]; then',
                                    '       response_code=$(/usr/bin/curl -sk -w "%{http_code}" ' + str(context.properties['declarationUrl']) + ' -o $file_loc)',
                                    '       if [[ $response_code == 200 ]]; then',
                                    '           echo "Custom config download complete; checking for valid JSON."',
                                    '           cat $file_loc | jq .class',
                                    '           if [[ $? == 0 ]]; then',
                                    '               wait_for_ready',
                                    '               response_code=$(/usr/bin/curl -skvvu cluster_admin:$passwd -w "%{http_code}" -X POST -H "Content-Type: application/json" -H "Expect:" https://localhost:${manGuiPort}/mgmt/shared/appsvcs/declare -d @$file_loc -o /dev/null)',
                                    '           if [[ $response_code == *200 || $response_code == *502 ]]; then',
                                    '               echo "Deployment of custom application succeeded."',
                                    '               deployed="yes"',
                                    '           else',
                                    '               echo "Failed to deploy custom application; continuing..."',
                                    '           fi',
                                    '       else',
                                    '           echo "Custom config was not valid JSON, continuing..."',
                                    '       fi',
                                    '       else',
                                    '           echo "Failed to download custom config; continuing..."',
                                    '       fi',
                                    '   else',
                                    '      echo "Custom config was not a URL, continuing..."',
                                    '   fi',
                                    '   if [[ $deployed == "no" && ' + str(context.properties['declarationUrl']) + ' == "default" ]]; then',
                                    '      payload=\'{"class":"ADC","schemaVersion":"3.0.0","label":"autoscale_waf","id":"AUTOSCALE_WAF","remark":"Autoscale WAF","waf":{"class":"Tenant","Shared":{"class":"Application","template":"shared","serviceAddress":{"class":"Service_Address","virtualAddress":"0.0.0.0"},"policyWAF":{"class":"WAF_Policy","file":"/tmp/as30-linux-medium.xml"}},"http":{"class":"Application","template":"http","serviceMain":{"class":"Service_HTTP","virtualAddresses":[{"use":"/waf/Shared/serviceAddress"}],"snat":"auto","securityLogProfiles":[{"bigip":"/Common/Log illegal requests"}],"pool":"pool","policyWAF":{"use":"/waf/Shared/policyWAF"}},"pool":{"class":"Pool","monitors":["http"],"members":[{"autoPopulate":true,"hostname":"demo.example.com","servicePort":80,"addressDiscovery":"gce","updateInterval":15,"tagKey":"applicationPoolTagKey","tagValue":"applicationPoolTagValue","addressRealm":"private","region":""}]}}}}\'',
                                    '      payload=$(echo $payload | jq -c --arg asm_policy $asm_policy --arg pool_http_port $applicationPort --arg vs_http_port $applicationPort \'.waf.Shared.policyWAF.file = $asm_policy | .waf.http.pool.members[0].servicePort = ($pool_http_port | tonumber) | .waf.http.serviceMain.virtualPort = ($vs_http_port | tonumber)\')',
                                    '      payload=$(echo $payload | jq -c \'del(.waf.http.pool.members[0].updateInterval) | del(.waf.http.pool.members[0].tagKey) | del(.waf.http.pool.members[0].tagValue) | del(.waf.http.pool.members[0].addressRealm) | del(.waf.http.pool.members[0].region)\')',
                                    '      payload=$(echo $payload | jq -c --arg pool_member $applicationDnsName \'.waf.http.pool.members[0].hostname = $pool_member | .waf.http.pool.members[0].addressDiscovery = "fqdn"\')',
                                    '      response_code=$(/usr/bin/curl -skvvu cluster_admin:$passwd -w "%{http_code}" -X POST -H "Content-Type: application/json" -H "Expect:" https://localhost:${manGuiPort}/mgmt/shared/appsvcs/declare -d "$payload" -o /dev/null)',
                                    '      if [[ $response_code == 200 || $response_code == 502  ]]; then',
                                    '         echo "Deployment of application succeeded."',
                                    '      else',
                                    '         echo "Failed to deploy application"',
                                    '         exit 1',
                                    '      fi',
                                    '   fi',
                                    '    ### END CUSTOM CONFIGURATION',
                                    '    tmsh save /sys config',
                                    '    bigstart restart restnoded',
                                    '    f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/autoscale.js --cloud gce --provider-options \'storageBucket:' + storageName + ',mgmtPort:' + str(context.properties['manGuiPort']) + ',serviceAccount:' + context.properties['serviceAccount'] + ',instanceGroup:' + deployment + '-igm\' --host localhost --port 8443 --user cluster_admin --password-url file:///config/cloud/gce/.adminPassword --password-encrypted -c unblock-sync --log-level silly --output /var/log/cloud/google/autoscale.log',
                                    '  fi',
                                    'fi',
                                    'tmsh save /sys config',
                                    'date',
                                    'echo "custom-config.sh complete"',
                                    'EOF',
                                    'cat <<\'EOF\' > /config/cloud/gce/rm-password.sh',
                                    '#!/bin/bash',
                                    'date',
                                    'echo \'starting rm-password.sh\'',
                                    'rm /config/cloud/gce/.adminPassword',
                                    'date',
                                    'EOF',
                                    'checks=0',
                                    'while [ $checks -lt 12 ]; do echo checking downloads directory',
                                    '    if [ -d "/var/config/rest/downloads" ]; then',
                                    '        echo downloads directory ready',
                                    '        break',
                                    '    fi',
                                    '    echo downloads directory not ready yet',
                                    '    let checks=checks+1',
                                    '    sleep 10',
                                    'done',
                                    'if [ ! -d "/var/config/rest/downloads" ]; then',
                                    '    mkdir -p /var/config/rest/downloads',
                                    'fi',
                                    'curl -s -f --retry 20 -o /config/cloud/f5-cloud-libs.tar.gz https://cdn.f5.com/product/cloudsolutions/f5-cloud-libs/v4.24.0/f5-cloud-libs.tar.gz',
                                    'curl -s -f --retry 20 -o /config/cloud/f5-cloud-libs-gce.tar.gz https://cdn.f5.com/product/cloudsolutions/f5-cloud-libs-gce/v2.8.0/f5-cloud-libs-gce.tar.gz',
                                    'curl -s -f --retry 20 -o /var/config/rest/downloads/f5-appsvcs-3.25.0-3.noarch.rpm https://cdn.f5.com/product/cloudsolutions/f5-appsvcs-extension/v3.25.0/f5-appsvcs-3.25.0-3.noarch.rpm',
                                    'curl -s -f --retry 20 -o /config/cloud/asm-policy-linux.tar.gz http://cdn.f5.com/product/cloudsolutions/solution-scripts/asm-policy-linux.tar.gz',
                                    'chmod 755 /config/verifyHash',
                                    'chmod 755 /config/installCloudLibs.sh',
                                    'chmod 755 /config/waitThenRun.sh',
                                    'chmod 755 /config/cloud/gce/custom-config.sh',
                                    'chmod 755 /config/cloud/gce/rm-password.sh',
                                    'chmod 755 /config/cloud/gce/run_autoscale_update.sh',
                                    'chmod 755 /config/cloud/gce/run_autoscale_backup.sh',
                                    'mkdir -p /var/log/cloud/google',
                                    'nohup /config/installCloudLibs.sh &>> /var/log/cloud/google/install.log < /dev/null &',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/runScript.js --signal PASSWORD_CREATED --file f5-rest-node --cl-args \'/config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/generatePassword --file /config/cloud/gce/.adminPassword --encrypt\' --log-level silly -o /var/log/cloud/google/generatePassword.log &>> /var/log/cloud/google/install.log < /dev/null &',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/runScript.js --wait-for PASSWORD_CREATED --signal ADMIN_CREATED --file /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/createUser.sh --cl-args \'--user cluster_admin --password-file /config/cloud/gce/.adminPassword --password-encrypted\' --log-level silly -o /var/log/cloud/google/createUser.log &>> /var/log/cloud/google/install.log < /dev/null &',
                                    CUSTHASH,
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/onboard.js --port 8443 --ssl-port ' + str(context.properties['manGuiPort']) + ' --wait-for ADMIN_CREATED -o /var/log/cloud/google/onboard.log --log-level silly --no-reboot --install-ilx-package file:///var/config/rest/downloads/f5-appsvcs-3.25.0-3.noarch.rpm --host localhost --user cluster_admin --password-url file:///config/cloud/gce/.adminPassword --password-encrypted --hostname $(curl http://metadata.google.internal/computeMetadata/v1/instance/hostname -H "Metadata-Flavor: Google") --ntp 0.us.pool.ntp.org --ntp 1.us.pool.ntp.org --tz UTC ' + '--modules ' + PROVISIONING_MODULES + ' --db provision.1nicautoconfig:disable' + SENDANALYTICS + ' &>> /var/log/cloud/google/install.log < /dev/null &',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/runScript.js --file /config/cloud/gce/custom-config.sh --cwd /config/cloud/gce -o /var/log/cloud/google/custom-config.log --log-level silly --wait-for ONBOARD_DONE --signal CUSTOM_CONFIG_DONE &>> /var/log/cloud/google/install.log < /dev/null &',
                                    'touch /config/startupFinished',
                                    ])
                            )
                }]
        }
    return metadata
def GenerateConfig(context):
    # set variables
    import random
    ## set variables
    storageNumber = str(random.randint(10000, 99999))
    storageName = 'f5-bigip-' + context.env['deployment'] + '-' + storageNumber
    deployment = context.env['deployment']
    # build resources
    resources = [
        Storage(context,storageName),
        Instance(context,storageName,deployment),
        Igm(context,deployment),
        Autoscaler(context,deployment),
        HealthCheck(context,deployment),
        TargetPool(context,deployment),
        ForwardingRule(context,deployment),
        FirewallRuleSync(context),
        FirewallRuleApp(context),
        FirewallRuleMgmt(context),
    ]
    return {'resources': resources}