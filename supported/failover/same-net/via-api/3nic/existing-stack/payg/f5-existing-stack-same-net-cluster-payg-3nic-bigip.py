# Copyright 2019 F5 Networks All rights reserved.
#
# Version 3.0.3

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
            'targetTags': ['mgmtfw-'+ context.env['deployment']],
            'allowed': [{
                "IPProtocol": "TCP",
                "ports": [str(context.properties['mgmtGuiPort']),'22'],
                },
            ]
        }
    }
    return firewallRuleMgmt


def Metadata(context,group, storageName, licenseType):

  # SETUP VARIABLES
  ## Template Analytics
  ALLOWUSAGEANALYTICS = str(context.properties['allowUsageAnalytics']).lower()
  if ALLOWUSAGEANALYTICS in ['yes', 'true']:
      CUSTHASH = 'CUSTOMERID=`curl -s "http://metadata.google.internal/computeMetadata/v1/project/numeric-project-id" -H "Metadata-Flavor: Google" |sha512sum|cut -d " " -f 1`;\nDEPLOYMENTID=`curl -s "http://metadata.google.internal/computeMetadata/v1/instance/id" -H "Metadata-Flavor: Google"|sha512sum|cut -d " " -f 1`;'
      SENDANALYTICS = ' --metrics "cloudName:google,region:' + context.properties['region'] + ',bigipVersion:' + context.properties['imageName'] + ',customerId:${CUSTOMERID},deploymentId:${DEPLOYMENTID},templateName:f5-existing-stack-same-net-cluster-payg-3nic-bigip.py,templateVersion:3.0.3,licenseType:payg"'
  else:
      CUSTHASH = '# No template analytics'
      SENDANALYTICS = ''

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
    CLUSTERJS = ' '.join(["HOSTNAME=$(curl -s -f --retry 20 \"http://metadata.google.internal/computeMetadata/v1/instance/hostname\" -H \"Metadata-Flavor: Google\");NET2ADDRESS=$(curl -s -f --retry 20 \"http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/2/ip\" -H \"Metadata-Flavor: Google\");nohup /config/waitThenRun.sh",
                        "f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/cluster.js",
                        "-o /var/log/cloud/google/cluster.log",
                        "--log-level silly",
                        "--host localhost",
                        "--user admin",
                        "--password-url file:///config/cloud/gce/.adminPassword",
                        "--password-encrypted",
                        "--cloud gce",
                        "--provider-options 'region:" + context.properties['region'] + ",storageBucket:" + storageName  + "'",
                        "--master",
                        "--config-sync-ip ${NET2ADDRESS}",
                        "--create-group",
                        "--device-group failover_group",
                        "--sync-type sync-failover",
                        "--network-failover",
                        "--device ${HOSTNAME}",
                        "--auto-sync",
                        "2>&1 >> /var/log/cloud/google/install.log < /dev/null"
      ])
  elif group == "join":
     CLUSTERJS = ' '.join(["NET2ADDRESS=$(curl -s -f --retry 20 \"http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/2/ip\" -H \"Metadata-Flavor: Google\");nohup /config/waitThenRun.sh",
                        "f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/cluster.js",
                        "-o /var/log/cloud/google/cluster.log",
                        "--log-level silly",
                        "--host localhost",
                        "--user admin",
                        "--password-url file:///config/cloud/gce/.adminPassword",
                        "--password-encrypted",
                        "--cloud gce",
                        "--provider-options 'region:" + context.properties['region'] + ",storageBucket:" + storageName  + "'",
                        "--config-sync-ip ${NET2ADDRESS}",
                        "--join-group",
                        "--device-group failover_group",
                        "--remote-host ",
                        "$(ref.bigip1-" + context.env['deployment'] + ".networkInterfaces[1].networkIP)",
                        "2>&1 >> /var/log/cloud/google/install.log < /dev/null"
             ])
  else:
      CLUSTERJS = ''

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
                                    'declare -a filesToVerify=(\"/config/cloud/f5-cloud-libs.tar.gz\" \"/config/cloud/f5-cloud-libs-gce.tar.gz\" \"/config/cloud/f5-appsvcs-3.5.1-5.noarch.rpm\" \"/config/cloud/f5.service_discovery.tmpl\")',
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
                                    'echo \'Y2xpIHNjcmlwdCAvQ29tbW9uL3ZlcmlmeUhhc2ggewpwcm9jIHNjcmlwdDo6cnVuIHt9IHsKICAgICAgICBpZiB7W2NhdGNoIHsKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS1jbG91ZC1saWJzLnRhci5neikgNTU2MWUwMmI3NjRkN2I5YWNmNTJlZDU5M2ExYmZlNDkyMDNiOWZmNWU5ZWE5NDdlMThkNjA0ZmU0MDQ0NjIzMzY0Y2Q1Zjk5YzM5Yzg1ZDRlZjg3MTFhZDUxZmFiODFjZTAxMDdkOGMyNzY4MjRhZWYwMzE0Nzk4ZjczODQ2MGMKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS1jbG91ZC1saWJzLWF3cy50YXIuZ3opIDA3NmM5NjljYmZmZjEyZWZhY2NlMDg3OTgyMDI2MmI3Nzg3Yzk4NjQ1ZjExMDU2NjdjYzQ5MjdkNGFjZmUyNDY2ZWQ2NGM3NzdiNmQzNTk1N2Y2ZGY3YWUyNjY5MzdkZGU0MmZlZjRjOGIxZjg3MDAyMGEzNjZmN2Y5MTBmZmI1CiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUtY2xvdWQtbGlicy1henVyZS50YXIuZ3opIDkwMzcyMDNiMWFmMzEyODhiYTY5OTMyMDRhMmFiZjNiZDY2MGY2MmU3ZGZiMmQ1ODI1OTA5ZGQ2OTEzM2NlNWI0ZjVjNzI1YWZhYmQ3ZDJhY2FhNjkzNjY5Yzg3OGRhYTA0YTYzNzUzMTRkOTg1YmEwN2M4YTM2ZGNjYzYxYzVhCiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUtY2xvdWQtbGlicy1nY2UudGFyLmd6KSAxNjc3ODM1ZTY5OTY3ZmQ5ODgyZWFkMDNjYmRkMjRiNDI2NjI3MTMzYjhkYjllNDFmNmRlNWEyNmZlZjk5YzJkN2I2OTU5NzhhYzE4OWYwMGY2MWMwNzM3ZTZkYmI2MzhkNDJkZWE0M2E4NjdlZjRjMDFkOTUwN2QwZWUxZmIyZgogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LWNsb3VkLWxpYnMtb3BlbnN0YWNrLnRhci5neikgNWM4M2ZlNmE5M2E2ZmNlYjVhMmU4NDM3YjVlZDhjYzlmYWY0YzE2MjFiZmM5ZTZhMDc3OWY2YzIxMzdiNDVlYWI4YWUwZTdlZDc0NWM4Y2Y4MjFiOTM3MTI0NWNhMjk3NDljYTBiN2U1NjYzOTQ5ZDc3NDk2Yjg3MjhmNGIwZjkKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS1jbG91ZC1saWJzLWNvbnN1bC50YXIuZ3opIGEzMmFhYjM5NzA3M2RmOTJjYmJiYTUwNjdlNTgyM2U5YjVmYWZjYTg2MmEyNThiNjBiNmI0MGFhMDk3NWMzOTg5ZDFlMTEwZjcwNjE3N2IyZmZiZTRkZGU2NTMwNWEyNjBhNTg1NjU5NGNlN2FkNGVmMGM0N2I2OTRhZTRhNTEzCiAgICAgICAgICAgIHNldCBoYXNoZXMoYXNtLXBvbGljeS1saW51eC50YXIuZ3opIDYzYjVjMmE1MWNhMDljNDNiZDg5YWYzNzczYmJhYjg3YzcxYTZlN2Y2YWQ5NDEwYjIyOWI0ZTBhMWM0ODNkNDZmMWE5ZmZmMzlkOTk0NDA0MWIwMmVlOTI2MDcyNDAyNzQxNGRlNTkyZTk5ZjRjMjQ3NTQxNTMyM2UxOGE3MmUwCiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUuaHR0cC52MS4yLjByYzQudG1wbCkgNDdjMTlhODNlYmZjN2JkMWU5ZTljMzVmMzQyNDk0NWVmODY5NGFhNDM3ZWVkZDE3YjZhMzg3Nzg4ZDRkYjEzOTZmZWZlNDQ1MTk5YjQ5NzA2NGQ3Njk2N2IwZDUwMjM4MTU0MTkwY2EwYmQ3Mzk0MTI5OGZjMjU3ZGY0ZGMwMzQKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS5odHRwLnYxLjIuMHJjNi50bXBsKSA4MTFiMTRiZmZhYWI1ZWQwMzY1ZjAxMDZiYjVjZTVlNGVjMjIzODU2NTVlYTNhYzA0ZGUyYTM5YmQ5OTQ0ZjUxZTM3MTQ2MTlkYWU3Y2E0MzY2MmM5NTZiNTIxMjIyODg1OGYwNTkyNjcyYTI1NzlkNGE4Nzc2OTE4NmUyY2JmZQogICAgICAgICAgICBzZXQgaGFzaGVzKGY1Lmh0dHAudjEuMi4wcmM3LnRtcGwpIDIxZjQxMzM0MmU5YTdhMjgxYTBmMGUxMzAxZTc0NWFhODZhZjIxYTY5N2QyZTZmZGMyMWRkMjc5NzM0OTM2NjMxZTkyZjM0YmYxYzJkMjUwNGMyMDFmNTZjY2Q3NWM1YzEzYmFhMmZlNzY1MzIxMzY4OWVjM2M5ZTI3ZGZmNzdkCiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUuYXdzX2FkdmFuY2VkX2hhLnYxLjMuMHJjMS50bXBsKSA5ZTU1MTQ5YzAxMGMxZDM5NWFiZGFlM2MzZDJjYjgzZWMxM2QzMWVkMzk0MjQ2OTVlODg2ODBjZjNlZDVhMDEzZDYyNmIzMjY3MTFkM2Q0MGVmMmRmNDZiNzJkNDE0YjRjYjhlNGY0NDVlYTA3MzhkY2JkMjVjNGM4NDNhYzM5ZAogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LmF3c19hZHZhbmNlZF9oYS52MS40LjByYzEudG1wbCkgZGUwNjg0NTUyNTc0MTJhOTQ5ZjFlYWRjY2FlZTg1MDYzNDdlMDRmZDY5YmZiNjQ1MDAxYjc2ZjIwMDEyNzY2OGU0YTA2YmUyYmJiOTRlMTBmZWZjMjE1Y2ZjMzY2NWIwNzk0NWU2ZDczM2NiZTFhNGZhMWI4OGU4ODE1OTAzOTYKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS5hd3NfYWR2YW5jZWRfaGEudjEuNC4wcmMyLnRtcGwpIDZhYjBiZmZjNDI2ZGY3ZDMxOTEzZjlhNDc0YjFhMDc4NjA0MzVlMzY2YjA3ZDc3YjMyMDY0YWNmYjI5NTJjMWYyMDdiZWFlZDc3MDEzYTE1ZTQ0ZDgwZDc0ZjMyNTNlN2NmOWZiYmUxMmE5MGVjNzEyOGRlNmZhY2QwOTdkNjhmCiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUuYXdzX2FkdmFuY2VkX2hhLnYxLjQuMHJjMy50bXBsKSAyZjIzMzliNGJjM2EyM2M5Y2ZkNDJhYWUyYTZkZTM5YmEwNjU4MzY2ZjI1OTg1ZGUyZWE1MzQxMGE3NDVmMGYxOGVlZGM0OTFiMjBmNGE4ZGJhOGRiNDg5NzAwOTZlMmVmZGNhN2I4ZWZmZmExYTgzYTc4ZTVhYWRmMjE4YjEzNAogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LmF3c19hZHZhbmNlZF9oYS52MS40LjByYzQudG1wbCkgMjQxOGFjOGIxZjE4ODRjNWMwOTZjYmFjNmE5NGQ0MDU5YWFhZjA1OTI3YTZhNDUwOGZkMWYyNWI4Y2M2MDc3NDk4ODM5ZmJkZGE4MTc2ZDJjZjJkMjc0YTI3ZTZhMWRhZTJhMWUzYTBhOTk5MWJjNjVmYzc0ZmMwZDAyY2U5NjMKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS5hd3NfYWR2YW5jZWRfaGEudjEuNC4wcmM1LnRtcGwpIDVlNTgyMTg3YWUxYTYzMjNlMDk1ZDQxZWRkZDQxMTUxZDZiZDM4ZWI4M2M2MzQ0MTBkNDUyN2EzZDBlMjQ2YThmYzYyNjg1YWIwODQ5ZGUyYWRlNjJiMDI3NWY1MTI2NGQyZGVhY2NiYzE2Yjc3MzQxN2Y4NDdhNGExZWE5YmM0CiAgICAgICAgICAgIHNldCBoYXNoZXMoYXNtLXBvbGljeS50YXIuZ3opIDJkMzllYzYwZDAwNmQwNWQ4YTE1NjdhMWQ4YWFlNzIyNDE5ZThiMDYyYWQ3N2Q2ZDlhMzE2NTI5NzFlNWU2N2JjNDA0M2Q4MTY3MWJhMmE4YjEyZGQyMjllYTQ2ZDIwNTE0NGY3NTM3NGVkNGNhZTU4Y2VmYThmOWFiNjUzM2U2CiAgICAgICAgICAgIHNldCBoYXNoZXMoZGVwbG95X3dhZi5zaCkgMWEzYTNjNjI3NGFiMDhhN2RjMmNiNzNhZWRjOGQyYjJhMjNjZDllMGViMDZhMmUxNTM0YjM2MzJmMjUwZjFkODk3MDU2ZjIxOWQ1YjM1ZDNlZWQxMjA3MDI2ZTg5OTg5Zjc1NDg0MGZkOTI5NjljNTE1YWU0ZDgyOTIxNGZiNzQKICAgICAgICAgICAgc2V0IGhhc2hlcyhmNS5wb2xpY3lfY3JlYXRvci50bXBsKSAwNjUzOWUwOGQxMTVlZmFmZTU1YWE1MDdlY2I0ZTQ0M2U4M2JkYjFmNTgyNWE5NTE0OTU0ZWY2Y2E1NmQyNDBlZDAwYzdiNWQ2N2JkOGY2N2I4MTVlZTlkZDQ2NDUxOTg0NzAxZDA1OGM4OWRhZTI0MzRjODk3MTVkMzc1YTYyMAogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LnNlcnZpY2VfZGlzY292ZXJ5LnRtcGwpIDQ4MTFhOTUzNzJkMWRiZGJiNGY2MmY4YmNjNDhkNGJjOTE5ZmE0OTJjZGEwMTJjODFlM2EyZmU2M2Q3OTY2Y2MzNmJhODY3N2VkMDQ5YTgxNGE5MzA0NzMyMzRmMzAwZDNmOGJjZWQyYjBkYjYzMTc2ZDUyYWM5OTY0MGNlODFiCiAgICAgICAgICAgIHNldCBoYXNoZXMoZjUuY2xvdWRfbG9nZ2VyLnYxLjAuMC50bXBsKSA2NGEwZWQzYjVlMzJhMDM3YmE0ZTcxZDQ2MDM4NWZlOGI1ZTFhZWNjMjdkYzBlODUxNGI1MTE4NjM5NTJlNDE5YTg5ZjRhMmE0MzMyNmFiYjU0M2JiYTliYzM0Mzc2YWZhMTE0Y2VkYTk1MGQyYzNiZDA4ZGFiNzM1ZmY1YWQyMAogICAgICAgICAgICBzZXQgaGFzaGVzKGY1LWFwcHN2Y3MtMy41LjEtNS5ub2FyY2gucnBtKSBiYTcxYzZlMWM1MmQwYzcwNzdjZGIyNWE1ODcwOWI4ZmI3YzM3YjM0NDE4YTgzMzhiYmY2NzY2ODMzOTY3NmQyMDhjMWE0ZmVmNGU1NDcwYzE1MmFhYzg0MDIwYjRjY2I4MDc0Y2UzODdkZTI0YmUzMzk3MTEyNTZjMGZhNzhjOAoKICAgICAgICAgICAgc2V0IGZpbGVfcGF0aCBbbGluZGV4ICR0bXNoOjphcmd2IDFdCiAgICAgICAgICAgIHNldCBmaWxlX25hbWUgW2ZpbGUgdGFpbCAkZmlsZV9wYXRoXQoKICAgICAgICAgICAgaWYgeyFbaW5mbyBleGlzdHMgaGFzaGVzKCRmaWxlX25hbWUpXX0gewogICAgICAgICAgICAgICAgdG1zaDo6bG9nIGVyciAiTm8gaGFzaCBmb3VuZCBmb3IgJGZpbGVfbmFtZSIKICAgICAgICAgICAgICAgIGV4aXQgMQogICAgICAgICAgICB9CgogICAgICAgICAgICBzZXQgZXhwZWN0ZWRfaGFzaCAkaGFzaGVzKCRmaWxlX25hbWUpCiAgICAgICAgICAgIHNldCBjb21wdXRlZF9oYXNoIFtsaW5kZXggW2V4ZWMgL3Vzci9iaW4vb3BlbnNzbCBkZ3N0IC1yIC1zaGE1MTIgJGZpbGVfcGF0aF0gMF0KICAgICAgICAgICAgaWYgeyAkZXhwZWN0ZWRfaGFzaCBlcSAkY29tcHV0ZWRfaGFzaCB9IHsKICAgICAgICAgICAgICAgIGV4aXQgMAogICAgICAgICAgICB9CiAgICAgICAgICAgIHRtc2g6OmxvZyBlcnIgIkhhc2ggZG9lcyBub3QgbWF0Y2ggZm9yICRmaWxlX3BhdGgiCiAgICAgICAgICAgIGV4aXQgMQogICAgICAgIH1dfSB7CiAgICAgICAgICAgIHRtc2g6OmxvZyBlcnIge1VuZXhwZWN0ZWQgZXJyb3IgaW4gdmVyaWZ5SGFzaH0KICAgICAgICAgICAgZXhpdCAxCiAgICAgICAgfQogICAgfQogICAgc2NyaXB0LXNpZ25hdHVyZSBTYkQ5MTFFaElkb01MVVY1V0tmN0psNTF3eEZ5WUJLS0FvbEY1RVJwUk02YUJnMTduRmxlVTNHWTFhSG04MmVNa2oxcWtxZ0lMaDk2RHptYlZFbVRDQTh4bjRzSERLcUVUWk00MVhYYWJhTzVEb3pOKzlzZjY5aEdXcGs4eXcxbk9IZ1ZmeWRYaWRlM2ZNOTJ4NXEvNzRkMkp6c1Jzd3NZaXo3YW12TTVzeFAyTkhzbm94U1BSZTQvdngrTWpiSkdTdWk1SmhGV2NtNDNrSFV6RXo5NFlFTkZtU1kxQnlKZnJlNGViUVFUandja2IvL21NMjNnbEhUcHlvdWIvZThkalZaUE9nLzFtcW1HVzYzTnBjU2s2WlRDSzB1bEs1bHY4SGptOGRVdFZmZjlzdVladG5ub1BTVTRhZXlJMzlLRGlXTmRmd2tBV204QVJhQ1loczhwT1E9PQogICAgc2lnbmluZy1rZXkgL0NvbW1vbi9mNS1pcnVsZQp9\' | base64 -d > /config/verifyHash',
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
                                    'cat <<\'EOF\' > /config/cloud/gce/pre-nic-swap.sh',
                                    '#!/bin/bash',
                                    'CONFIG_FILE=\'/config/cloud/.deployment\'',
                                    'CLOUD_LIBS_DIR=\'/config/cloud/gce/node_modules/@f5devcentral\'',
                                    'echo \'{"tagKey":"f5_deployment","tagValue":"' + context.env['deployment'] + '"}\' > $CONFIG_FILE',
                                    'echo "/usr/bin/f5-rest-node ${CLOUD_LIBS_DIR}/f5-cloud-libs-gce/scripts/failover.js" >> /config/failover/tgactive',
                                    'echo "/usr/bin/f5-rest-node ${CLOUD_LIBS_DIR}/f5-cloud-libs-gce/scripts/failover.js" >> /config/failover/tgrefresh',
                                    '# save management route to file',
                                    'MGMT_GW=$(/usr/bin/curl -s -f --retry 20 \"http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/1/gateway\" -H \'Metadata-Flavor: Google\')',
                                    'CONFIG=$(cat $CONFIG_FILE | jq --arg mgmtGw $MGMT_GW \'. + {mgmtGw: $mgmtGw}\')',
                                    'echo $CONFIG > $CONFIG_FILE',
                                    '/usr/bin/tmsh delete sys management-route all',
                                    'echo \"pre-nic-swap done\"',
                                    'EOF',
                                    'cat <<\'EOF\' > /config/cloud/gce/post-nic-swap.sh',
                                    '#!/bin/bash',
                                    'CLOUD_LIBS_DIR=\'/config/cloud/gce/node_modules/@f5devcentral\'',
                                    'source ${CLOUD_LIBS_DIR}/f5-cloud-libs/scripts/util.sh',
                                    'wait_mcp_running',
                                    'wait_for_management_ip',
                                    'MGMT_GW=$(cat /config/cloud/.deployment | jq .mgmtGw -r)',
                                    '# create default management route to allow connections to metadata, etc.',
                                    '/usr/bin/tmsh create sys management-route default network default gateway $MGMT_GW',
                                    '/usr/bin/tmsh save sys config',
                                    'EOF',
                                    'cat <<\'EOF\' > /config/cloud/gce/custom-config.sh',
                                    '#!/bin/bash',
                                    'source /usr/lib/bigstart/bigip-ready-functions',
                                    'wait_bigip_ready',
                                    'echo \"Getting information from metadata\"',
                                    'COMPUTE_BASE_URL=\"http://metadata.google.internal/computeMetadata/v1\"',
                                    'HOSTNAME=$(curl -s -f --retry 10 \"${COMPUTE_BASE_URL}/instance/hostname\" -H \'Metadata-Flavor: Google\')',
                                    'NET0ADDRESS=$(curl -s -f --retry 10 \"${COMPUTE_BASE_URL}/instance/network-interfaces/0/ip\" -H \'Metadata-Flavor: Google\')',
                                    'NET0MASK=$(curl -s -f --retry 10 \"${COMPUTE_BASE_URL}/instance/network-interfaces/0/subnetmask\" -H \'Metadata-Flavor: Google\')',
                                    'NET0GATEWAY=$(curl -s -f --retry 10 \"${COMPUTE_BASE_URL}/instance/network-interfaces/0/gateway\" -H \'Metadata-Flavor: Google\')',
                                    'NET2ADDRESS=$(curl -s -f --retry 10 \"${COMPUTE_BASE_URL}/instance/network-interfaces/2/ip\" -H \'Metadata-Flavor: Google\')',
                                    'NET2MASK=$(curl -s -f --retry 10 \"${COMPUTE_BASE_URL}/instance/network-interfaces/2/subnetmask\" -H \'Metadata-Flavor: Google\')',
                                    'NET2GATEWAY=$(curl -s -f --retry 10 \"${COMPUTE_BASE_URL}/instance/network-interfaces/2/gateway\" -H \'Metadata-Flavor: Google\')',
                                    'NET0NETWORK=$(/bin/ipcalc -n ${NET0ADDRESS} ${NET0MASK} | cut -d= -f2)',
                                    'NET2NETWORK=$(/bin/ipcalc -n ${NET2ADDRESS} ${NET2MASK} | cut -d= -f2)',
                                    'PROGNAME=$(basename $0)',
                                    'function error_exit {',
                                    'echo \"${PROGNAME}: ${1:-\\\"Unknown Error\\\"}\" 1>&2',
                                    'exit 1',
                                    '}',
                                    'function wait_for_ready {',
                                    '   checks=0',
                                    '   ready_response=""',
                                    '   ready_response_declare=""',
                                    '   checks_max=120',
                                    '   while [ $checks -lt $checks_max ] ; do',
                                    '      ready_response=$(curl -sku admin:$passwd -w "%{http_code}" -X GET  https://localhost:${mgmtGuiPort}/mgmt/shared/appsvcs/info -o /dev/null)',
                                    '      ready_response_declare=$(curl -sku admin:$passwd -w "%{http_code}" -X GET  https://localhost:${mgmtGuiPort}/mgmt/shared/appsvcs/declare -o /dev/null)',
                                    '      if [[ $ready_response == *200 && $ready_response_declare == *204 ]]; then',
                                    '          echo "AS3 is ready"',
                                    '          break',
                                    '      else',
                                    '         echo "AS3" is not ready: $checks, response: $ready_response $ready_response_declare',
                                    '         let checks=checks+1',
                                    '         if [[ $checks == $((checks_max/2)) ]]; then',
                                    '             echo "restarting restnoded"'
                                    '             bigstart restart restnoded',
                                    '         fi',
                                    '         sleep 5',
                                    '      fi',
                                    '   done',
                                    '   if [[ $ready_response != *200 || $ready_response_declare != *204 ]]; then',
                                    '      error_exit "$LINENO: AS3 was not installed correctly. Exit."',
                                    '   fi',
                                    '}',
                                    'date',
                                    'declare -a tmsh=()',
                                    'tmsh+=(\'tmsh load sys application template /config/cloud/f5.service_discovery.tmpl\')',
                                    'tmsh+=(',
                                    '\"tmsh create net vlan external interfaces add { 1.0 } mtu 1460\"',
                                    '\"tmsh create net self ${NET0ADDRESS}/32 vlan external\"',
                                    '\"tmsh create net route ext_gw_int network ${NET0GATEWAY}/32 interface external\"',
                                    '\"tmsh create net route ext_rt network ${NET0NETWORK}/${NET0MASK} gw ${NET0GATEWAY}\"',
                                    '\"tmsh create net route default gw ${NET0GATEWAY}\"',
                                    '\"tmsh create net vlan internal interfaces add { 1.2 } mtu 1460\"',
                                    '\"tmsh create net self ${NET2ADDRESS}/32 vlan internal allow-service add { tcp:4353 udp:1026 }\"',
                                    '\"tmsh create net route int_gw_int network ${NET2GATEWAY}/32 interface internal\"',
                                    '\"tmsh create net route int_rt network ${NET2NETWORK}/${NET2MASK} gw ${NET2GATEWAY}\"',
                                    '\"tmsh modify cm device ${HOSTNAME} unicast-address { { effective-ip ${NET2ADDRESS} effective-port 1026 ip ${NET2ADDRESS} } }\"',
                                    '\"tmsh modify sys global-settings remote-host add { metadata.google.internal { hostname metadata.google.internal addr 169.254.169.254 } }\"',
                                    '\"tmsh modify sys db failover.selinuxallowscripts value enable\"',
                                    '\"tmsh save /sys config\"',
                                    '\'bigstart restart restnoded\')',
                                    'for CMD in "${tmsh[@]}"',
                                    'do',
                                    '    if $CMD;then',
                                    '        echo \"command $CMD successfully executed."',
                                    '    else',
                                    '        error_exit "$LINENO: An error has occurred while executing $CMD. Aborting!"',
                                    '    fi',
                                    'done',
                                    'date',
                                    '### START CUSTOM CONFIGURATION',
                                    'mgmtGuiPort="' + str(context.properties['mgmtGuiPort']) + '"',
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
                                    '           response_code=$(/usr/bin/curl --retry 10 -skvvu admin:$passwd -w "%{http_code}" -X POST -H "Content-Type: application/json" https://localhost:${mgmtGuiPort}/mgmt/shared/appsvcs/declare -d @$file_loc -o /dev/null)',
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
                                    '### END CUSTOM CONFIGURATION',
                                    'EOF',
                                    'cat <<\'EOF\' > /config/cloud/gce/rm-password.sh',
                                    '#!/bin/bash',
                                    'date',
                                    'echo \'starting rm-password.sh\'',
                                    'rm /config/cloud/gce/.adminPassword',
                                    'date',
                                    'EOF', 
                                    'cat <<\'EOF\' > /config/cloud/gce/create-va.sh',
                                    '#!/bin/bash',
                                    'date',
                                    'echo "starting create-va.sh"',
                                    'baseUrl="http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0"',
                                    'forwardedIps=$(curl -s -f --retry 20 -H "Metadata-Flavor: Google" "${baseUrl}/forwarded-ips/?recursive=true")',
                                    'aliasIps=$(curl -s -f --retry 20 -H "Metadata-Flavor: Google" "${baseUrl}/ip-aliases/?recursive=true")',
                                    'ipsList=()',
                                    'for i in $(echo $forwardedIps | jq -c -r \'.[]\') ; do',
                                    '   ipsList=("${ipsList[@]}" "$i")',
                                    'done',
                                    'for i in $(echo $aliasIps | jq -c -r \'.[]\') ; do',
                                    '   i=$(echo $i | cut -d "/" -f1)',
                                    '   ipsList=("${ipsList[@]}" "$i")',
                                    'done',
                                    'for addr in "${ipsList[@]}"; do',
                                    '   echo "creating virtual address: $addr"',
                                    '   /usr/bin/tmsh create ltm virtual-address $addr address $addr',
                                    'done',
                                    '/usr/bin/tmsh save sys config',
                                    '# run failover to ensure objects are on the correct BIG-IP',
                                    '/config/failover/tgactive',
                                    'date',
                                    'EOF',
                                    'curl -s -f --retry 20 -o /config/cloud/f5-cloud-libs.tar.gz https://cdn.f5.com/product/cloudsolutions/f5-cloud-libs/v4.10.3/f5-cloud-libs.tar.gz',
                                    'curl -s -f --retry 20 -o /config/cloud/f5-cloud-libs-gce.tar.gz https://cdn.f5.com/product/cloudsolutions/f5-cloud-libs-gce/v2.3.4/f5-cloud-libs-gce.tar.gz',
                                    'curl -s -f --retry 20 -o /config/cloud/f5-appsvcs-3.5.1-5.noarch.rpm https://cdn.f5.com/product/cloudsolutions/f5-appsvcs-extension/v3.6.0/dist/lts/f5-appsvcs-3.5.1-5.noarch.rpm',
                                    'curl -s -f --retry 20 -o /config/cloud/f5.service_discovery.tmpl https://cdn.f5.com/product/cloudsolutions/iapps/common/f5-service-discovery/v2.3.2/f5.service_discovery.tmpl',
                                    'chmod 755 /config/verifyHash',
                                    'chmod 755 /config/installCloudLibs.sh',
                                    'chmod 755 /config/waitThenRun.sh',
                                    'chmod 755 /config/cloud/gce/pre-nic-swap.sh',
                                    'chmod 755 /config/cloud/gce/post-nic-swap.sh',
                                    'chmod 755 /config/cloud/gce/custom-config.sh',
                                    'chmod 755 /config/cloud/gce/rm-password.sh',
                                    'chmod 755 /config/cloud/gce/create-va.sh',
                                    'mkdir -p /var/log/cloud/google',
                                    CUSTHASH,
                                    'nohup /usr/bin/setdb provision.1nicautoconfig disable &>> /var/log/cloud/google/install.log < /dev/null &',
                                    'nohup /config/installCloudLibs.sh &>> /var/log/cloud/google/install.log < /dev/null &',
                                    'cat <<\'EOF\' > /config/cloud/gce/first-run.sh',
                                    'nohup /usr/bin/setdb provision.1nicautoconfig disable 2>&1 >> /var/log/cloud/google/install.log < /dev/null ',
                                    'nohup /config/installCloudLibs.sh 2>&1 >> /var/log/cloud/google/install.log < /dev/null ',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/runScript.js --file f5-rest-node --cl-args \'/config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/generatePassword --file /config/cloud/gce/.adminPassword --encrypt\' --log-level verbose --output /var/log/cloud/google/generatePassword.log 2>&1 >> /var/log/cloud/google/install.log < /dev/null ',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/runScript.js --file /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/createUser.sh --cl-args \'--user admin --password-file /config/cloud/gce/.adminPassword --password-encrypted\' --log-level debug --output /var/log/cloud/google/createUser.log 2>&1 >> /var/log/cloud/google/install.log < /dev/null ',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/runScript.js --file /config/cloud/gce/pre-nic-swap.sh --log-level debug --output /var/log/cloud/google/nic-swap.log 2>&1 >> /var/log/cloud/google/install.log < /dev/null ',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/onboard.js --output /var/log/cloud/google/onboard.log --log-level debug --host localhost --user admin --password-url file:///config/cloud/gce/.adminPassword --password-encrypted --port 443 --db provision.managementeth:eth1 2>&1 >> /var/log/cloud/google/install.log < /dev/null ',
                                    'reboot',
                                    'EOF',
                                    'cat <<\'EOF\' > /config/cloud/gce/second-run.sh',
                                    'if [ ! -f /config/cloud/gce/CUSTOM_CONFIG_DONE ]; then',
                                    '   source /usr/lib/bigstart/bigip-ready-functions',
                                    '   wait_bigip_ready',
                                    '   nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/runScript.js --file /config/cloud/gce/post-nic-swap.sh --log-level debug --output /var/log/cloud/google/nic-swap.log 2>&1 >> /var/log/cloud/google/install.log < /dev/null ',
                                    '   nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/onboard.js --output /var/log/cloud/google/onboard.log --log-level debug --install-ilx-package file:///config/cloud/f5-appsvcs-3.5.1-5.noarch.rpm --host localhost --user admin --password-url file:///config/cloud/gce/.adminPassword --password-encrypted --port 443 --ssl-port ' + str(context.properties['mgmtGuiPort']) + ' --hostname $(curl -s -f --retry 20 \"http://metadata.google.internal/computeMetadata/v1/instance/hostname\" -H \"Metadata-Flavor: Google\") --ntp 0.us.pool.ntp.org --ntp 1.us.pool.ntp.org --tz UTC ' + ' --modules ' + PROVISIONING_MODULES + SENDANALYTICS + ' 2>&1 >> /var/log/cloud/google/install.log < /dev/null ',
                                    '   nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/runScript.js --file /config/cloud/gce/custom-config.sh --cwd /config/cloud/gce --output /var/log/cloud/google/custom-config.log --log-level debug 2>&1 >> /var/log/cloud/google/install.log < /dev/null ',
                                    CLUSTERJS,
                                    '   nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/runScript.js --file /config/cloud/gce/rm-password.sh --cwd /config/cloud/gce --output /var/log/cloud/google/rm-password.log --log-level debug 2>&1 >> /var/log/cloud/google/install.log < /dev/null ',
                                    '   nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/runScript.js --file /config/cloud/gce/create-va.sh --cwd /config/cloud/gce --output /var/log/cloud/google/create-va.log --log-level debug 2>&1 >> /var/log/cloud/google/install.log < /dev/null ',
                                    '   touch /config/cloud/gce/CUSTOM_CONFIG_DONE',
                                    'fi',
                                    'EOF',
                                    'chmod 755 /config/cloud/gce/first-run.sh',
                                    'chmod 755 /config/cloud/gce/second-run.sh',
                                    'echo "/config/cloud/gce/second-run.sh 2>&1 | tee --append /var/log/cloud/google/install.log" >> /config/startup',
                                    'nohup /config/cloud/gce/first-run.sh &',
                                    'touch /config/startupFinished',
                                    ])
                            )
                }]
    }
  return metadata

