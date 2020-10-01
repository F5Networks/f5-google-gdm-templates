# Copyright 2019 F5 Networks All rights reserved.
#
# Version 3.8.0

"""Creates BIG-IP"""
COMPUTE_URL_BASE = 'https://www.googleapis.com/compute/v1/'


def FirewallRuleMgmt(context):
    # Build Management firewall rule
    source_list = str(context.properties['restrictedSrcAddress']).split()
    firewallRuleMgmt = {
        'name': 'mgmtfw-' + context.env['deployment'],
        'type': 'compute.v1.firewall',
        'properties': {
            'network': ''.join([COMPUTE_URL_BASE, 'projects/',
                                context.env['project'], '/global/networks/',
                                context.properties['mgmtNetwork']]),
            'sourceRanges': source_list,
            'targetTags': ['mgmtfw-' + context.env['deployment']],
            'allowed': [{
                "IPProtocol": "TCP",
                "ports": [str(context.properties['mgmtGuiPort']), '22'],
                },
            ]
        }
    }
    return firewallRuleMgmt

def FirewallRuleSync(context):
    # Build cluster sync firewall rule
    firewallRuleSync = {
        'name': 'syncfw-' + context.env['deployment'],
        'type': 'compute.v1.firewall',
        'properties': {
            'network': ''.join([COMPUTE_URL_BASE, 'projects/',
                                context.env['project'], '/global/networks/',
                                context.properties['network2']]),
            'targetTags': ['syncfw-'+ context.env['deployment']],
            'sourceTags': ['syncfw-'+ context.env['deployment']],
            'allowed': [{
                'IPProtocol': 'TCP',
                'ports': [4353]
                },{
                'IPProtocol': 'UDP',
                'ports': [1026],
                },{
                "IPProtocol": "TCP",
                "ports": ['6123-6128'],
                }
            ]
        }
    }
    return firewallRuleSync

def FirewallRuleApp(context):
    from collections import OrderedDict
    # Build Application firewall rule
    ports = '40000 ' + str(context.properties['applicationPort'])
    if int(context.properties['numberOfIntForwardingRules']) != 0:
      ports = ports + ' ' + str(context.properties['applicationIntPort'])
    ports = ports.split()
    ports = list(OrderedDict.fromkeys(ports))
    source_list = str(context.properties['restrictedSrcAddressApp'])
    if int(context.properties['numberOfIntForwardingRules']) != 0:
      source_list = source_list + ' ' + str(context.properties['restrictedSrcAddressIntApp'])
    source_list = source_list.split()
    source_list = list(OrderedDict.fromkeys(source_list))
    firewallRuleApp = {
        'name': 'appfw-' + context.env['deployment'],
        'type': 'compute.v1.firewall',
        'properties': {
            'network': ''.join([COMPUTE_URL_BASE, 'projects/',
                                context.env['project'], '/global/networks/',
                                context.properties['network1']]),
            'sourceRanges': source_list,
            'targetTags': ['appfw-'+ context.env['deployment']],
            'allowed': [{
                "IPProtocol": "TCP",
                "ports": ports,
                },
            ]
        }
    }
    return firewallRuleApp

def HealthCheck(context, source):
    # Build internal HA health check
    if source == "internal":
      healthCheck = {
          'name': context.env['deployment'] + '-' + source,
          'type': 'compute.v1.healthCheck',
          'properties': {
            'type': 'TCP',
            'tcpHealthCheck': {
              'port': 40000,
            }
          }
      }
    else:
      healthCheck = {
          'name': context.env['deployment'] + '-' + source,
          'type': 'compute.v1.httpHealthCheck',
          'properties': {
            'port': 40000,
          }
      }
  
    return healthCheck
  

def TargetPool(context, instanceName0, instanceName1):
    # Build lb target pool
    targetPool = {
        'name': context.env['deployment'] + '-tp',
        'type': 'compute.v1.targetPool',
        'properties': {
            'region': context.properties['region'],
            'sessionAffinity': 'CLIENT_IP',
            'instances': ['$(ref.' + instanceName0 + '.selfLink)','$(ref.' + instanceName1 + '.selfLink)'],
            'healthChecks': ['$(ref.' + context.env['deployment'] + '-external.selfLink)'],
        }
    }
    return targetPool

def ForwardingRule(context, name):
  # Build forwarding rule
  forwardingRule = {
        'name': name,
        'type': 'compute.v1.forwardingRule',
        'properties': {
            'region': context.properties['region'],
            'IPProtocol': 'TCP',
            'target': '$(ref.' + context.env['deployment'] + '-tp.selfLink)',
            'loadBalancingScheme': 'EXTERNAL',
        }
  }
  return forwardingRule

def IntForwardingRule(context, name, network1SharedVpc):
  # Build forwarding rule
  ports = str(context.properties['applicationIntPort']).split()
  intForwardingRule = {
        'name': name,
        'type': 'compute.v1.forwardingRule',
        'properties': {
            'description': 'Internal forwarding rule used for BIG-IP LB',
            'region': context.properties['region'],
            'IPProtocol': 'TCP',
            'ports': ports,
            'backendService': '$(ref.' + context.env['deployment'] + '-bes.selfLink)',
            'loadBalancingScheme': 'INTERNAL',
            'network': ''.join([COMPUTE_URL_BASE, 'projects/',
                                  network1SharedVpc, '/global/networks/',
                                  context.properties['network1']]),
            'subnetwork': ''.join([COMPUTE_URL_BASE, 'projects/',
                                  network1SharedVpc, '/regions/',
                                  context.properties['region'], '/subnetworks/',
                                  context.properties['subnet1']]),
        }
  }
  return intForwardingRule
def BackendService(context):
  backendService = {
    'name': context.env['deployment'] + '-bes',
    'type': 'compute.v1.regionBackendService',
    'properties': {
      'description': 'Backend service used for internal LB',
      "backends": [
        {
          "group": '$(ref.' + context.env['deployment'] + '-ig.selfLink)',
        }
      ],
      'healthChecks': ['$(ref.' + context.env['deployment'] + '-internal.selfLink)'],
      'sessionAffinity': 'CLIENT_IP',
      'loadBalancingScheme': 'INTERNAL',
      'protocol': 'TCP',
      'region': context.properties['region'],
    },
  }
  return backendService
def InstanceGroup(context, network1SharedVpc):
  instanceGroup = {
    'name': context.env['deployment'] + '-ig',
    'type': 'compute.v1.instanceGroup',
    'properties': {
      'description': 'Instance group used for internal LB',
      'network': ''.join([COMPUTE_URL_BASE, 'projects/',
                          network1SharedVpc, '/global/networks/',
                          context.properties['network1']]),
      'zone': context.properties['availabilityZone1'],
    },
  }
  return instanceGroup
