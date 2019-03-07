# Copyright 2018 F5 Networks All rights reserved.
#
# Version v2.1.2

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
        SENDANALYTICS = ' --metrics "cloudName:google,region:' + context.properties['region'] + ',bigipVersion:' + context.properties['imageName'] + ',customerId:${CUSTOMERID},deploymentId:${DEPLOYMENTID},templateName:f5-payg-autoscale-bigip-waf.py,templateVersion:v2.1.1,licenseType:payg"'
    else:
        CUSTHASH = 'echo "No analytics."'
        SENDANALYTICS = ''
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
                                    'declare -a filesToVerify=(\"/config/cloud/f5-cloud-libs.tar.gz\" \"/config/cloud/f5-cloud-libs-gce.tar.gz\" \"/config/cloud/f5-appsvcs-3.5.1-5.noarch.rpm\"  \"/config/cloud/f5.service_discovery.tmpl\")',
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
                                    'cat <<\'EOF\' > /config/verifyHash',
                                    'cli script /Common/verifyHash {',
                                    'proc script::run {} {',
                                    '        if {[catch {',
                                    '            set hashes(f5-cloud-libs.tar.gz) 2ab601b44cb15118d533350af714cc2597881972b8c43bfca1c210c6927d9c4b166093ee5ca9a3cbaa03a84f6411cb4e42a1b95e4d244b870faede9537e92046',
                                    '            set hashes(f5-cloud-libs-aws.tar.gz) 076c969cbfff12efacce0879820262b7787c98645f1105667cc4927d4acfe2466ed64c777b6d35957f6df7ae266937dde42fef4c8b1f870020a366f7f910ffb5',
                                    '            set hashes(f5-cloud-libs-azure.tar.gz) 57fae388e8aa028d24a2d3fa2c029776925011a72edb320da47ccd4fb8dc762321c371312f692b7b8f1c84e8261c280f6887ba2e0f841b50547e6e6abc8043ba',
                                    '            set hashes(f5-cloud-libs-gce.tar.gz) 1677835e69967fd9882ead03cbdd24b426627133b8db9e41f6de5a26fef99c2d7b695978ac189f00f61c0737e6dbb638d42dea43a867ef4c01d9507d0ee1fb2f',
                                    '            set hashes(f5-cloud-libs-openstack.tar.gz) 5c83fe6a93a6fceb5a2e8437b5ed8cc9faf4c1621bfc9e6a0779f6c2137b45eab8ae0e7ed745c8cf821b9371245ca29749ca0b7e5663949d77496b8728f4b0f9',
                                    '            set hashes(f5-cloud-libs-consul.tar.gz) 2c6face582064600553f442a67a58bc7c19533923fac72a88edef0a90a845a5b9c45b5ba340184292a27a3319d8b8118364d16ea17f6225d31f7c2e997be9775',
                                    '            set hashes(asm-policy-linux.tar.gz) 63b5c2a51ca09c43bd89af3773bbab87c71a6e7f6ad9410b229b4e0a1c483d46f1a9fff39d9944041b02ee9260724027414de592e99f4c2475415323e18a72e0',
                                    '            set hashes(f5.http.v1.2.0rc4.tmpl) 47c19a83ebfc7bd1e9e9c35f3424945ef8694aa437eedd17b6a387788d4db1396fefe445199b497064d76967b0d50238154190ca0bd73941298fc257df4dc034',
                                    '            set hashes(f5.http.v1.2.0rc6.tmpl) 811b14bffaab5ed0365f0106bb5ce5e4ec22385655ea3ac04de2a39bd9944f51e3714619dae7ca43662c956b5212228858f0592672a2579d4a87769186e2cbfe',
                                    '            set hashes(f5.http.v1.2.0rc7.tmpl) 21f413342e9a7a281a0f0e1301e745aa86af21a697d2e6fdc21dd279734936631e92f34bf1c2d2504c201f56ccd75c5c13baa2fe7653213689ec3c9e27dff77d',
                                    '            set hashes(f5.aws_advanced_ha.v1.3.0rc1.tmpl) 9e55149c010c1d395abdae3c3d2cb83ec13d31ed39424695e88680cf3ed5a013d626b326711d3d40ef2df46b72d414b4cb8e4f445ea0738dcbd25c4c843ac39d',
                                    '            set hashes(f5.aws_advanced_ha.v1.4.0rc1.tmpl) de068455257412a949f1eadccaee8506347e04fd69bfb645001b76f200127668e4a06be2bbb94e10fefc215cfc3665b07945e6d733cbe1a4fa1b88e881590396',
                                    '            set hashes(f5.aws_advanced_ha.v1.4.0rc2.tmpl) 6ab0bffc426df7d31913f9a474b1a07860435e366b07d77b32064acfb2952c1f207beaed77013a15e44d80d74f3253e7cf9fbbe12a90ec7128de6facd097d68f',
                                    '            set hashes(f5.aws_advanced_ha.v1.4.0rc3.tmpl) 2f2339b4bc3a23c9cfd42aae2a6de39ba0658366f25985de2ea53410a745f0f18eedc491b20f4a8dba8db48970096e2efdca7b8efffa1a83a78e5aadf218b134',
                                    '            set hashes(f5.aws_advanced_ha.v1.4.0rc4.tmpl) 2418ac8b1f1884c5c096cbac6a94d4059aaaf05927a6a4508fd1f25b8cc6077498839fbdda8176d2cf2d274a27e6a1dae2a1e3a0a9991bc65fc74fc0d02ce963',
                                    '            set hashes(asm-policy.tar.gz) 2d39ec60d006d05d8a1567a1d8aae722419e8b062ad77d6d9a31652971e5e67bc4043d81671ba2a8b12dd229ea46d205144f75374ed4cae58cefa8f9ab6533e6',
                                    '            set hashes(deploy_waf.sh) 1a3a3c6274ab08a7dc2cb73aedc8d2b2a23cd9e0eb06a2e1534b3632f250f1d897056f219d5b35d3eed1207026e89989f754840fd92969c515ae4d829214fb74',
                                    '            set hashes(f5.policy_creator.tmpl) 06539e08d115efafe55aa507ecb4e443e83bdb1f5825a9514954ef6ca56d240ed00c7b5d67bd8f67b815ee9dd46451984701d058c89dae2434c89715d375a620',
                                    '            set hashes(f5.service_discovery.tmpl) 4811a95372d1dbdbb4f62f8bcc48d4bc919fa492cda012c81e3a2fe63d7966cc36ba8677ed049a814a930473234f300d3f8bced2b0db63176d52ac99640ce81b',
                                    '            set hashes(f5.cloud_logger.v1.0.0.tmpl) 64a0ed3b5e32a037ba4e71d460385fe8b5e1aecc27dc0e8514b511863952e419a89f4a2a43326abb543bba9bc34376afa114ceda950d2c3bd08dab735ff5ad20',
                                    '            set hashes(f5-appsvcs-3.5.1-5.noarch.rpm) ba71c6e1c52d0c7077cdb25a58709b8fb7c37b34418a8338bbf67668339676d208c1a4fef4e5470c152aac84020b4ccb8074ce387de24be339711256c0fa78c8',
                                    'NEW_LINE',
                                    '            set file_path [lindex $tmsh::argv 1]',
                                    '            set file_name [file tail $file_path]',
                                    'NEW_LINE',
                                    '            if {![info exists hashes($file_name)]} {',
                                    '                tmsh::log err \"No hash found for $file_name\"',
                                    '                exit 1',
                                    '            }',
                                    'NEW_LINE',
                                    '            set expected_hash $hashes($file_name)',
                                    '            set computed_hash [lindex [exec /usr/bin/openssl dgst -r -sha512 $file_path] 0]',
                                    '            if { $expected_hash eq $computed_hash } {',
                                    '                exit 0',
                                    '            }',
                                    '            tmsh::log err \"Hash does not match for $file_path\"',
                                    '            exit 1',
                                    '        }]} {',
                                    '            tmsh::log err {Unexpected error in verifyHash}',
                                    '            exit 1',
                                    '        }',
                                    '    }',
                                    '    script-signature OkhShM2pz6d5Rl2P+wsrW0nHGEinXT1SeFA4+0S1jvSDyeBvfjZq4vMzyLJWf5Ip1plRd3LtGsEIc5B/ixZyXOnz8Kp0pMa8TNjHew4s1IeOnNqoIPRzGzmVJ/zbxYzHCYg6Fn4zdX9giS/YQd7IQHSzsM3LYOkadKGEtRO6IRC/uGfcA4XPRslTlR5NS/9GgLouQS/UlejP5+uQkzDlueYJnSn+JoN2ewRZhotylncQlcJ4+8U/ucmV9vhLw+7/LZ9q2QrHIY4KExIazElBFT7xbS+dihMLp9xIztrqSiJc8+T+3le+0PhO9ZB4YOQg9uNV5FBWaSfVLjbu8pSZaA==',                                    '    signing-key /Common/f5-irule',
                                    '}',
                                    'EOF',
                                    '# empty new line chars get stripped, strip out place holder NEW_LINE',
                                    'sed -i "s/NEW_LINE//" /config/verifyHash',
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
                                    'useServiceDiscovery=' + str(context.properties['tagValue']),
                                    '(crontab -l 2>/dev/null; echo \'*/1 * * * * /config/cloud/gce/run_autoscale_update.sh\') | crontab -',
                                    '(crontab -l 2>/dev/null; echo \'59 23 * * * /config/cloud/gce/run_autoscale_backup.sh\') | crontab -',
                                    'f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/autoscale.js --cloud gce --provider-options \'storageBucket:' + storageName + ',mgmtPort:' + str(context.properties['manGuiPort']) + ',serviceAccount:' + context.properties['serviceAccount'] + ',instanceGroup:' + deployment + '-igm\' --host localhost --port 8443 --user cluster_admin --password-url file:///config/cloud/gce/.adminPassword --password-encrypted --device-group autoscale-group --block-sync -c join --log-level silly -o /var/log/cloud/google/autoscale.log',
                                    'if [ -f /config/cloud/master ];then',
                                    '  if $(jq \'.ucsLoaded\' < /config/cloud/master);then',
                                    '    echo "UCS backup loaded from backup folder in storage: ' + storageName + '."',
                                    '  else',
                                    '    echo "SELF-SELECTED as Master ... Initiated Autoscale Cluster ... Loading default config"',
                                    '    tmsh modify cm device-group autoscale-group asm-sync enabled',
                                    '    tmsh load sys application template /config/cloud/f5.http.v1.2.0rc7.tmpl',
                                    '    tmsh load sys application template /config/cloud/f5.service_discovery.tmpl',
                                    '    source /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/waitForBigip.sh;wait-for-bigip',
                                    '                                                                   ',
                                    '    ### START CUSTOM CONFIGURATION:  Policy Name/Policy URL, etc. ',
                                    '    applicationDnsName="' + str(context.properties['applicationDnsName']) + '"',
                                    '    applicationPort="' + str(context.properties['applicationPort']) + '"',
                                    '    asm_policy="/config/cloud/asm-policy-linux-' + context.properties['policyLevel'] + '.xml"',
                                    '    tagName="' + str(context.properties['tagName']) + '"',
                                    '    tagValue="' + str(context.properties['tagValue']) + '"',
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
                                    '               response_code=$(/usr/bin/curl -skvvu cluster_admin:$passwd -w "%{http_code}" -X POST -H "Content-Type: application/json" https://localhost:${manGuiPort}/mgmt/shared/appsvcs/declare -d @$file_loc -o /dev/null)',
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
                                    '      if [ -n "${useServiceDiscovery}" ];then',
                                    '         payload=$(echo $payload | jq -c \'del(.waf.http.pool.members[0].autoPopulate) | del(.waf.http.pool.members[0].hostname)\')',
                                    '         payload=$(echo $payload | jq -c --arg tagName $tagName --arg tagValue $tagValue \'.waf.http.pool.members[0].tagKey = $tagName | .waf.http.pool.members[0].tagValue = $tagValue\')',
                                    '      else',
                                    '         payload=$(echo $payload | jq -c \'del(.waf.http.pool.members[0].updateInterval) | del(.waf.http.pool.members[0].tagKey) | del(.waf.http.pool.members[0].tagValue) | del(.waf.http.pool.members[0].addressRealm) | del(.waf.http.pool.members[0].region)\')',
                                    '         payload=$(echo $payload | jq -c --arg pool_member $applicationDnsName \'.waf.http.pool.members[0].hostname = $pool_member | .waf.http.pool.members[0].addressDiscovery = "fqdn"\')',
                                    '      fi',
                                    '      response_code=$(/usr/bin/curl -skvvu cluster_admin:$passwd -w "%{http_code}" -X POST -H "Content-Type: application/json" https://localhost:${manGuiPort}/mgmt/shared/appsvcs/declare -d "$payload" -o /dev/null)',
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
                                    'curl -s -f --retry 20 -o /config/cloud/f5-cloud-libs.tar.gz https://cdn.f5.com/product/cloudsolutions/f5-cloud-libs/v4.8.0/f5-cloud-libs.tar.gz',
                                    'curl -s -f --retry 20 -o /config/cloud/f5-cloud-libs-gce.tar.gz https://cdn.f5.com/product/cloudsolutions/f5-cloud-libs-gce/v2.3.4/f5-cloud-libs-gce.tar.gz',
                                    'curl -s -f --retry 20 -o /config/cloud/f5-appsvcs-3.5.1-5.noarch.rpm https://cdn.f5.com/product/cloudsolutions/f5-appsvcs-extension/v3.6.0/dist/lts/f5-appsvcs-3.5.1-5.noarch.rpm',
                                    'curl -s -f --retry 20 -o /config/cloud/f5.service_discovery.tmpl https://cdn.f5.com/product/cloudsolutions/iapps/common/f5-service-discovery/v2.3.2/f5.service_discovery.tmpl',
                                    'curl -s -f --retry 20 -o /config/cloud/f5.http.v1.2.0rc7.tmpl http://cdn.f5.com/product/cloudsolutions/iapps/common/f5-http/f5.http.v1.2.0rc7.tmpl',
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
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/onboard.js --port 8443 --ssl-port ' + str(context.properties['manGuiPort']) + ' --wait-for ADMIN_CREATED -o /var/log/cloud/google/onboard.log --log-level silly --no-reboot --install-ilx-package file:///config/cloud/f5-appsvcs-3.5.1-5.noarch.rpm --host localhost --user cluster_admin --password-url file:///config/cloud/gce/.adminPassword --password-encrypted --hostname $(curl http://metadata.google.internal/computeMetadata/v1/instance/hostname -H "Metadata-Flavor: Google") --ntp 0.us.pool.ntp.org --ntp 1.us.pool.ntp.org --tz UTC --module ltm:nominal --module asm:nominal --db provision.1nicautoconfig:disable' + SENDANALYTICS + ' &>> /var/log/cloud/google/install.log < /dev/null &',
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