def Instance(context, group, storageName, licenseType):
  aliasIps = []
  accessConfigSubnet = []
  accessConfigMgmt = []
  tagItems = ['mgmtfw-' + context.env['deployment'], 'intfw-' + context.env['deployment']]
  provisionPublicIp = str(context.properties['provisionPublicIP']).lower()

  # access config and tags - conditional on provisionPublicIP parameter (yes/no)
  if provisionPublicIp in ['yes', 'true']:
    accessConfigSubnet = [{
       'name': 'Subnet 1 NAT',
       'type': 'ONE_TO_ONE_NAT'
    }]
    accessConfigMgmt = [{
      'name': 'Management NAT',
      'type': 'ONE_TO_ONE_NAT'
    }]
  else:
    tagItems.append('no-ip')

  if group == 'create':
    aliasIps = [{'ipCidrRange': ip} for ip in context.properties['aliasIp'].split(';')]

  # Build instance template
  instance = {
        'zone': context.properties['availabilityZone1'],
        'canIpForward': True,
        'tags': {
          'items': tagItems
        },
        'labels': {
          'f5_deployment': context.env['deployment']
        },
        'machineType': ''.join([COMPUTE_URL_BASE, 'projects/',
                         context.env['project'], '/zones/', context.properties['availabilityZone1'], '/machineTypes/',
                         context.properties['instanceType']]),
        'serviceAccounts': [{
            'email': context.properties['serviceAccount'],
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
                            context.env['project'], '/global/networks/',
                            context.properties['network1']]),
            'subnetwork': ''.join([COMPUTE_URL_BASE, 'projects/',
                            context.env['project'], '/regions/',
                            context.properties['region'], '/subnetworks/',
                            context.properties['subnet1']]),
            'accessConfigs': accessConfigSubnet,
            'aliasIpRanges': aliasIps
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
def ForwardingRule(context, name, target):
  # Build forwarding rule
  forwardingRule = {
        'name': name,
        'type': 'compute.v1.forwardingRule',
        'properties': {
            'region': context.properties['region'],
            'IPProtocol': 'TCP',
            'target': target,
            'loadBalancingScheme': 'EXTERNAL',
        }
  }
  return forwardingRule

def GenerateConfig(context):

   ## set variables
  import random
  storageNumber = str(random.randint(10000, 99999))
  storageName = 'f5-bigip-' + context.env['deployment'] + '-' + storageNumber
  instanceName0 = 'bigip1-' + context.env['deployment']
  instanceName1 = 'bigip2-' + context.env['deployment']
  fwdRulesNamePrefix = context.env['deployment'] + '-fr'
  forwardingRules = [ForwardingRule(context, fwdRulesNamePrefix + str(i), '$(ref.' + instanceName0 + '-ti.selfLink)')
        for i in list(range(int(context.properties['numberOfForwardingRules'])))]

  resources = [
  FirewallRuleMgmt(context),
  {
    'name': instanceName0,
    'type': 'compute.v1.instance',
    'properties': Instance(context, 'create', storageName, 'payg')
  },{
    'name': instanceName1,
    'type': 'compute.v1.instance',
    'properties': Instance(context, 'join', storageName, 'payg')
  },{
    'name': storageName,
    'type': 'storage.v1.bucket',
    'properties': {
      'project': context.env['project'],
      'name': storageName,
    },
  },{
    'name': 'intfirewall-' + context.env['deployment'],
    'type': 'compute.v1.firewall',
    'properties': {
        'network': ''.join([COMPUTE_URL_BASE, 'projects/',
                            context.env['project'], '/global/networks/',
                            context.properties['network2']]),
        'targetTags': ['intfw-'+ context.env['deployment']],
        'sourceTags': ['intfw-'+ context.env['deployment']],
        'allowed': [{
            'IPProtocol': 'TCP',
            'ports': [4353]
            },{
            'IPProtocol': 'UDP',
            'ports': [1026],
        }]
      }
    },{
    'name': instanceName0 + '-ti',
    'type': 'compute.v1.targetInstances',
    'properties': {
      'description': instanceName0,
      'natPolicy': 'NO_NAT',
      'zone': context.properties['availabilityZone1'],
      'instance': ''.join([COMPUTE_URL_BASE, 'projects/', context.env['project'], '/zones/',
                          context.properties['availabilityZone1'], '/instances/', instanceName0])
    }
  },{
    'name': instanceName1 + '-ti',
    'type': 'compute.v1.targetInstances',
    'properties': {
      'description': instanceName1,
      'natPolicy': 'NO_NAT',
      'zone': context.properties['availabilityZone1'],
      'instance': ''.join([COMPUTE_URL_BASE, 'projects/', context.env['project'], '/zones/',
                          context.properties['availabilityZone1'], '/instances/', instanceName1])
    }
    }
  ]
  # add forwarding rules
  resources += forwardingRules
  return {'resources': resources}