def Instance(context, group, storageName, licenseType, device, network1SharedVpc):
  accessConfigExternal = []
  accessConfigMgmt = []
  tagItems = ['mgmtfw-' + context.env['deployment'], 'appfw-' + context.env['deployment'], 'syncfw-' + context.env['deployment']]
  provisionPublicIp = str(context.properties['provisionPublicIP']).lower()

  # access config and tags - conditional on provisionPublicIP parameter (yes/no)
  if provisionPublicIp in ['yes', 'true']:
    accessConfigExternal = [{
       'name': 'External NAT',
       'type': 'ONE_TO_ONE_NAT'
    }]
    accessConfigMgmt = [{
      'name': 'Management NAT',
      'type': 'ONE_TO_ONE_NAT'
    }]
  else:
    tagItems.append('no-ip')

  # Build instance template
  instance = {
        'zone': context.properties['availabilityZone1'],
        'canIpForward': True,
        'description': 'Clustered F5 BIG-IP configured with three interfaces.',
        'tags': {
          'items': tagItems
        },
        'hostname': ''.join(['bigip', device, '-', context.env['deployment'], '.c.', context.env['project'], '.internal']),
        'labels': {
          'f5_deployment': context.env['deployment']
        },
        'machineType': ''.join([COMPUTE_URL_BASE, 'projects/',
                         context.env['project'], '/zones/', context.properties['availabilityZone1'], '/machineTypes/',
                         context.properties['instanceType']]),
        'serviceAccounts': [{
            'email': str(context.properties['serviceAccount']),
            'scopes': ['https://www.googleapis.com/auth/compute','https://www.googleapis.com/auth/devstorage.read_write']
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
                            network1SharedVpc, '/global/networks/',
                            context.properties['network1']]),
            'subnetwork': ''.join([COMPUTE_URL_BASE, 'projects/',
                            network1SharedVpc, '/regions/',
                            context.properties['region'], '/subnetworks/',
                            context.properties['subnet1']]),
            'accessConfigs': accessConfigExternal
          },
          {
            'network': ''.join([COMPUTE_URL_BASE, 'projects/',
                            context.env['project'], '/global/networks/',
                            context.properties['mgmtNetwork']]),
            'subnetwork': ''.join([COMPUTE_URL_BASE, 'projects/',
                            context.env['project'], '/regions/',
                            context.properties['region'], '/subnetworks/',
                            context.properties['mgmtSubnet']]),
            'accessConfigs': accessConfigMgmt
          },
          {
              'network': ''.join([COMPUTE_URL_BASE, 'projects/',
                                  context.env['project'], '/global/networks/',
                                  context.properties['network2']]),
              'subnetwork': ''.join([COMPUTE_URL_BASE, 'projects/',
                                  context.env['project'], '/regions/',
                                  context.properties['region'], '/subnetworks/',
                                  context.properties['subnet2']]),
          }],
          'metadata': Metadata(context, group, storageName, licenseType)
    }
  return instance

def BuildTmsh(context, name, source):
  if source == "internal":
    tmsh = 'tmsh create ltm virtual ' + context.env['deployment'] + '-intfr' + name + '-monitor destination ${intfr' + name + '_RESPONSE}:40000 ip-protocol tcp description "Do Not delete, Used to monitor which HA pair is active"\n'
  else:
    tmsh = 'tmsh create ltm virtual ' + context.env['deployment'] + '-fr' + name + '-monitor destination ${fr' + name + '_RESPONSE}:40000 ip-protocol tcp profiles add { http } rules { monitor_respond_200 } description "Do Not delete, Used to monitor which HA pair is active"\n'
  return tmsh

def BuildVar(context, name, source):
  if source == "internal":
    ip = 'intfr' + name + '_RESPONSE=$(curl -s -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" https://www.googleapis.com/compute/v1/projects/' + context.env['project'] + '/regions/' + context.properties['region'] + '/forwardingRules/'+ context.env['deployment'] + '-intfr' + name + '|jq -r .IPAddress)\necho "Internal LB IP response: ${intfr' + name + '_RESPONSE}"\n'
  else:
    ip = 'fr' + name + '_RESPONSE=$(curl -s -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" https://www.googleapis.com/compute/v1/projects/' + context.env['project'] + '/regions/' + context.properties['region'] + '/forwardingRules/'+ context.env['deployment'] + '-fr' + name + '|jq -r .IPAddress)\necho "External LB IP response: ${fr' + name + '_RESPONSE}"\n'
  return ip

  

