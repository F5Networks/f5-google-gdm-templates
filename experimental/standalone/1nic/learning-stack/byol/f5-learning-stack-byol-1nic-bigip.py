# Copyright 2022 F5 Networks All rights reserved.
#
# Version 3.17.0

"""Creates BIG-IP"""
COMPUTE_URL_BASE = 'https://www.googleapis.com/compute/v1/'

def GenerateConfig(context):
  ALLOWUSAGEANALYTICS = context.properties['allowUsageAnalytics']
  if ALLOWUSAGEANALYTICS == "yes":
      CUSTHASH = 'CUSTOMERID=`curl -s "http://metadata.google.internal/computeMetadata/v1/project/numeric-project-id" -H "Metadata-Flavor: Google" |sha512sum|cut -d " " -f 1`;DEPLOYMENTID=`curl -s "http://metadata.google.internal/computeMetadata/v1/instance/id" -H "Metadata-Flavor: Google"|sha512sum|cut -d " " -f 1`;'
      SENDANALYTICS = ' --metrics "cloudName:google,region:' + context.properties['availabilityZone1'] + ',bigipVersion:13-0-0-2-3-1671,customerId:${CUSTOMERID},deploymentId:${DEPLOYMENTID},templateName:f5-full-stack-byol-1nic-bigip.py-rc1,templateVersion:v1.1.0,licenseType:byol"'
  else:
      CUSTHASH = ''
      SENDANALYTICS = ''

  # Provisioning modules
  PROVISIONING_MODULES = ','.join(context.properties['bigIpModules'].split('-'))

  resources = [{
      'name': 'net-' + context.env['deployment'],
      'type': 'compute.v1.network',
      'properties': {
          'IPv4Range': '10.0.0.1/24'
      }
  }, {
      'name': 'firewall-' + context.env['deployment'],
      'type': 'compute.v1.firewall',
      'properties': {
          'network': '$(ref.net-' + context.env['deployment'] + '.selfLink)',
          'sourceRanges': ['0.0.0.0/0'],
          'allowed': [{
              'IPProtocol': 'TCP',
              'ports': [80,22,443,8443]
          }]
      }
  }, {
      'name': 'webserver-' + context.env['deployment'],
      'type': 'compute.v1.instance',
      'properties': {
          'zone': context.properties['availabilityZone1'],
          'machineType': ''.join([COMPUTE_URL_BASE, 'projects/',
                                  context.env['project'], '/zones/',
                                  context.properties['availabilityZone1'], '/machineTypes/',
                                  context.properties['instanceType']]),
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
              'network': '$(ref.net-' + context.env['deployment']
                         + '.selfLink)',
              'accessConfigs': [{
                  'name': 'External NAT',
                  'type': 'ONE_TO_ONE_NAT'
              }]
          }],
          'metadata': {
              'items': [{
                  'key': 'startup-script',
                  'value': ''.join(['#!/bin/bash',
                                    'INSTANCE=$(curl http://metadata.google.',
                                    'internal/computeMetadata/v1/instance/',
                                    'hostname -H "Metadata-Flavor: Google")',
                                    'echo "<html><header><title>Hello from ',
                                    'Deployment Manager!</title></header>',
                                    '<body><h2>Hello from $INSTANCE</h2><p>',
                                    'Google Deployment Manager and F5 bids you good day!</p>',
                                    '</body></html>" > index.html',
                                    'sudo python -m SimpleHTTPServer 80'])
              }]
          }
      }
  }, {
      'name': 'bigip1-' + context.env['deployment'],
      'type': 'compute.v1.instance',
      'properties': {
          'zone': context.properties['availabilityZone1'],
          'machineType': ''.join([COMPUTE_URL_BASE, 'projects/',
                                  context.env['project'], '/zones/',
                                  context.properties['availabilityZone1'], '/machineTypes/',
                                  context.properties['instanceType']]),
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
              'network': '$(ref.net-' + context.env['deployment'] + '.selfLink)',
              'accessConfigs': [{
                  'name': 'External NAT',
                  'type': 'ONE_TO_ONE_NAT'
              }]
          }],
          'metadata': {
              'items': [{
                  'key': 'startup-script',
                  'value': ('\n'.join(['#!/bin/bash',
                                    'if [ -f /config/startupFinished ]; then',
                                    '    exit',
                                    'fi',
                                    'mkdir -p /config/cloud/gce',
                                    '### START CUSTOM PACKAGE CONFIGURATION',
                                    'cat << \'EOF\' >> /config/cloud/runtime-init-config.yaml',
                                    'controls:',
                                    '  logLevel: info',
                                    '  logFilename: /var/log/cloud/bigIpRuntimeInit.log',
                                    'extension_packages:',
                                    '  install_operations:',
                                    '    - extensionType: as3',
                                    '      extensionVersion: 3.34.0',
                                    '      extensionHash: 05a80ec0848dc5b8876b78a8fbee2980d5a1671d635655b3af604dc830d5fed4',
                                    'EOF',
                                    '### END CUSTOM PACKAGE CONFIGURATION',
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
                                    'declare -a filesToVerify=(\"/config/cloud/f5-cloud-libs.tar.gz\")',
                                    'for fileToVerify in \"${filesToVerify[@]}\"',
                                    'do',
                                    '    echo verifying \"$fileToVerify\"',
                                    '    if ! tmsh run cli script verifyHash \"$fileToVerify\"; then',
                                    '        echo \"$fileToVerify\" is not valid',
                                    '        exit 1',
                                    '    fi',
                                    '    echo verified \"$fileToVerify\"',
                                    'done',
                                    'mkdir -p /config/cloud/gce/node_modules',
                                    'echo expanding f5-cloud-libs.tar.gz',
                                    'tar xvfz /config/cloud/f5-cloud-libs.tar.gz -C /config/cloud/gce/node_modules',
                                    'echo expanding f5-cloud-libs-gce.tar.gz',
                                    'tar xvfz /config/cloud/f5-cloud-libs-gce.tar.gz -C /config/cloud/gce/node_modules/f5-cloud-libs/node_modules',
                                    'touch /config/cloud/cloudLibsReady',
                                    'EOF',
                                    'echo \'Y2xpIHNjcmlwdCAvQ29tbW9uL3ZlcmlmeUhhc2ggewpwcm9jIHNjcmlwdDo6cnVuIHt9IHsKICAgICAgICBpZiB7W2NhdGNoIHsKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS1jbG91ZC1saWJzLnRhci5neikgODVkMGI4MmQzNjVlNDg3NDkzYmM2Mjg2Zjg4YzNiY2ViNzllYjA0NWEzNmVkNzJiY2IwZjBiYWUwY2VlNDkwYzU3ZGM4ZTNkZWVlNmMzZjNiMGMwMTBlMTkwNWM3NzAxZmQ0OTkxNDYyODdjZDUwZTM3MDJlYTBkYzZmNmRiOWQKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS1jbG91ZC1saWJzLWF3cy50YXIuZ3opIGMyZWFkZjA0YTkxMGUyOGE1MmMyMWUxYjlhZjkwMTViNWE0ZTVhNTA1MDFiYzBkZmJkMzU0ZDAzZDA4ZDVhODJmZThjMDMyNmRkNDEzOGI4MzVmZjg4ZmMxNzIzMmU5NTdiOGYyZDNmYjAzMWVkMTgwOWZkM2QwYjk3M2FmZTA5CiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUtY2xvdWQtbGlicy1henVyZS50YXIuZ3opIDcwM2JhZTBlNzc0MTE0YjE2NTI4Y2E3MWJiMjEwOWRiNWYzNjYyM2Y4Yjg2OTg1ODgzNDg2Nzc4NjJmZmE0ODU1OWJhOTY5ODAwMWQyZjI0NTg2MDA1OWE0ZmVjNTg4YTE1ZWU5MjQzMTdiOTY3YmYzMzhjY2E2NmIwZGU2OTM2CiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUtY2xvdWQtbGlicy1nY2UudGFyLmd6KSBmZDE2YWI4MjdiMzA4OWU3NmQ1Yzc3YzcxM2EyZWFiZTY4NTcwN2RiYTcyMDdjZmRmMjc3OGRiMmU5NjI4MWZjOGUzZTQ0MjRmYjIwZjU4NGM0NGNiOTcyMmI0ZmJmMzUyZTdjMzY0ZGU1ZmVkNjFhNzRiZDEzOGY5NzQ3MDViMgogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LWNsb3VkLWxpYnMtb3BlbnN0YWNrLnRhci5neikgNWM4M2ZlNmE5M2E2ZmNlYjVhMmU4NDM3YjVlZDhjYzlmYWY0YzE2MjFiZmM5ZTZhMDc3OWY2YzIxMzdiNDVlYWI4YWUwZTdlZDc0NWM4Y2Y4MjFiOTM3MTI0NWNhMjk3NDljYTBiN2U1NjYzOTQ5ZDc3NDk2Yjg3MjhmNGIwZjkKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS1jbG91ZC1saWJzLWNvbnN1bC50YXIuZ3opIGEzMmFhYjM5NzA3M2RmOTJjYmJiYTUwNjdlNTgyM2U5YjVmYWZjYTg2MmEyNThiNjBiNmI0MGFhMDk3NWMzOTg5ZDFlMTEwZjcwNjE3N2IyZmZiZTRkZGU2NTMwNWEyNjBhNTg1NjU5NGNlN2FkNGVmMGM0N2I2OTRhZTRhNTEzCiAgICAgICAgICAgIHNldCBoYXNoZXMoYXNtLXBvbGljeS1saW51eC50YXIuZ3opIDYzYjVjMmE1MWNhMDljNDNiZDg5YWYzNzczYmJhYjg3YzcxYTZlN2Y2YWQ5NDEwYjIyOWI0ZTBhMWM0ODNkNDZmMWE5ZmZmMzlkOTk0NDA0MWIwMmVlOTI2MDcyNDAyNzQxNGRlNTkyZTk5ZjRjMjQ3NTQxNTMyM2UxOGE3MmUwCiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUuaHR0cC52MS4yLjByYzQudG1wbCkgNDdjMTlhODNlYmZjN2JkMWU5ZTljMzVmMzQyNDk0NWVmODY5NGFhNDM3ZWVkZDE3YjZhMzg3Nzg4ZDRkYjEzOTZmZWZlNDQ1MTk5YjQ5NzA2NGQ3Njk2N2IwZDUwMjM4MTU0MTkwY2EwYmQ3Mzk0MTI5OGZjMjU3ZGY0ZGMwMzQKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS5odHRwLnYxLjIuMHJjNi50bXBsKSA4MTFiMTRiZmZhYWI1ZWQwMzY1ZjAxMDZiYjVjZTVlNGVjMjIzODU2NTVlYTNhYzA0ZGUyYTM5YmQ5OTQ0ZjUxZTM3MTQ2MTlkYWU3Y2E0MzY2MmM5NTZiNTIxMjIyODg1OGYwNTkyNjcyYTI1NzlkNGE4Nzc2OTE4NmUyY2JmZQogICAgICAgICAgICBzZXQgaGFzaGVzKGY1Lmh0dHAudjEuMi4wcmM3LnRtcGwpIDIxZjQxMzM0MmU5YTdhMjgxYTBmMGUxMzAxZTc0NWFhODZhZjIxYTY5N2QyZTZmZGMyMWRkMjc5NzM0OTM2NjMxZTkyZjM0YmYxYzJkMjUwNGMyMDFmNTZjY2Q3NWM1YzEzYmFhMmZlNzY1MzIxMzY4OWVjM2M5ZTI3ZGZmNzdkCiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUuYXdzX2FkdmFuY2VkX2hhLnYxLjMuMHJjMS50bXBsKSA5ZTU1MTQ5YzAxMGMxZDM5NWFiZGFlM2MzZDJjYjgzZWMxM2QzMWVkMzk0MjQ2OTVlODg2ODBjZjNlZDVhMDEzZDYyNmIzMjY3MTFkM2Q0MGVmMmRmNDZiNzJkNDE0YjRjYjhlNGY0NDVlYTA3MzhkY2JkMjVjNGM4NDNhYzM5ZAogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LmF3c19hZHZhbmNlZF9oYS52MS40LjByYzEudG1wbCkgZGUwNjg0NTUyNTc0MTJhOTQ5ZjFlYWRjY2FlZTg1MDYzNDdlMDRmZDY5YmZiNjQ1MDAxYjc2ZjIwMDEyNzY2OGU0YTA2YmUyYmJiOTRlMTBmZWZjMjE1Y2ZjMzY2NWIwNzk0NWU2ZDczM2NiZTFhNGZhMWI4OGU4ODE1OTAzOTYKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS5hd3NfYWR2YW5jZWRfaGEudjEuNC4wcmMyLnRtcGwpIDZhYjBiZmZjNDI2ZGY3ZDMxOTEzZjlhNDc0YjFhMDc4NjA0MzVlMzY2YjA3ZDc3YjMyMDY0YWNmYjI5NTJjMWYyMDdiZWFlZDc3MDEzYTE1ZTQ0ZDgwZDc0ZjMyNTNlN2NmOWZiYmUxMmE5MGVjNzEyOGRlNmZhY2QwOTdkNjhmCiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUuYXdzX2FkdmFuY2VkX2hhLnYxLjQuMHJjMy50bXBsKSAyZjIzMzliNGJjM2EyM2M5Y2ZkNDJhYWUyYTZkZTM5YmEwNjU4MzY2ZjI1OTg1ZGUyZWE1MzQxMGE3NDVmMGYxOGVlZGM0OTFiMjBmNGE4ZGJhOGRiNDg5NzAwOTZlMmVmZGNhN2I4ZWZmZmExYTgzYTc4ZTVhYWRmMjE4YjEzNAogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LmF3c19hZHZhbmNlZF9oYS52MS40LjByYzQudG1wbCkgMjQxOGFjOGIxZjE4ODRjNWMwOTZjYmFjNmE5NGQ0MDU5YWFhZjA1OTI3YTZhNDUwOGZkMWYyNWI4Y2M2MDc3NDk4ODM5ZmJkZGE4MTc2ZDJjZjJkMjc0YTI3ZTZhMWRhZTJhMWUzYTBhOTk5MWJjNjVmYzc0ZmMwZDAyY2U5NjMKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS5hd3NfYWR2YW5jZWRfaGEudjEuNC4wcmM1LnRtcGwpIDVlNTgyMTg3YWUxYTYzMjNlMDk1ZDQxZWRkZDQxMTUxZDZiZDM4ZWI4M2M2MzQ0MTBkNDUyN2EzZDBlMjQ2YThmYzYyNjg1YWIwODQ5ZGUyYWRlNjJiMDI3NWY1MTI2NGQyZGVhY2NiYzE2Yjc3MzQxN2Y4NDdhNGExZWE5YmM0CiAgICAgICAgICAgIHNldCBoYXNoZXMoYXNtLXBvbGljeS50YXIuZ3opIDJkMzllYzYwZDAwNmQwNWQ4YTE1NjdhMWQ4YWFlNzIyNDE5ZThiMDYyYWQ3N2Q2ZDlhMzE2NTI5NzFlNWU2N2JjNDA0M2Q4MTY3MWJhMmE4YjEyZGQyMjllYTQ2ZDIwNTE0NGY3NTM3NGVkNGNhZTU4Y2VmYThmOWFiNjUzM2U2CiAgICAgICAgICAgIHNldCBoYXNoZXMoZGVwbG95X3dhZi5zaCkgMWEzYTNjNjI3NGFiMDhhN2RjMmNiNzNhZWRjOGQyYjJhMjNjZDllMGViMDZhMmUxNTM0YjM2MzJmMjUwZjFkODk3MDU2ZjIxOWQ1YjM1ZDNlZWQxMjA3MDI2ZTg5OTg5Zjc1NDg0MGZkOTI5NjljNTE1YWU0ZDgyOTIxNGZiNzQKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS5wb2xpY3lfY3JlYXRvci50bXBsKSAwNjUzOWUwOGQxMTVlZmFmZTU1YWE1MDdlY2I0ZTQ0M2U4M2JkYjFmNTgyNWE5NTE0OTU0ZWY2Y2E1NmQyNDBlZDAwYzdiNWQ2N2JkOGY2N2I4MTVlZTlkZDQ2NDUxOTg0NzAxZDA1OGM4OWRhZTI0MzRjODk3MTVkMzc1YTYyMAogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LnNlcnZpY2VfZGlzY292ZXJ5LnRtcGwpIDQ4MTFhOTUzNzJkMWRiZGJiNGY2MmY4YmNjNDhkNGJjOTE5ZmE0OTJjZGEwMTJjODFlM2EyZmU2M2Q3OTY2Y2MzNmJhODY3N2VkMDQ5YTgxNGE5MzA0NzMyMzRmMzAwZDNmOGJjZWQyYjBkYjYzMTc2ZDUyYWM5OTY0MGNlODFiCiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUuY2xvdWRfbG9nZ2VyLnYxLjAuMC50bXBsKSA2NGEwZWQzYjVlMzJhMDM3YmE0ZTcxZDQ2MDM4NWZlOGI1ZTFhZWNjMjdkYzBlODUxNGI1MTE4NjM5NTJlNDE5YTg5ZjRhMmE0MzMyNmFiYjU0M2JiYTliYzM0Mzc2YWZhMTE0Y2VkYTk1MGQyYzNiZDA4ZGFiNzM1ZmY1YWQyMAogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LWFwcHN2Y3MtMy41LjEtNS5ub2FyY2gucnBtKSBiYTcxYzZlMWM1MmQwYzcwNzdjZGIyNWE1ODcwOWI4ZmI3YzM3YjM0NDE4YTgzMzhiYmY2NzY2ODMzOTY3NmQyMDhjMWE0ZmVmNGU1NDcwYzE1MmFhYzg0MDIwYjRjY2I4MDc0Y2UzODdkZTI0YmUzMzk3MTEyNTZjMGZhNzhjOAogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LWFwcHN2Y3MtMy4xOC4wLTQubm9hcmNoLnJwbSkgZTcyZWU4MDA1YTI3MDcwYWMzOTlhYjA5N2U4YWE1MDdhNzJhYWU0NzIxZDc0OTE1ODljZmViODIxZGIzZWY4NmNiYzk3OWU3OTZhYjMxOWVjNzI3YmI1MTQwMGNjZGE4MTNjNGI5ZWI0YTZiM2QxMjIwYTM5NmI1ODJmOGY0MDAKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS1hcHBzdmNzLTMuMjAuMC0zLm5vYXJjaC5ycG0pIGQ0YmJhODg5MmEyMDY4YmI1M2Y4OGM2MDkwZGM2NWYxNzcwN2FiY2EzNWE3ZWQyZmZmMzk5ODAwNTdmZTdmN2EyZWJmNzEwYWIyMjg0YTFkODNkNzBiNzc0NmJlYWJhZDlkZjYwMzAxN2MwZmQ4NzI4Zjc0NTc2NjFjOTVhYzhkCiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUtYXBwc3Zjcy0zLjI1LjAtMy5ub2FyY2gucnBtKSAyNmYxOWJkYWFhODFjYmUwNDIxYjNlMDhjMDk5ODdmOWRkMGM1NGIwNWE2MjZkNmEyMWE4MzZiMzQyNDhkMmQ5ZDgzMDk1ZjBkYWFkOGU3YTRhMDY4ZTllZjk5Yjg5ZmJjZDI0NmFlOGI2MTdhYzJiMjQ1NjU5OTE1N2QwZThiMwogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LWFwcHN2Y3MtMy4yNi4xLTEubm9hcmNoLnJwbSkgYjQ2MGUxMTY3OWQzOGE5NjU0OWI1MDQxZGVmMjdiNDE5ZjFhNDFjOGY3ODhmOWY4YzdhMDM0YWE1Y2I1YThjOWZkMTUxYzdjNDM5YmViZDA5M2ZjZDg1Y2Q4NjU3ZjFjMDY0NTUxZDkzMzc1NjZmOWZjN2U5NTA2YzU1ZGMwMmMKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS1hcHBzdmNzLTMuMzEuMC02Lm5vYXJjaC5ycG0pIDY1MDZmZGU1ZDFjMmUwNjc2NjJiNTEzMzg3ZGNjZGEwMjgxZDNiYmM2MDRmYzZkY2Y4ZTU3NDBhZTU2Mzc0ODg5OWY3ZjMzNWUzNDkwMDZmZTNmMGU3NTFjZDcwZDRlZjhiZTM3MDFhZTQ1ZGNhMzA1ZGU2NDlmMjU5ZjA5MGE5CiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUtY2xvdWQtZmFpbG92ZXItMS4xLjAtMC5ub2FyY2gucnBtKSAxNWE0NDBjMjk5ZjllNGFmODZhM2QwZjViMGQ3NWIwMDU0Mzg1Yjk1ZTQ3YzNlZjExNmQyZTBiZmIwMDQxYTI2ZGNiZjU0OTAyOGUyYTI2ZDJjNzE4ZWM2MTQ0NmJkNjU3YmUzOGZiYmNkOWRiNzgxZWZlNTQxNGMxNzRhYzY4YwogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LWNsb3VkLWZhaWxvdmVyLTEuMy4wLTAubm9hcmNoLnJwbSkgMTk2ODFlYjMzZDlmOTEwYzkxM2Y4MTgwMTk5NDg1ZWI2NTNiNGI1ZWJlYWFlMGI5MGE2Y2U4MzQxZDdhMjJmZWQ4ZDIxODE1YjViYTE0OGM0Njg4NTJkMjBjYzI2ZmFkNGM0MjQyZTUwZWNjMTg0ZjFmODc3MGRhY2NlZDZmNmEKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS1jbG91ZC1mYWlsb3Zlci0xLjQuMC0wLm5vYXJjaC5ycG0pIDQ5ZTkxMDhhMDcwZTBjODcxM2FlYjdiMzMwNjYyMzU4NTQyZTYxYjdjNTNhOWQ0NTEwOGQzN2E5YmY1MjQ2ZjllNGFhYWUxMGNjNjEwNjQ4MDFkY2NjZDIwYmZkNTEwODM0N2IwZjY5NDUxMGU3ZWNlMDdmOTZjNDViYTY4M2IwCiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUtY2xvdWQtZmFpbG92ZXItMS41LjAtMC5ub2FyY2gucnBtKSAzM2E3ZTJkMDQ3MTA2YmNjZTY4MTc1N2E2NTI0MGJmYWNlZGQ0OGUxMzU2N2UwNWZkYjIzYTRiMjY5ZDI2NmFhNTAwMWY4MTE1OGMzOTY0ZGMyOTdmMDQyOGRiMzFjOWRmNDI4MDAyODk4ZDE5MDI4NWIzNDljNTk0MjJhNTczYgogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LWNsb3VkLWZhaWxvdmVyLTEuNi4xLTEubm9hcmNoLnJwbSkgYzFiODQyZGEyMWI4ZDFiYTIxYjZlYjYzYzg1OThhOWVhOTk4NmQ1ZGFkZGMyMWU0ZDI4MGUxZDZiMDlkM2RiMWRlOGFjN2RlNWM4NGVkZjA3YjQzZTRhZjAzZGFmOGZlNzQ3YTQwNDhmNjU3M2Q5NTUyMDYzNTJjZGUyY2VjNjUKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS1jbG91ZC1mYWlsb3Zlci0xLjcuMS0xLm5vYXJjaC5ycG0pIDE0ZmYwY2QyYmI0OTc4MGNjMGFlMzAyMWM0ZmM4ZmNjMDk2ZTNmY2UyMjU4MDk2YTRhYTAyNmQ2ZDM3ZGU3MjhjYTczNDViZmUzYTc5MDMxZTMzNmU3NGQyNWEyYjQwZmYyODMyNGMyYzc1MmJmMGVlNzFiN2ZjODliNmZjOGZlCiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUtY2xvdWQtZmFpbG92ZXItMS44LjAtMC5ub2FyY2gucnBtKSAyMzA4NmQxY2JmM2NiMjRlYWM3ZWJhMjMwNTE1NmM2MDBmYTIxZjFiODk2MzIxYTJmYTUyMjVkMzMxZDdlNDE0NzFlZGIzZjUzNjgxNDRkODY4NDhhNDUyMGIxZTAwNWMwMTQ0ODVmZjQ1MWU3ZGE2NDI5MDUzZjU4YmZlOGNlNAogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LWNsb3VkLWZhaWxvdmVyLTEuOS4wLTAubm9hcmNoLnJwbSkgMDljMTUzNzczODlhYzE4MzEzMzcwNjM1ZmI5OWY5YWZmMDU5NzA4MDdjYzYwYmZmMDc0ZjgwZjY2NDAyM2NmYzBkOWY1YjdmMmVkN2E4Zjg3OWRlYjJkYTg0YTAzNGJiOWZhOWY0ZTk1Zjk4MDZkNjQ0YWY1MThkYjMyZjE0MjUKCiAgICAgICAgICAgIHNldCBmaWxlX3BhdGggW2xpbmRleCAkdG1zaDo6YXJndiAxXQogICAgICAgICAgICBzZXQgZmlsZV9uYW1lIFtmaWxlIHRhaWwgJGZpbGVfcGF0aF0KCiAgICAgICAgICAgIGlmIHshW2luZm8gZXhpc3RzIGhhc2hlcygkZmlsZV9uYW1lKV19IHsKICAgICAgICAgICAgICAgIHRtc2g6OmxvZyBlcnIgIk5vIGhhc2ggZm91bmQgZm9yICRmaWxlX25hbWUiCiAgICAgICAgICAgICAgICBleGl0IDEKICAgICAgICAgICAgfQoKICAgICAgICAgICAgc2V0IGV4cGVjdGVkX2hhc2ggJGhhc2hlcygkZmlsZV9uYW1lKQogICAgICAgICAgICBzZXQgY29tcHV0ZWRfaGFzaCBbbGluZGV4IFtleGVjIC91c3IvYmluL29wZW5zc2wgZGdzdCAtciAtc2hhNTEyICRmaWxlX3BhdGhdIDBdCiAgICAgICAgICAgIGlmIHsgJGV4cGVjdGVkX2hhc2ggZXEgJGNvbXB1dGVkX2hhc2ggfSB7CiAgICAgICAgICAgICAgICBleGl0IDAKICAgICAgICAgICAgfQogICAgICAgICAgICB0bXNoOjpsb2cgZXJyICJIYXNoIGRvZXMgbm90IG1hdGNoIGZvciAkZmlsZV9wYXRoIgogICAgICAgICAgICBleGl0IDEKICAgICAgICB9XX0gewogICAgICAgICAgICB0bXNoOjpsb2cgZXJyIHtVbmV4cGVjdGVkIGVycm9yIGluIHZlcmlmeUhhc2h9CiAgICAgICAgICAgIGV4aXQgMQogICAgICAgIH0KICAgIH0KICAgIHNjcmlwdC1zaWduYXR1cmUgVWxoUmtBOWhoMGVPVmVRRjZBK09wekY5ZHZ4emFROFZxMjdEaUtRSlR5c0JXYXR2bkUrWmhHTDN6TVlwSW0xcCsvOFhTWWxvSmFkYnFMSjNEeklrQncxWG1xQU42ZjNHM0dRWmVMa1dpQUhEOFdaWlFZTkg4UUtOR1pvU0hpV0IzYlAzZDdmbnpFVUtTNVFyemhDbG5JUmZ0WUt2N3AxbXZ1R1FqTSs0UUYyNFZ0TlBCV1JkQnBKSDNtQ1Nidkg0UDM3SjZweTFOZTF3MUN5RG9FU2R4S1B1MmJ3bGJrdDUzWHdtWXc3TUR2MkJaV0hVUm5LRHl3Q1UwZEtxb0FlankwbEx1aFpPTld2UThTWjF6Z281SUJrYmRMRUhRV2Y3ZTNhY2ZBaFY4eFlCVHVyeEx6bnFOODJZT3N1bWp3cGRoYW95OEwyTGVZSXI3WHkvTkxNeGZ3PT0KICAgIHNpZ25pbmcta2V5IC9Db21tb24vZjUtaXJ1bGUKfQ==\' | base64 -d > /config/verifyHash',
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
                                    'cat <<\'EOF\' > /config/cloud/gce/custom-config.sh',
                                    '#!/bin/bash',
                                    'PROGNAME=$(basename $0)',
                                    'function error_exit {',
                                    'echo \"${PROGNAME}: ${1:-\\\"Unknown Error\\\"}\" 1>&2',
                                    'exit 1',
                                    '}',
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
                                    'declare -a tmsh=()',
                                    'date',
                                    'echo \'starting custom-config.sh\'',
                                    'tmsh+=(',
                                    '\'tmsh save /sys config\')',
                                    'for CMD in "${tmsh[@]}"',
                                    'do',
                                    '    if $CMD;then',
                                    '        echo \"command $CMD successfully executed."',
                                    '    else',
                                    '        error_exit "$LINENO: An error has occurred while executing $CMD. Aborting!"',
                                    '    fi',
                                    'done',
                                    'date',
                                    'manGuiPort="' + str(context.properties['manGuiPort']) + '"',
                                    'passwd=$(f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/decryptDataFromFile.js --data-file /config/cloud/gce/.adminPassword)',
                                    'file_loc="/config/cloud/custom_config"',
                                    'url_regex="(http:\/\/|https:\/\/)[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$"',
                                    'if [[ ' + str(context.properties['declarationUrl']) + ' =~ $url_regex ]]; then',
                                    '   response_code=$(/usr/bin/curl -sk -w "%{http_code}" ' + str(context.properties['declarationUrl']) + ' -o $file_loc)',
                                    '   if [[ $response_code == 200 ]]; then',
                                    '       echo "Custom config download complete; checking for valid JSON."',
                                    '       cat $file_loc | jq .class',
                                    '       if [[ $? == 0 ]]; then',
                                    '           wait_for_ready',
                                    '           response_code=$(/usr/bin/curl -skvvu admin:$passwd -w "%{http_code}" -X POST -H "Content-Type: application/json" -H "Expect:" https://localhost:${manGuiPort}/mgmt/shared/appsvcs/declare -d @$file_loc -o /dev/null)',
                                    '           if [[ $response_code == *200 || $response_code == *502 ]]; then',
                                    '               echo "Deployment of custom application succeeded."',
                                    '           else',
                                    '               echo "Failed to deploy custom application; continuing..."',
                                    '           fi',
                                    '       else',
                                    '           echo "Custom config was not valid JSON, continuing..."',
                                    '       fi',
                                    '   else',
                                    '       echo "Failed to download custom config; continuing..."',
                                    '   fi',
                                    'else',
                                    '   echo "Custom config was not a URL, continuing..."',
                                    'fi',
                                    '### START CUSTOM CONFIGURATION',
                                    '### END CUSTOM CONFIGURATION',
                                    'EOF',
                                    'cat <<\'EOF\' > /config/cloud/gce/rm-password.sh',
                                    '#!/bin/bash',
                                    'date',
                                    'echo \'starting rm-password.sh\'',
                                    'rm /config/cloud/gce/.adminPassword',
                                    'date',
                                    'EOF',
                                    'curl -s -f --retry 20 -o /config/cloud/f5-cloud-libs.tar.gz https://cdn.f5.com/product/cloudsolutions/f5-cloud-libs/v4.27.0/f5-cloud-libs.tar.gz',
                                    'curl -s -f --retry 20 -o /config/cloud/f5-cloud-libs-gce.tar.gz https://cdn.f5.com/product/cloudsolutions/f5-cloud-libs-gce/v2.9.2/f5-cloud-libs-gce.tar.gz',
                                    'curl -s -f --retry 20 -o /config/cloud/f5-bigip-runtime-init-1.4.2-1.gz.run -L http://cdn.f5.com/product/cloudsolutions/f5-bigip-runtime-init/v1.4.2/dist/f5-bigip-runtime-init-1.4.2-1.gz.run',
                                    'chmod 755 /config/verifyHash',
                                    'chmod 755 /config/installCloudLibs.sh',
                                    'chmod 755 /config/waitThenRun.sh',
                                    'chmod 755 /config/cloud/gce/custom-config.sh',
                                    'chmod 755 /config/cloud/gce/rm-password.sh',
                                    'nohup /config/installCloudLibs.sh &>> /var/log/install.log < /dev/null &',
                                    'nohup bash /config/cloud/f5-bigip-runtime-init-1.4.2-1.gz.run -- \'--cloud gcp\' && /usr/local/bin/f5-bigip-runtime-init --config-file /config/cloud/runtime-init-config.yaml --skip-telemetry >> /var/log/cloud/google/install.log < /dev/null &',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/f5-cloud-libs/scripts/runScript.js --signal PASSWORD_CREATED --file f5-rest-node --cl-args \'/config/cloud/gce/node_modules/f5-cloud-libs/scripts/generatePassword --file /config/cloud/gce/.adminPassword\' --log-level verbose -o /var/log/generatePassword.log &>> /var/log/install.log < /dev/null &',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/f5-cloud-libs/scripts/runScript.js --wait-for PASSWORD_CREATED --signal ADMIN_CREATED --file /config/cloud/gce/node_modules/f5-cloud-libs/scripts/createUser.sh --cl-args \'--user admin --password-file /config/cloud/gce/.adminPassword\' --log-level debug -o /var/log/createUser.log &>> /var/log/install.log < /dev/null &',
                                    CUSTHASH,
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/f5-cloud-libs/scripts/onboard.js --port 8443 --ssl-port ',
                                    context.properties['manGuiPort'],
                                    ' --wait-for ADMIN_CREATED -o /var/log/onboard.log --log-level debug --no-reboot --host localhost --user admin --password-url file:///config/cloud/gce/.adminPassword --ntp 0.us.pool.ntp.org --ntp 1.us.pool.ntp.org --tz UTC ' + '--modules ' + PROVISIONING_MODULES + ' --license ',
                                    context.properties['licenseKey1'],
                                    SENDANALYTICS,
                                    ' --ping &>> /var/log/install.log < /dev/null &',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/f5-cloud-libs/scripts/runScript.js --file /config/cloud/gce/custom-config.sh --cwd /config/cloud/gce -o /var/log/custom-config.log --log-level debug --wait-for ONBOARD_DONE --signal CUSTOM_CONFIG_DONE &>> /var/log/install.log < /dev/null &',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/f5-cloud-libs/scripts/runScript.js --file /config/cloud/gce/rm-password.sh --cwd /config/cloud/gce -o /var/log/rm-password.log --log-level debug --wait-for CUSTOM_CONFIG_DONE --signal PASSWORD_REMOVED &>> /var/log/install.log < /dev/null &',
                                    'touch /config/startupFinished',

                                    ])
                            )
              }]
          }
      }
  }]
  outputs = [{
      'name': 'bigipIP',
      'value': ''.join(['$(ref.' + context.env['name'] + '-' + context.env['deployment'] + '.bigipIP)'])
  }]
  return {'resources': resources}