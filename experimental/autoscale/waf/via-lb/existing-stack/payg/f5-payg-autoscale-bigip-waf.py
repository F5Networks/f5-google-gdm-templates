# Copyright 2018 F5 Networks All rights reserved.
#
# Version v1.5.0

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
                    'scopes': ['https://www.googleapis.com/auth/compute.readonly','https://www.googleapis.com/auth/devstorage.read_write','https://www.googleapis.com/auth/pubsub']
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
        SENDANALYTICS = ' --metrics "cloudName:google,region:' + context.properties['region'] + ',bigipVersion:' + context.properties['imageName'] + ',customerId:${CUSTOMERID},deploymentId:${DEPLOYMENTID},templateName:f5-existing-stack-payg-2nic-bigip.py,templateVersion:v1.3.0,licenseType:payg"'
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
                                    'declare -a filesToVerify=(\"/config/cloud/f5-cloud-libs.tar.gz\" \"/config/cloud/f5-cloud-libs-gce.tar.gz\" \"/config/cloud/f5.service_discovery.tmpl\")',
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
                                    '            set hashes(f5-cloud-libs.tar.gz) a1de46685e31463e6c103078797b90e5f29a4b94702b0522eef2364c3792414067a0bea50c4ed49784c14277a578d8b41f9ac7ba058d9ff72ef687034e5119c6',
                                    '            set hashes(f5-cloud-libs-aws.tar.gz) d0803e306c01bdf82895c8f30f3b3c2df5f76edbe1875c0ffbfea6864436ece54a73ffd02ccd1b889c324b093897702087b722f10cc7f87994f518f81d7260ea',
                                    '            set hashes(f5-cloud-libs-azure.tar.gz) a1f264a165b88c03f55d49afb4fdb5f63d80755f1afe947a02e4a36755c7fcec432495417d8084329c6c14e4c426c2e63bab92862afb760d63f584a570b119e6',
                                    '            set hashes(f5-cloud-libs-gce.tar.gz) c01b25f4d6f48d9ac21b1a6ba3553c978e4fb8ce8655947a307f27e67833c4bebf8b72fef108ea02e11b5e9aa35d33e39db8624b3db34de509d0d79959c754c7',
                                    '            set hashes(f5-cloud-libs-openstack.tar.gz) 5c83fe6a93a6fceb5a2e8437b5ed8cc9faf4c1621bfc9e6a0779f6c2137b45eab8ae0e7ed745c8cf821b9371245ca29749ca0b7e5663949d77496b8728f4b0f9',
                                    '            set hashes(asm-policy-linux.tar.gz) 63b5c2a51ca09c43bd89af3773bbab87c71a6e7f6ad9410b229b4e0a1c483d46f1a9fff39d9944041b02ee9260724027414de592e99f4c2475415323e18a72e0',
                                    '            set hashes(f5.http.v1.2.0rc4.tmpl) 47c19a83ebfc7bd1e9e9c35f3424945ef8694aa437eedd17b6a387788d4db1396fefe445199b497064d76967b0d50238154190ca0bd73941298fc257df4dc034',
                                    '            set hashes(f5.http.v1.2.0rc6.tmpl) 811b14bffaab5ed0365f0106bb5ce5e4ec22385655ea3ac04de2a39bd9944f51e3714619dae7ca43662c956b5212228858f0592672a2579d4a87769186e2cbfe',
                                    '            set hashes(f5.http.v1.2.0rc7.tmpl) 21f413342e9a7a281a0f0e1301e745aa86af21a697d2e6fdc21dd279734936631e92f34bf1c2d2504c201f56ccd75c5c13baa2fe7653213689ec3c9e27dff77d',
                                    '            set hashes(f5.aws_advanced_ha.v1.3.0rc1.tmpl) 9e55149c010c1d395abdae3c3d2cb83ec13d31ed39424695e88680cf3ed5a013d626b326711d3d40ef2df46b72d414b4cb8e4f445ea0738dcbd25c4c843ac39d',
                                    '            set hashes(f5.aws_advanced_ha.v1.4.0rc1.tmpl) de068455257412a949f1eadccaee8506347e04fd69bfb645001b76f200127668e4a06be2bbb94e10fefc215cfc3665b07945e6d733cbe1a4fa1b88e881590396',
                                    '            set hashes(f5.aws_advanced_ha.v1.4.0rc2.tmpl) 6ab0bffc426df7d31913f9a474b1a07860435e366b07d77b32064acfb2952c1f207beaed77013a15e44d80d74f3253e7cf9fbbe12a90ec7128de6facd097d68f',
                                    '            set hashes(f5.aws_advanced_ha.v1.4.0rc3.tmpl) 2f2339b4bc3a23c9cfd42aae2a6de39ba0658366f25985de2ea53410a745f0f18eedc491b20f4a8dba8db48970096e2efdca7b8efffa1a83a78e5aadf218b134',
                                    '            set hashes(asm-policy.tar.gz) 2d39ec60d006d05d8a1567a1d8aae722419e8b062ad77d6d9a31652971e5e67bc4043d81671ba2a8b12dd229ea46d205144f75374ed4cae58cefa8f9ab6533e6',
                                    '            set hashes(deploy_waf.sh) 1a3a3c6274ab08a7dc2cb73aedc8d2b2a23cd9e0eb06a2e1534b3632f250f1d897056f219d5b35d3eed1207026e89989f754840fd92969c515ae4d829214fb74',
                                    '            set hashes(f5.policy_creator.tmpl) 06539e08d115efafe55aa507ecb4e443e83bdb1f5825a9514954ef6ca56d240ed00c7b5d67bd8f67b815ee9dd46451984701d058c89dae2434c89715d375a620',
                                    '            set hashes(f5.service_discovery.tmpl) 7a4660468dffdc4f6d9aec4c1f9d22abfb3e484e7d6fe6a12fc9ab3eec3819dc34d133aea3cce4fdd87a0f4045069270061f2ea1ee7735922e4371592e498a0b',
                                    '            set hashes(f5.cloud_logger.v1.0.0.tmpl) a26d5c470e70b821621476bcfd0579dbc0964f6a54158bc6314fa1e2f63b23bf3f3eb43ade5081131c24e08579db2e1e574beb3f8d9789d28acb4f312fad8c3e',
                                    'EOF',
                                    'echo -e "" >> /config/verifyHash',
                                    'cat <<\'EOF\' >> /config/verifyHash',
                                    '            set file_path [lindex $tmsh::argv 1]',
                                    '            set file_name [file tail $file_path]',
                                    'EOF',
                                    'echo -e "" >> /config/verifyHash',
                                    'cat <<\'EOF\' >> /config/verifyHash',
                                    '            if {![info exists hashes($file_name)]} {',
                                    '                tmsh::log err \"No hash found for $file_name\"',
                                    '                exit 1',
                                    '            }',
                                    'EOF',
                                    'echo -e "" >> /config/verifyHash',
                                    'cat <<\'EOF\' >> /config/verifyHash',
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
                                    '    script-signature jJpTQ0bcHm9SypZSOPeKaHoUKRdTyLbz80xHYXy39dWx76geCGT5otZi4SdqGBiiwKFydQTqSVu+Uzj8TQZGg2fbxKg/Ks28Ht+nvLoTiNwZGY5o+iPse45QvltBvE+aCOIaw8a5ZBd5ZMF7A8JQpTwttUFRjFgXFu9CncAWOTypov46ve9dzRW8dRPbAImaJSby38jUIVWjv2iB3qZHz//bXjdZ5qUpFvpPH5dGzYN5SoQmUVI3kbiOpZlRJcSj8cKzQ7EsQozile5JkzPrzUeeMgOHihAZcOzgvYWl2LYe9iedixzF7ci6d4YNUuUhFfyrlrUOZSMUPtRzM3+rYQ==',                                    '    signing-key /Common/f5-irule',
                                    '}',
                                    'EOF\n',
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
                                    'f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/autoscale.js --cloud gce --provider-options \'storageBucket:' + storageName + ',mgmtPort:' + str(context.properties['manGuiPort']) + ',serviceAccount:' + context.properties['serviceAccount'] + ',instanceGroup:' + deployment + '-igm\' --host localhost --port 8443 --user cluster_admin --password-url file:///config/cloud/gce/.adminPassword --password-encrypted --device-group autoscale-group --cluster-action update --log-level debug --output /var/log/cloud/google/autoscale.log',
                                    'EOF',
                                    'cat <<\'EOF\' > /config/cloud/gce/run_autoscale_backup.sh',
                                    '#!/bin/bash',
                                    'f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/autoscale.js --cloud gce --provider-options \'storageBucket:' + storageName + ',mgmtPort:' + str(context.properties['manGuiPort']) + ',serviceAccount:' + context.properties['serviceAccount'] + ',instanceGroup:' + deployment + '-igm\' --host localhost --port 8443 --user cluster_admin --password-url file:///config/cloud/gce/.adminPassword --password-encrypted --device-group autoscale-group --cluster-action backup-ucs --log-level debug --output /var/log/cloud/google/autoscale.log',
                                    'EOF',
                                    'cat <<\'EOF\' > /config/cloud/gce/custom-config.sh',
                                    '#!/bin/bash',
                                    'date',
                                    'echo "starting custom-config.sh"',                                  
                                    'tmsh save /sys config',
                                    'echo "Attempting to Join or Initiate Autoscale Cluster"',
                                    'useServiceDiscovery=' + str(context.properties['tagValue']),
                                    '(crontab -l 2>/dev/null; echo \'*/1 * * * * /config/cloud/gce/run_autoscale_update.sh\') | crontab -',
                                    '(crontab -l 2>/dev/null; echo \'59 23 * * * /config/cloud/gce/run_autoscale_backup.sh\') | crontab -',
                                    'f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/autoscale.js --cloud gce --provider-options \'storageBucket:' + storageName + ',mgmtPort:' + str(context.properties['manGuiPort']) + ',serviceAccount:' + context.properties['serviceAccount'] + ',instanceGroup:' + deployment + '-igm\' --host localhost --port 8443 --user cluster_admin --password-url file:///config/cloud/gce/.adminPassword --password-encrypted --device-group autoscale-group --block-sync -c join --log-level debug -o /var/log/cloud/google/autoscale.log',
                                    'if [ -f /config/cloud/master ];then',
                                    '  if $(jq \'.ucsLoaded\' < /config/cloud/master);then',
                                    '    echo "UCS backup loaded from backup folder in storage: ' + storageName + '."',
                                    '  else',                      
                                    '    echo "SELF-SELECTED as Master ... Initiated Autoscale Cluster ... Loading default config"',
                                    '    tmsh modify cm device-group autoscale-group asm-sync enabled',
                                    '    tmsh load sys application template /config/cloud/f5.http.v1.2.0rc7.tmpl',
                                    '    tmsh load sys application template /config/cloud/f5.service_discovery.tmpl',
                                    '    source /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/waitForBigip.sh;wait-for-bigip',
                                    '    ### START CUSTOM CONFIGURTION:  Policy Name/Policy URL, etc. ',
                                    '    tmsh load asm policy file /config/cloud/asm-policy-linux-' + context.properties['policyLevel'] + '.xml',
                                    '    # modify asm policy names below (ex. /Common/linux-' + context.properties['policyLevel'] + ') to match policy name in the xml file',
                                    '    tmsh modify asm policy /Common/linux-'+ context.properties['policyLevel'] + ' active',
                                    '    tmsh create ltm policy app-ltm-policy strategy first-match legacy',
                                    '    tmsh modify ltm policy app-ltm-policy controls add { asm }',
                                    '    tmsh modify ltm policy app-ltm-policy rules add { associate-asm-policy { actions replace-all-with { 0 { asm request enable policy /Common/linux-' + context.properties['policyLevel'] + ' } } } }',
                                    '    # deploy logging profiles',
                                    '    # profile names',
                                    '    local_asm_log_name=\'Log illegal requests\'',
                                    '    if [ -n "${useServiceDiscovery}" ];then',
                                    '        tmsh create ltm pool ' + deployment + ' { monitor http load-balancing-mode least-connections-member }',
                                    '        tmsh create sys application service ' + deployment + ' { device-group autoscale-group template f5.http.v1.2.0rc7 lists add { asm__security_logging { value { \"${local_asm_log_name}\" } } } tables add { pool__hosts { column-names { name } rows {{ row { ' + str(context.properties['applicationDnsName']) + ' }}}}} variables add { pool__pool_to_use { value /Common/' + deployment + ' } asm__use_asm { value /Common/app-ltm-policy } pool__addr { value 0.0.0.0 } pool__mask { value 0.0.0.0 } pool__port { value ' + str(context.properties['applicationPort']) + ' } monitor__http_version { value http11 } }}',
                                    '        tmsh create sys application service ' + deployment + '_sd { template f5.service_discovery variables add { basic__advanced { value no } basic__display_help { value hide } cloud__cloud_provider { value gce }  cloud__gce_region { value \\"/#default#\\" } pool__interval { value 15 } pool__member_conn_limit { value 0 } pool__member_port { value ' + str(context.properties['applicationPort']) + ' } pool__pool_to_use { value /Common/' + deployment + ' } pool__public_private {value private} pool__tag_key { value ' + str(context.properties['tagName']) + ' } pool__tag_value { value ' + str(context.properties['tagValue']) + ' } } }',
                                    '    else',
                                    '        tmsh create ltm node ' + deployment + ' fqdn { name ' + str(context.properties['applicationDnsName']) + ' }',
                                    '        tmsh create sys application service ' + deployment + ' { device-group autoscale-group template f5.http.v1.2.0rc7 lists add { asm__security_logging { value { \"${local_asm_log_name}\" } } } tables add { pool__hosts { column-names { name } rows { { row { ' + str(context.properties['applicationDnsName']) + ' } } } } pool__members { column-names { addr port connection_limit } rows { { row { /Common/' + deployment + ' ' + str(context.properties['applicationPort']) + ' 0 } } } } } variables add { pool__pool_to_use { value \"/#create_new#\" } asm__use_asm { value /Common/app-ltm-policy } pool__addr { value 0.0.0.0 } pool__mask { value 0.0.0.0 } pool__port { value ' + str(context.properties['applicationPort']) + ' } ssl_mode { value no_ssl } monitor__http_version { value http11 } }}',
                                    '    fi',
                                    '    ### END CUSTOM CONFIGURATION',
                                    '    tmsh save /sys config',
                                    '    bigstart restart restnoded',
                                    '    f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/autoscale.js --cloud gce --provider-options \'storageBucket:' + storageName + ',mgmtPort:' + str(context.properties['manGuiPort']) + ',serviceAccount:' + context.properties['serviceAccount'] + ',instanceGroup:' + deployment + '-igm\' --host localhost --port 8443 --user cluster_admin --password-url file:///config/cloud/gce/.adminPassword --password-encrypted -c unblock-sync --log-level debug --output /var/log/cloud/google/autoscale.log',
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
                                    'curl -s -f --retry 20 -o /config/cloud/f5-cloud-libs.tar.gz https://raw.githubusercontent.com/F5Networks/f5-cloud-libs/v4.2.0/dist/f5-cloud-libs.tar.gz',
                                    'curl -s -f --retry 20 -o /config/cloud/f5-cloud-libs-gce.tar.gz https://raw.githubusercontent.com/F5Networks/f5-cloud-libs-gce/v2.1.0/dist/f5-cloud-libs-gce.tar.gz',
                                    'curl -s -f --retry 20 -o /config/cloud/f5.service_discovery.tmpl https://raw.githubusercontent.com/F5Networks/f5-cloud-iapps/v2.0.3/f5-service-discovery/f5.service_discovery.tmpl',
                                    'curl -s -f --retry 20 -o /config/cloud/f5.http.v1.2.0rc7.tmpl http://cdn.f5.com/product/blackbox/aws/f5.http.v1.2.0rc7.tmpl',
                                    'curl -s -f --retry 20 -o /config/cloud/asm-policy-linux.tar.gz http://cdn.f5.com/product/blackbox/aws/asm-policy-linux.tar.gz',
                                    'chmod 755 /config/verifyHash',
                                    'chmod 755 /config/installCloudLibs.sh',
                                    'chmod 755 /config/waitThenRun.sh',
                                    'chmod 755 /config/cloud/gce/custom-config.sh',
                                    'chmod 755 /config/cloud/gce/rm-password.sh',
                                    'chmod 755 /config/cloud/gce/run_autoscale_update.sh',
                                    'chmod 755 /config/cloud/gce/run_autoscale_backup.sh',
                                    'mkdir -p /var/log/cloud/google',
                                    'nohup /config/installCloudLibs.sh &>> /var/log/cloud/google/install.log < /dev/null &',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/runScript.js --signal PASSWORD_CREATED --file f5-rest-node --cl-args \'/config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/generatePassword --file /config/cloud/gce/.adminPassword --encrypt\' --log-level debug -o /var/log/cloud/google/generatePassword.log &>> /var/log/cloud/google/install.log < /dev/null &',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/runScript.js --wait-for PASSWORD_CREATED --signal ADMIN_CREATED --file /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/createUser.sh --cl-args \'--user cluster_admin --password-file /config/cloud/gce/.adminPassword --password-encrypted\' --log-level debug -o /var/log/cloud/google/createUser.log &>> /var/log/cloud/google/install.log < /dev/null &',
                                    CUSTHASH,
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/onboard.js --port 8443 --ssl-port ' + str(context.properties['manGuiPort']) + ' --wait-for ADMIN_CREATED -o /var/log/cloud/google/onboard.log --log-level debug --no-reboot --host localhost --user cluster_admin --password-url file:///config/cloud/gce/.adminPassword --password-encrypted --hostname $(curl http://metadata.google.internal/computeMetadata/v1/instance/hostname -H "Metadata-Flavor: Google") --ntp 0.us.pool.ntp.org --ntp 1.us.pool.ntp.org --tz UTC --module ltm:nominal --module asm:nominal --db provision.1nicautoconfig:disable' + SENDANALYTICS + ' &>> /var/log/cloud/google/install.log < /dev/null &',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/runScript.js --file /config/cloud/gce/custom-config.sh --cwd /config/cloud/gce -o /var/log/cloud/google/custom-config.log --log-level debug --wait-for ONBOARD_DONE --signal CUSTOM_CONFIG_DONE &>> /var/log/cloud/google/install.log < /dev/null &',
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