def Metadata(context,group, storageName, licenseType):

  # SETUP VARIABLES
  ## Template Analytics
  ALLOWUSAGEANALYTICS = str(context.properties['allowUsageAnalytics']).lower()
  if ALLOWUSAGEANALYTICS in ['yes', 'true']:
      CUSTHASH = 'CUSTOMERID=`curl -s "http://metadata.google.internal/computeMetadata/v1/project/numeric-project-id" -H "Metadata-Flavor: Google" |sha512sum|cut -d " " -f 1`;\nDEPLOYMENTID=`curl -s "http://metadata.google.internal/computeMetadata/v1/instance/id" -H "Metadata-Flavor: Google"|sha512sum|cut -d " " -f 1`;'
      SENDANALYTICS = ' --metrics "cloudName:google,region:' + context.properties['region'] + ',bigipVersion:' + context.properties['imageName'] + ',customerId:${CUSTOMERID},deploymentId:${DEPLOYMENTID},templateName:f5-existing-stack-same-net-cluster-byol-3nic-bigip.py,templateVersion:3.8.0,licenseType:byol"'
  else:
      CUSTHASH = '# No template analytics'
      SENDANALYTICS = ''

  ## Phone home
  ALLOWPHONEHOME = str(context.properties['allowPhoneHome']).lower()
  if ALLOWPHONEHOME in ['yes', 'true']:
      PHONEHOME = '"tmsh modify sys software update auto-phonehome enabled"'
  else:
      PHONEHOME = '"tmsh modify sys software update auto-phonehome disabled"'

  ## ntp servers
  ntp_servers = str(context.properties['ntpServer']).split()
  ntp_list = ''
  for ntp_server in ntp_servers:
      ntp_list = ntp_list + ' --ntp ' + ntp_server
  timezone = ' --tz UTC'
  if context.properties['timezone']:
      timezone = " --tz {0}".format(str(context.properties['timezone']))


  ## Onboard
  if group == "create" and licenseType == "byol":
      LICENSE = ' --license ' + context.properties['licenseKey1']
  elif group == "join" and licenseType == "byol":
      LICENSE = ' --license ' + context.properties['licenseKey2']
  else:
      LICENSE = ''

  # Provisioning modules
  PROVISIONING_MODULES = ','.join(context.properties['bigIpModules'].split('-'))

  ## Cluster
  if group == "create":
      CLUSTERJS = ' '.join(["nohup /config/waitThenRun.sh",
                        "f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/cluster.js",
                        "-o /var/log/cloud/google/cluster.log",
                        "--log-level " + str(context.properties['logLevel']),
                        "--host localhost",
                        "--wait-for CUSTOM_CONFIG_DONE",
                        "--signal CLUSTER_DONE",
                        "--user admin",
                        "--password-url file:///config/cloud/gce/.adminPassword",
                        "--password-encrypted",
                        "--cloud gce",
                        "--provider-options 'region:" + context.properties['region'] + ",storageBucket:" + storageName  + "'",
                        "--primary",
                        "--config-sync-ip ${INT2ADDRESS}",
                        "--create-group",
                        "--device-group failover_group",
                        "--sync-type sync-failover",
                        "--network-failover",
                        "--device ${HOSTNAME}",
                        "--auto-sync",
                        "--no-reboot",
                        "2>&1 >> /var/log/cloud/google/install.log < /dev/null &"
      ])
      SYNC = ''
  elif group == "join":
      CLUSTERJS = ' '.join(["nohup /config/waitThenRun.sh",
                        "f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/cluster.js",
                        "-o /var/log/cloud/google/cluster.log",
                        "--log-level " + str(context.properties['logLevel']),
                        "--host localhost",
                        "--wait-for CUSTOM_CONFIG_DONE",
                        "--signal CLUSTER_DONE",
                        "--user admin",
                        "--password-url file:///config/cloud/gce/.adminPassword",
                        "--password-encrypted",
                        "--cloud gce",
                        "--provider-options 'region:" + context.properties['region'] + ",storageBucket:" + storageName  + "'",
                        "--config-sync-ip ${INT2ADDRESS}",
                        "--join-group",
                        "--device-group failover_group",
                        "--remote-host ",
                        "$(ref.bigip1-" + context.env['deployment'] + ".networkInterfaces[1].networkIP)",
                        "--no-reboot",
                        "2>&1 >> /var/log/cloud/google/install.log < /dev/null &"
             ])
      SYNC = 'tmsh modify cm device-group failover_group devices modify { $HOSTNAME { set-sync-leader } }'
  else:
      CLUSTERJS = ''
      SYNC = ''

  # Build Monitors
  monitoring_intvs = ''
  monitoring_extvs = ''
  monitoring_intvar = ''
  monitoring_extvar = ''
  for i in range(int(context.properties['numberOfIntForwardingRules'])):
    monitoring_intvs = monitoring_intvs + BuildTmsh(context, str(i), "internal")
    monitoring_intvar = monitoring_intvar + BuildVar(context, str(i), "internal")
  for i in range(int(context.properties['numberOfForwardingRules'])):
    monitoring_extvs = monitoring_extvs + BuildTmsh(context, str(i), "external")
    monitoring_extvar = monitoring_extvar + BuildVar(context, str(i), "external")
  monitoring_extvs = 'tmsh load sys config merge file /tmp/monitor_irule\n' + monitoring_extvs

  ## generate metadata
  metadata = {
              'items': [{
                  'key': 'startup-script',
                  'value': ('\n'.join(['#!/bin/bash',
                                    'if [ -f /config/startupFinished ]; then',
                                    '    exit',
                                    'fi',
                                    'if [ ! -f /config/cloud/gce/FIRST_BOOT_COMPLETE ]; then',
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
                                    'declare -a filesToVerify=(\"/config/cloud/f5-cloud-libs.tar.gz\" \"/config/cloud/f5-cloud-libs-gce.tar.gz\" \"/config/cloud/f5-appsvcs-3.20.0-3.noarch.rpm\")',
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
                                    'touch /config/cloud/cloudLibsReady',
                                    'EOF',
                                    'echo \'Y2xpIHNjcmlwdCAvQ29tbW9uL3ZlcmlmeUhhc2ggewpwcm9jIHNjcmlwdDo6cnVuIHt9IHsKICAgICAgICBpZiB7W2NhdGNoIHsKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS1jbG91ZC1saWJzLnRhci5neikgZTY4OGNiMTUzNDE2YWJjODVkYTA4MWRkMDlkMmRkNGZkNDMzYzI5ZjE5N2ZkOTI3YzEyYWZhOWUwZDQ0Njk5MjgwYjQ4YTJhZTkzZjE5MzYxZGQwYzNjZGI3MjgyMzIwNWVkMDM3ZWYwYTEwZjdjZmJlZjA5ZjM5OWFhNjIwYzgKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS1jbG91ZC1saWJzLWF3cy50YXIuZ3opIGZlZmE3NmZmZTllMmMzNmQzYjM2YjEyZjdjNWE1MWYxZmI4MjY1MjIxZDAwMGFmYWZkMTEzYWYwN2NiZGEzMDcxN2JkYTAzYjI2YzllMTBjNjM2MzQ0YTczNWU3ZWU1OWQ4ZGUxNzJjNmI5NzBiY2MyNGUxNjFjZGYwMWQzNTRmCiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUtY2xvdWQtbGlicy1henVyZS50YXIuZ3opIGZhMGQyN2QyY2Q2OWY5NjVkY2RjMGRkNzliYjg1YmFhZDQ3Njg2YWYxOWEyMDEzZGIyZWU3ZmI0ODZhMGNjYmQxMDcyYzNhMzRlZjQ1NTNjMjhmZTczODc2NjVlMzY1NTcxMzRjZjZkNGUyMjFmMjM5MmYwYjExZWFmOWJjYmFmCiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUtY2xvdWQtbGlicy1nY2UudGFyLmd6KSBlOGY5MzVhNzBhZmYwZGJkMTliODk2N2M0ZWEzNWNhODAyN2ZmNTY1N2Q5Mjk5MjNhY2E5NzEzOTQzNzBhMjY5ZjRjYmI5NjBkZDUwNmFiZDM0YTM2ZDgyZGUwYjM0NDJlMmY2M2MwNzljNTNjZjFmMGYwMjNkYTExMDMwOWNiNgogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LWNsb3VkLWxpYnMtb3BlbnN0YWNrLnRhci5neikgNWM4M2ZlNmE5M2E2ZmNlYjVhMmU4NDM3YjVlZDhjYzlmYWY0YzE2MjFiZmM5ZTZhMDc3OWY2YzIxMzdiNDVlYWI4YWUwZTdlZDc0NWM4Y2Y4MjFiOTM3MTI0NWNhMjk3NDljYTBiN2U1NjYzOTQ5ZDc3NDk2Yjg3MjhmNGIwZjkKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS1jbG91ZC1saWJzLWNvbnN1bC50YXIuZ3opIGEzMmFhYjM5NzA3M2RmOTJjYmJiYTUwNjdlNTgyM2U5YjVmYWZjYTg2MmEyNThiNjBiNmI0MGFhMDk3NWMzOTg5ZDFlMTEwZjcwNjE3N2IyZmZiZTRkZGU2NTMwNWEyNjBhNTg1NjU5NGNlN2FkNGVmMGM0N2I2OTRhZTRhNTEzCiAgICAgICAgICAgIHNldCBoYXNoZXMoYXNtLXBvbGljeS1saW51eC50YXIuZ3opIDYzYjVjMmE1MWNhMDljNDNiZDg5YWYzNzczYmJhYjg3YzcxYTZlN2Y2YWQ5NDEwYjIyOWI0ZTBhMWM0ODNkNDZmMWE5ZmZmMzlkOTk0NDA0MWIwMmVlOTI2MDcyNDAyNzQxNGRlNTkyZTk5ZjRjMjQ3NTQxNTMyM2UxOGE3MmUwCiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUuaHR0cC52MS4yLjByYzQudG1wbCkgNDdjMTlhODNlYmZjN2JkMWU5ZTljMzVmMzQyNDk0NWVmODY5NGFhNDM3ZWVkZDE3YjZhMzg3Nzg4ZDRkYjEzOTZmZWZlNDQ1MTk5YjQ5NzA2NGQ3Njk2N2IwZDUwMjM4MTU0MTkwY2EwYmQ3Mzk0MTI5OGZjMjU3ZGY0ZGMwMzQKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS5odHRwLnYxLjIuMHJjNi50bXBsKSA4MTFiMTRiZmZhYWI1ZWQwMzY1ZjAxMDZiYjVjZTVlNGVjMjIzODU2NTVlYTNhYzA0ZGUyYTM5YmQ5OTQ0ZjUxZTM3MTQ2MTlkYWU3Y2E0MzY2MmM5NTZiNTIxMjIyODg1OGYwNTkyNjcyYTI1NzlkNGE4Nzc2OTE4NmUyY2JmZQogICAgICAgICAgICBzZXQgaGFzaGVzKGY1Lmh0dHAudjEuMi4wcmM3LnRtcGwpIDIxZjQxMzM0MmU5YTdhMjgxYTBmMGUxMzAxZTc0NWFhODZhZjIxYTY5N2QyZTZmZGMyMWRkMjc5NzM0OTM2NjMxZTkyZjM0YmYxYzJkMjUwNGMyMDFmNTZjY2Q3NWM1YzEzYmFhMmZlNzY1MzIxMzY4OWVjM2M5ZTI3ZGZmNzdkCiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUuYXdzX2FkdmFuY2VkX2hhLnYxLjMuMHJjMS50bXBsKSA5ZTU1MTQ5YzAxMGMxZDM5NWFiZGFlM2MzZDJjYjgzZWMxM2QzMWVkMzk0MjQ2OTVlODg2ODBjZjNlZDVhMDEzZDYyNmIzMjY3MTFkM2Q0MGVmMmRmNDZiNzJkNDE0YjRjYjhlNGY0NDVlYTA3MzhkY2JkMjVjNGM4NDNhYzM5ZAogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LmF3c19hZHZhbmNlZF9oYS52MS40LjByYzEudG1wbCkgZGUwNjg0NTUyNTc0MTJhOTQ5ZjFlYWRjY2FlZTg1MDYzNDdlMDRmZDY5YmZiNjQ1MDAxYjc2ZjIwMDEyNzY2OGU0YTA2YmUyYmJiOTRlMTBmZWZjMjE1Y2ZjMzY2NWIwNzk0NWU2ZDczM2NiZTFhNGZhMWI4OGU4ODE1OTAzOTYKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS5hd3NfYWR2YW5jZWRfaGEudjEuNC4wcmMyLnRtcGwpIDZhYjBiZmZjNDI2ZGY3ZDMxOTEzZjlhNDc0YjFhMDc4NjA0MzVlMzY2YjA3ZDc3YjMyMDY0YWNmYjI5NTJjMWYyMDdiZWFlZDc3MDEzYTE1ZTQ0ZDgwZDc0ZjMyNTNlN2NmOWZiYmUxMmE5MGVjNzEyOGRlNmZhY2QwOTdkNjhmCiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUuYXdzX2FkdmFuY2VkX2hhLnYxLjQuMHJjMy50bXBsKSAyZjIzMzliNGJjM2EyM2M5Y2ZkNDJhYWUyYTZkZTM5YmEwNjU4MzY2ZjI1OTg1ZGUyZWE1MzQxMGE3NDVmMGYxOGVlZGM0OTFiMjBmNGE4ZGJhOGRiNDg5NzAwOTZlMmVmZGNhN2I4ZWZmZmExYTgzYTc4ZTVhYWRmMjE4YjEzNAogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LmF3c19hZHZhbmNlZF9oYS52MS40LjByYzQudG1wbCkgMjQxOGFjOGIxZjE4ODRjNWMwOTZjYmFjNmE5NGQ0MDU5YWFhZjA1OTI3YTZhNDUwOGZkMWYyNWI4Y2M2MDc3NDk4ODM5ZmJkZGE4MTc2ZDJjZjJkMjc0YTI3ZTZhMWRhZTJhMWUzYTBhOTk5MWJjNjVmYzc0ZmMwZDAyY2U5NjMKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS5hd3NfYWR2YW5jZWRfaGEudjEuNC4wcmM1LnRtcGwpIDVlNTgyMTg3YWUxYTYzMjNlMDk1ZDQxZWRkZDQxMTUxZDZiZDM4ZWI4M2M2MzQ0MTBkNDUyN2EzZDBlMjQ2YThmYzYyNjg1YWIwODQ5ZGUyYWRlNjJiMDI3NWY1MTI2NGQyZGVhY2NiYzE2Yjc3MzQxN2Y4NDdhNGExZWE5YmM0CiAgICAgICAgICAgIHNldCBoYXNoZXMoYXNtLXBvbGljeS50YXIuZ3opIDJkMzllYzYwZDAwNmQwNWQ4YTE1NjdhMWQ4YWFlNzIyNDE5ZThiMDYyYWQ3N2Q2ZDlhMzE2NTI5NzFlNWU2N2JjNDA0M2Q4MTY3MWJhMmE4YjEyZGQyMjllYTQ2ZDIwNTE0NGY3NTM3NGVkNGNhZTU4Y2VmYThmOWFiNjUzM2U2CiAgICAgICAgICAgIHNldCBoYXNoZXMoZGVwbG95X3dhZi5zaCkgMWEzYTNjNjI3NGFiMDhhN2RjMmNiNzNhZWRjOGQyYjJhMjNjZDllMGViMDZhMmUxNTM0YjM2MzJmMjUwZjFkODk3MDU2ZjIxOWQ1YjM1ZDNlZWQxMjA3MDI2ZTg5OTg5Zjc1NDg0MGZkOTI5NjljNTE1YWU0ZDgyOTIxNGZiNzQKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS5wb2xpY3lfY3JlYXRvci50bXBsKSAwNjUzOWUwOGQxMTVlZmFmZTU1YWE1MDdlY2I0ZTQ0M2U4M2JkYjFmNTgyNWE5NTE0OTU0ZWY2Y2E1NmQyNDBlZDAwYzdiNWQ2N2JkOGY2N2I4MTVlZTlkZDQ2NDUxOTg0NzAxZDA1OGM4OWRhZTI0MzRjODk3MTVkMzc1YTYyMAogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LnNlcnZpY2VfZGlzY292ZXJ5LnRtcGwpIDQ4MTFhOTUzNzJkMWRiZGJiNGY2MmY4YmNjNDhkNGJjOTE5ZmE0OTJjZGEwMTJjODFlM2EyZmU2M2Q3OTY2Y2MzNmJhODY3N2VkMDQ5YTgxNGE5MzA0NzMyMzRmMzAwZDNmOGJjZWQyYjBkYjYzMTc2ZDUyYWM5OTY0MGNlODFiCiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUuY2xvdWRfbG9nZ2VyLnYxLjAuMC50bXBsKSA2NGEwZWQzYjVlMzJhMDM3YmE0ZTcxZDQ2MDM4NWZlOGI1ZTFhZWNjMjdkYzBlODUxNGI1MTE4NjM5NTJlNDE5YTg5ZjRhMmE0MzMyNmFiYjU0M2JiYTliYzM0Mzc2YWZhMTE0Y2VkYTk1MGQyYzNiZDA4ZGFiNzM1ZmY1YWQyMAogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LWFwcHN2Y3MtMy41LjEtNS5ub2FyY2gucnBtKSBiYTcxYzZlMWM1MmQwYzcwNzdjZGIyNWE1ODcwOWI4ZmI3YzM3YjM0NDE4YTgzMzhiYmY2NzY2ODMzOTY3NmQyMDhjMWE0ZmVmNGU1NDcwYzE1MmFhYzg0MDIwYjRjY2I4MDc0Y2UzODdkZTI0YmUzMzk3MTEyNTZjMGZhNzhjOAogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LWFwcHN2Y3MtMy4xOC4wLTQubm9hcmNoLnJwbSkgZTcyZWU4MDA1YTI3MDcwYWMzOTlhYjA5N2U4YWE1MDdhNzJhYWU0NzIxZDc0OTE1ODljZmViODIxZGIzZWY4NmNiYzk3OWU3OTZhYjMxOWVjNzI3YmI1MTQwMGNjZGE4MTNjNGI5ZWI0YTZiM2QxMjIwYTM5NmI1ODJmOGY0MDAKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS1hcHBzdmNzLTMuMjAuMC0zLm5vYXJjaC5ycG0pIGQ0YmJhODg5MmEyMDY4YmI1M2Y4OGM2MDkwZGM2NWYxNzcwN2FiY2EzNWE3ZWQyZmZmMzk5ODAwNTdmZTdmN2EyZWJmNzEwYWIyMjg0YTFkODNkNzBiNzc0NmJlYWJhZDlkZjYwMzAxN2MwZmQ4NzI4Zjc0NTc2NjFjOTVhYzhkCiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUtY2xvdWQtZmFpbG92ZXItMS4xLjAtMC5ub2FyY2gucnBtKSAxNWE0NDBjMjk5ZjllNGFmODZhM2QwZjViMGQ3NWIwMDU0Mzg1Yjk1ZTQ3YzNlZjExNmQyZTBiZmIwMDQxYTI2ZGNiZjU0OTAyOGUyYTI2ZDJjNzE4ZWM2MTQ0NmJkNjU3YmUzOGZiYmNkOWRiNzgxZWZlNTQxNGMxNzRhYzY4YwogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LWNsb3VkLWZhaWxvdmVyLTEuMy4wLTAubm9hcmNoLnJwbSkgMTk2ODFlYjMzZDlmOTEwYzkxM2Y4MTgwMTk5NDg1ZWI2NTNiNGI1ZWJlYWFlMGI5MGE2Y2U4MzQxZDdhMjJmZWQ4ZDIxODE1YjViYTE0OGM0Njg4NTJkMjBjYzI2ZmFkNGM0MjQyZTUwZWNjMTg0ZjFmODc3MGRhY2NlZDZmNmEKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS1jbG91ZC1mYWlsb3Zlci0xLjQuMC0wLm5vYXJjaC5ycG0pIDQ5ZTkxMDhhMDcwZTBjODcxM2FlYjdiMzMwNjYyMzU4NTQyZTYxYjdjNTNhOWQ0NTEwOGQzN2E5YmY1MjQ2ZjllNGFhYWUxMGNjNjEwNjQ4MDFkY2NjZDIwYmZkNTEwODM0N2IwZjY5NDUxMGU3ZWNlMDdmOTZjNDViYTY4M2IwCiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUtY2xvdWQtZmFpbG92ZXItMS41LjAtMC5ub2FyY2gucnBtKSAzM2E3ZTJkMDQ3MTA2YmNjZTY4MTc1N2E2NTI0MGJmYWNlZGQ0OGUxMzU2N2UwNWZkYjIzYTRiMjY5ZDI2NmFhNTAwMWY4MTE1OGMzOTY0ZGMyOTdmMDQyOGRiMzFjOWRmNDI4MDAyODk4ZDE5MDI4NWIzNDljNTk0MjJhNTczYgoKICAgICAgICAgICAgc2V0IGZpbGVfcGF0aCBbbGluZGV4ICR0bXNoOjphcmd2IDFdCiAgICAgICAgICAgIHNldCBmaWxlX25hbWUgW2ZpbGUgdGFpbCAkZmlsZV9wYXRoXQoKICAgICAgICAgICAgaWYgeyFbaW5mbyBleGlzdHMgaGFzaGVzKCRmaWxlX25hbWUpXX0gewogICAgICAgICAgICAgICAgdG1zaDo6bG9nIGVyciAiTm8gaGFzaCBmb3VuZCBmb3IgJGZpbGVfbmFtZSIKICAgICAgICAgICAgICAgIGV4aXQgMQogICAgICAgICAgICB9CgogICAgICAgICAgICBzZXQgZXhwZWN0ZWRfaGFzaCAkaGFzaGVzKCRmaWxlX25hbWUpCiAgICAgICAgICAgIHNldCBjb21wdXRlZF9oYXNoIFtsaW5kZXggW2V4ZWMgL3Vzci9iaW4vb3BlbnNzbCBkZ3N0IC1yIC1zaGE1MTIgJGZpbGVfcGF0aF0gMF0KICAgICAgICAgICAgaWYgeyAkZXhwZWN0ZWRfaGFzaCBlcSAkY29tcHV0ZWRfaGFzaCB9IHsKICAgICAgICAgICAgICAgIGV4aXQgMAogICAgICAgICAgICB9CiAgICAgICAgICAgIHRtc2g6OmxvZyBlcnIgIkhhc2ggZG9lcyBub3QgbWF0Y2ggZm9yICRmaWxlX3BhdGgiCiAgICAgICAgICAgIGV4aXQgMQogICAgICAgIH1dfSB7CiAgICAgICAgICAgIHRtc2g6OmxvZyBlcnIge1VuZXhwZWN0ZWQgZXJyb3IgaW4gdmVyaWZ5SGFzaH0KICAgICAgICAgICAgZXhpdCAxCiAgICAgICAgfQogICAgfQogICAgc2NyaXB0LXNpZ25hdHVyZSBuTTU0bmxndTZwQzlCMUpmc0JWdHQ2Zm5ReGZyWXExV1kvZ1F4NmFqMmJQTVZ6MzlpT0RqekdQZTM5bitucllqSlZCVi9kaE1URmRCRkltU0JGOWRxVGRnUHR0RXFhMHRRVUNxTXFnVWRyMTUrT1FoaUo0ZEo4dmZJTm96dkxidTBkTGhvV2VwYmcwRXI3c0o2cjVtdjhXVlg2WDFUMkRuUG50OTJyZVRMMVhHQWVZL3BjK1BzYlowSzYrZ3NKOGdlZDVjQmJQYU5ZY01LdUh3N2xWbE9nWHVUdXFJQzRwbi80Tmo2NW1WNmt0MFF1QUVObVl5WU5laXc3bWlKWFVpd2NZSEkyTVN4bG11Z2laV3FPLzlyeTBEZllnYk8wTEs1b01yajVRSjJRSWRUZldSem55dFM5Y3Qwd0VLQjJmNU1DRzlaQ1B3R3NORDlOVmpsTzBzY2c9PQogICAgc2lnbmluZy1rZXkgL0NvbW1vbi9mNS1pcnVsZQp9Cg==\' | base64 -d > /config/verifyHash',
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
                                    'cat <<\'EOF\' > /config/cloud/gce/collect-interface.sh',
                                    '#!/bin/bash',
                                    'COMPUTE_BASE_URL=\"http://metadata.google.internal/computeMetadata/v1\"',
                                    'echo "MGMTADDRESS=$(curl -s -f --retry 20 \'http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/1/ip\' -H \'Metadata-Flavor: Google\')" >> /config/cloud/gce/interface.config',
                                    'echo "MGMTMASK=$(curl -s -f --retry 20 \'http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/1/subnetmask\' -H \'Metadata-Flavor: Google\')" >> /config/cloud/gce/interface.config',
                                    'echo "MGMTGATEWAY=$(curl -s -f --retry 20 \'http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/1/gateway\' -H \'Metadata-Flavor: Google\')" >> /config/cloud/gce/interface.config',
                                    'echo "INT1ADDRESS=$(curl -s -f --retry 20 \'http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/ip\' -H \'Metadata-Flavor: Google\')" >> /config/cloud/gce/interface.config',
                                    'echo "INT1MASK=$(curl -s -f --retry 20 \'http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/subnetmask\' -H \'Metadata-Flavor: Google\')" >> /config/cloud/gce/interface.config',
                                    'echo "INT1GATEWAY=$(curl -s -f --retry 20 \'http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/gateway\' -H \'Metadata-Flavor: Google\')" >> /config/cloud/gce/interface.config',
                                    'echo "INT2ADDRESS=$(curl -s -f --retry 20 \'http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/2/ip\' -H \'Metadata-Flavor: Google\')" >> /config/cloud/gce/interface.config',
                                    'echo "INT2MASK=$(curl -s -f --retry 20 \'http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/2/subnetmask\' -H \'Metadata-Flavor: Google\')" >> /config/cloud/gce/interface.config',
                                    'echo "INT2GATEWAY=$(curl -s -f --retry 20 \'http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/2/gateway\' -H \'Metadata-Flavor: Google\')" >> /config/cloud/gce/interface.config',
                                    'echo "HOSTNAME=$(curl -s -f --retry 10 \"${COMPUTE_BASE_URL}/instance/hostname\" -H \'Metadata-Flavor: Google\')" >> /config/cloud/gce/interface.config',
                                    'CONFIG_FILE=\'/config/cloud/.deployment\'',
                                    'echo \'{"tagKey":"f5_deployment","tagValue":"' + context.env['deployment'] + '"}\' > $CONFIG_FILE',
                                    'CLOUD_LIBS_DIR=\'/config/cloud/gce/node_modules/@f5devcentral\'',
                                    'chmod 755 /config/cloud/gce/interface.config',
                                    'reboot',
                                    'EOF',
                                    'cat <<\'EOF\' > /config/cloud/gce/custom-config.sh',
                                    '#!/bin/bash',
                                    'source /usr/lib/bigstart/bigip-ready-functions',
                                    'wait_bigip_ready',
                                    'source /config/cloud/gce/interface.config',
                                    'MGMTNETWORK=$(/bin/ipcalc -n ${MGMTADDRESS} ${MGMTMASK} | cut -d= -f2)',
                                    'INT1NETWORK=$(/bin/ipcalc -n ${INT1ADDRESS} ${INT1MASK} | cut -d= -f2)',
                                    'INT2NETWORK=$(/bin/ipcalc -n ${INT2ADDRESS} ${INT2MASK} | cut -d= -f2)',
                                    'PROGNAME=$(basename $0)',
                                    'function error_exit {',
                                    'echo \"${PROGNAME}: ${1:-\\\"Unknown Error\\\"}\" 1>&2',
                                    'exit 1',
                                    '}',
                                    'function wait_for_ready {',
                                    '   app=$1',
                                    '   checks=0',
                                    '   ready_response=""',
                                    '   checks_max=120',
                                    '   while [ $checks -lt $checks_max ] ; do',
                                    '      ready_response=$(curl -sku admin:$passwd -w "%{http_code}" -X GET  https://localhost:${mgmtGuiPort}/mgmt/shared/${app}/info -o /dev/null)',
                                    '      if [[ $ready_response == *200 ]]; then',
                                    '          echo "${app} is ready"',
                                    '          break',
                                    '      else',
                                    '         echo "${app}" is not ready: $checks, response: $ready_response',
                                    '         let checks=checks+1',
                                    '         if [[ $checks == $((checks_max/2)) ]]; then',
                                    '             echo "restarting restnoded"'
                                    '             bigstart restart restnoded',
                                    '         fi',
                                    '         sleep 15',
                                    '      fi',
                                    '   done',
                                    '   if [[ $ready_response != *200 ]]; then',
                                    '      error_exit "$LINENO: ${app} was not installed correctly. Exit."',
                                    '   fi',
                                    '}',
                                    'date',
                                    'declare -a tmsh=()',
                                    'echo \'starting custom-config.sh\'',
                                    'wait_bigip_ready',
                                    'tmsh+=(',
                                    PHONEHOME,
                                    '"tmsh modify sys global-settings mgmt-dhcp disabled"',
                                    '"tmsh delete sys management-route all"',
                                    '"tmsh delete sys management-ip all"',
                                    '"tmsh create sys management-ip ${MGMTADDRESS}/32"',
                                    '"tmsh create sys management-route mgmt_gw network ${MGMTGATEWAY}/32 type interface"',
                                    '"tmsh create sys management-route mgmt_net network ${MGMTNETWORK}/${MGMTMASK} gateway ${MGMTGATEWAY}"',
                                    '"tmsh create sys management-route default gateway ${MGMTGATEWAY}"',
                                    '"tmsh create net vlan external interfaces add { 1.0 } mtu 1460"',
                                    '"tmsh create net self self_external address ${INT1ADDRESS}/32 vlan external"',
                                    '"tmsh create net route ext_gw_interface network ${INT1GATEWAY}/32 interface external"',
                                    '"tmsh create net route ext_rt network ${INT1NETWORK}/${INT1MASK} gw ${INT1GATEWAY}"',
                                    '"tmsh create net route default gw ${INT1GATEWAY}"',
                                    '"tmsh create net vlan internal interfaces add { 1.2 } mtu 1460"',
                                    '"tmsh create net self self_internal address ${INT2ADDRESS}/32 vlan internal allow-service add { tcp:4353 udp:1026 }"',
                                    '"tmsh create net route int_gw_interface network ${INT2GATEWAY}/32 interface internal"',
                                    '"tmsh create net route int_rt network ${INT2NETWORK}/${INT2MASK} gw ${INT2GATEWAY}"',
                                    '"tmsh modify cm device ${HOSTNAME} unicast-address { { effective-ip ${INT2ADDRESS} effective-port 1026 ip ${INT2ADDRESS} } }"',
                                    '"tmsh modify sys global-settings remote-host add { metadata.google.internal { hostname metadata.google.internal addr 169.254.169.254 } }"',
                                    '"tmsh modify sys db failover.selinuxallowscripts value enable"',
                                    '"tmsh modify sys management-dhcp sys-mgmt-dhcp-config request-options delete { ntp-servers }"',
                                    '\'tmsh save /sys config\'',
                                    ')',
                                    'for CMD in "${tmsh[@]}"',
                                    'do',
                                    '    if $CMD;then',
                                    '        echo \"command $CMD successfully executed."',
                                    '    else',
                                    '        error_exit "$LINENO: An error has occurred while executing $CMD. Aborting!"',
                                    '    fi',
                                    'done',
                                    '  wait_bigip_ready',
                                    'echo "Adding System to instance Group"',
                                    'TOKEN=$(curl "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token" -H "Metadata-Flavor: Google"|cut -d \'"\' -f4)',
                                    'IG_RESPONSE=$(curl -X POST -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" https://www.googleapis.com/compute/v1/projects/' + context.env['project'] + '/zones/' + context.properties['availabilityZone1'] + '/instanceGroups/' + context.env['deployment'] + '-ig/addInstances -d \'{ "instances": [{ "instance": "projects/' + context.env['project'] + '/zones/' + context.properties['availabilityZone1'] + '/instances/bigip1-' + context.env['deployment'] + '" },{ "instance": "projects/' + context.env['project'] + '/zones/' + context.properties['availabilityZone1'] + '/instances/bigip2-' + context.env['deployment'] + '" }] }\')',
                                    'echo "Instance Group Response:$IG_RESPONSE"',
                                    'echo "Locating lb addressess"',
                                    monitoring_intvar,
                                    monitoring_extvar,
                                    monitoring_intvs,
                                    monitoring_extvs,
                                    '  date',
                                    '  ### START CUSTOM CONFIGURATION',
                                    '  mgmtGuiPort="' + str(context.properties['mgmtGuiPort']) + '"',
                                    '  passwd=$(f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/decryptDataFromFile.js --data-file /config/cloud/gce/.adminPassword)',
                                    '  file_loc="/config/cloud/custom_config"',
                                    '  url_regex="(http:\/\/|https:\/\/)[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$"',
                                    '  if [[ ' + str(context.properties['declarationUrl']) + ' =~ $url_regex ]]; then',
                                    '     response_code=$(/usr/bin/curl -sk -w "%{http_code}" ' + str(context.properties['declarationUrl']) + ' -o $file_loc)',
                                    '     if [[ $response_code == 200 ]]; then',
                                    '         echo "Custom config download complete; checking for valid JSON."',
                                    '         cat $file_loc | jq .class',
                                    '         if [[ $? == 0 ]]; then',
                                    '             wait_for_ready appsvcs',
                                    '             response_code=$(/usr/bin/curl --retry 10 -skvvu admin:$passwd -w "%{http_code}" -X POST -H "Content-Type: application/json" https://localhost:${mgmtGuiPort}/mgmt/shared/appsvcs/declare -d @$file_loc -o /dev/null)',
                                    '             if [[ $response_code == *200 || $response_code == *502 ]]; then',
                                    '                 echo "Deployment of custom application succeeded."',
                                    '             else',
                                    '                 echo "Failed to deploy custom application; continuing..."',
                                    '             fi',
                                    '         else',
                                    '             echo "Custom config was not valid JSON, continuing..."',
                                    '         fi',
                                    '     else',
                                    '         echo "Failed to download custom config; continuing..."',
                                    '     fi',
                                    '  else',
                                    '     echo "Custom config was not a URL, continuing..."',
                                    '  fi',
                                    '### END CUSTOM CONFIGURATION',
                                    'EOF',
                                    'cat <<\'EOF\' > /config/cloud/gce/custom-config2.sh',
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
                                    'source /config/cloud/gce/interface.config',
                                    'tmsh delete sys management-ip all',
                                    'tmsh create sys management-ip ${MGMTADDRESS}/32',
                                    'tmsh save sys config',
                                    'EOF',
                                    'cat <<\'EOF\' > /config/cloud/gce/rm-password.sh',
                                    '#!/bin/bash',
                                    'date',
                                    'source /config/cloud/gce/interface.config',
                                    'echo \'starting rm-password.sh\'',
                                    SYNC,
                                    'rm /config/cloud/gce/.adminPassword',
                                    'tmsh save /sys config',
                                    'date',
                                    'EOF',
                                    'cat <<\'EOF\' > /tmp/monitor_irule',
                                    'ltm rule monitor_respond_200 {',
                                    'when HTTP_REQUEST {',
                                    '    HTTP::respond 200 System Responding',
                                    '}',
                                    '}',
                                    'EOF',
                                    'curl -s -f --retry 20 -o /config/cloud/f5-cloud-libs.tar.gz https://cdn.f5.com/product/cloudsolutions/f5-cloud-libs/v4.22.0/f5-cloud-libs.tar.gz',
                                    'curl -s -f --retry 20 -o /config/cloud/f5-cloud-libs-gce.tar.gz https://cdn.f5.com/product/cloudsolutions/f5-cloud-libs-gce/v2.6.0/f5-cloud-libs-gce.tar.gz',
                                    'curl -s -f --retry 20 -o /config/cloud/f5-appsvcs-3.20.0-3.noarch.rpm https://cdn.f5.com/product/cloudsolutions/f5-appsvcs-extension/v3.20.0/f5-appsvcs-3.20.0-3.noarch.rpm',
                                    'chmod 755 /config/verifyHash',
                                    'chmod 755 /config/installCloudLibs.sh',
                                    'chmod 755 /config/waitThenRun.sh',
                                    'chmod 755 /config/cloud/gce/collect-interface.sh',
                                    'chmod 755 /config/cloud/gce/custom-config.sh',
                                    'chmod 755 /config/cloud/gce/custom-config2.sh',
                                    'chmod 755 /config/cloud/gce/rm-password.sh',
                                    'chmod 755 /tmp/monitor_irule',
                                    'mkdir -p /var/log/cloud/google',
                                    CUSTHASH,
                                    'touch /config/cloud/gce/FIRST_BOOT_COMPLETE',
                                    'nohup /usr/bin/setdb provision.1nicautoconfig disable &>> /var/log/cloud/google/install.log < /dev/null &',
                                    'nohup /usr/bin/setdb provision.extramb 500 &>> /var/log/cloud/google/install.log < /dev/null &',
                                    'nohup /usr/bin/setdb restjavad.useextramb true &>> /var/log/cloud/google/install.log < /dev/null &',
                                    'nohup /config/installCloudLibs.sh &>> /var/log/cloud/google/install.log < /dev/null &',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/runScript.js --file f5-rest-node --cl-args \'/config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/generatePassword --file /config/cloud/gce/.adminPassword --encrypt\' --signal GENERATE_PASSWORD_DONE --log-level ' + str(context.properties['logLevel']) + ' --output /var/log/cloud/google/generatePassword.log 2>&1 >> /var/log/cloud/google/install.log < /dev/null &',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/runScript.js --file /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/createUser.sh --cl-args \'--user admin --password-file /config/cloud/gce/.adminPassword --password-encrypted\' --signal CREATE_USER_DONE --wait-for GENERATE_PASSWORD_DONE --log-level ' + str(context.properties['logLevel']) + ' --output /var/log/cloud/google/createUser.log 2>&1 >> /var/log/cloud/google/install.log < /dev/null &',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/onboard.js --db provision.managementeth:eth1 --host localhost ' + LICENSE + ' -o /var/log/cloud/google/mgmt-swap.log --log-level ' + str(context.properties['logLevel']) + ' --wait-for CREATE_USER_DONE --signal MGMT_SWAP_DONE >> /var/log/cloud/google/install.log < /dev/null &',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/runScript.js --file /config/cloud/gce/collect-interface.sh --cwd /config/cloud/gce -o /var/log/cloud/google/interface-config.log --wait-for MGMT_SWAP_DONE --log-level ' + str(context.properties['logLevel']) + ' >> /var/log/cloud/google/install.log < /dev/null &',
                                    'elif [ ! -f /config/cloud/gce/SECOND_BOOT_COMPLETE ]; then',
                                    'source /config/cloud/gce/interface.config',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/onboard.js -o /var/log/cloud/google/onboard.log --log-level ' + str(context.properties['logLevel']) + ' --signal ONBOARD_DONE --install-ilx-package file:///config/cloud/f5-appsvcs-3.20.0-3.noarch.rpm --host localhost --no-reboot --user admin --password-url file:///config/cloud/gce/.adminPassword --password-encrypted --port 443 --ssl-port ' + str(context.properties['mgmtGuiPort']) + ' --hostname $HOSTNAME ' + ntp_list + timezone + ' --modules ' + PROVISIONING_MODULES + SENDANALYTICS + ' 2>&1 >> /var/log/cloud/google/install.log < /dev/null &',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/runScript.js --file /config/cloud/gce/custom-config.sh --cwd /config/cloud/gce --wait-for ONBOARD_DONE --signal CUSTOM_CONFIG_DONE --log-level ' + str(context.properties['logLevel']) + ' -o /var/log/cloud/google/custom-config.log 2>&1 >> /var/log/cloud/google/install.log < /dev/null &',
                                    CLUSTERJS,
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/runScript.js --file /config/cloud/gce/rm-password.sh --cwd /config/cloud/gce -o /var/log/cloud/google/rm-password.log --wait-for CLUSTER_DONE --signal RM_PASSWORD_DONE --log-level ' + str(context.properties['logLevel']) + ' 2>&1 >> /var/log/cloud/google/install.log < /dev/null &',
                                    'touch /config/cloud/gce/SECOND_BOOT_COMPLETE',
                                    'else',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/runScript.js --file /config/cloud/gce/custom-config2.sh --cwd /config/cloud/gce -o /var/log/cloud/google/custom-config2.log --signal CUSTOM_CONFIG2_DONE --log-level ' + str(context.properties['logLevel']) + ' >> /var/log/cloud/google/install.log < /dev/null &',
                                    'touch /config/startupFinished',
                                    'fi'
                                    ])
                            )
                }]
    }
  return metadata

def Outputs(context):
    output_ip_options = {
        'public': '.accessConfigs[0].natIP',
        'private': '.networkIP'
    }
    pub_or_priv = 'public' if str(context.properties['provisionPublicIP']).lower() in ['yes', 'true'] else 'private'

    outputs = [{
        'name': 'region',
        'value': context.properties['region']
    },
    {
        'name': 'mgmtURL1',
        'value': 'https://$(ref.bigip1-' + context.env['deployment'] + '.networkInterfaces[1]' + output_ip_options[pub_or_priv] + '):' + str(context.properties['mgmtGuiPort'])
    },
    {
        'name': 'mgmtURL2',
        'value': 'https://$(ref.bigip2-' + context.env['deployment'] + '.networkInterfaces[1]' + output_ip_options[pub_or_priv] + '):' + str(context.properties['mgmtGuiPort'])
    }]
    return outputs

def ForwardingRuleOutputs(context, numberPostfix):
    forwardingRuleOutputs = {
        'name': 'appTrafficAddress' + numberPostfix,
        'value': '$(ref.' + context.env['deployment'] + '-fr' + numberPostfix + '.IPAddress)'
    }
    return forwardingRuleOutputs

def GenerateConfig(context):

  ## set variables
  # Set project names for networks
  network1SharedVpc = context.env['project']
  if str(context.properties['network1SharedVpc']).lower() != 'none':
      network1SharedVpc = context.properties['network1SharedVpc']
  storageName = 'f5-bigip-storage-' + context.env['deployment']
  instanceName0 = 'bigip1-' + context.env['deployment']
  instanceName1 = 'bigip2-' + context.env['deployment']
  forwardingRules = []
  forwardingRuleOutputs = []
  for i in list(range(int(context.properties['numberOfForwardingRules']))):
    forwardingRules = forwardingRules + [ForwardingRule(context, context.env['deployment'] + '-fr' + str(i))]
    forwardingRuleOutputs = forwardingRuleOutputs + [ForwardingRuleOutputs(context, str(i))]
  if context.properties['numberOfIntForwardingRules'] != 0:
    intForwardingRules = []
    for i in list(range(int(context.properties['numberOfIntForwardingRules']))):
      intForwardingRules = intForwardingRules + [IntForwardingRule(context, context.env['deployment'] + '-intfr' + str(i), network1SharedVpc)]
    internalResources = [InstanceGroup(context, network1SharedVpc)]
    internalResources = internalResources + [BackendService(context)]
    internalResources = internalResources + [HealthCheck(context, "internal")]
  else:
    internalResources = []
    intForwardingRules = []
  # build resources
  resources = [
  FirewallRuleMgmt(context),
  FirewallRuleSync(context),
  TargetPool(context,instanceName0,instanceName1),
  HealthCheck(context, "external"),
  {
    'name': instanceName0,
    'type': 'compute.v1.instance',
    'properties': Instance(context, 'create', storageName, 'byol', '1', network1SharedVpc)
  },{
    'name': instanceName1,
    'type': 'compute.v1.instance',
    'properties': Instance(context, 'join', storageName, 'byol', '2', network1SharedVpc)
  },{
    'name': storageName,
    'type': 'storage.v1.bucket',
    'properties': {
      'project': context.env['project'],
      'name': storageName,
    },
  }]
  if network1SharedVpc == context.env['project']:
    resources = resources + [FirewallRuleApp(context)]
  # add internal lb resources when not equal to 0
  resources = resources + internalResources
  # add forwarding rules
  resources = resources + forwardingRules
  resources = resources + intForwardingRules
  outputs = Outputs(context)
  outputs = outputs + forwardingRuleOutputs
  return {'resources': resources, 'outputs': outputs}