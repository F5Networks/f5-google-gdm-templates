# Copyright 2018 F5 Networks All rights reserved.
#
# Version v2.1.0

""" Creates Deployment """
COMPUTE_URL_BASE = 'https://www.googleapis.com/compute/v1/'
def FirewallRuleApp(context):
    # Build Application firewall rule
    ports = str(context.properties['applicationPort']).split()
    source_list = str(context.properties['restrictedSrcAddressApp']).split()
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
                "ports": ['443','22'],
                },
            ]
        }
    }
    return firewallRuleMgmt
def Instance(context):
    # declare specific instance properties ahead of time as they may change
    network_interfaces = [{
                'network': ''.join([COMPUTE_URL_BASE, 'projects/',
                                    context.env['project'], '/global/networks/',
                                    context.properties['network1']]),
                'subnetwork': ''.join([COMPUTE_URL_BASE, 'projects/',
                                    context.env['project'], '/regions/',
                                    context.properties['region'], '/subnetworks/',
                                    context.properties['subnet1']]),
                'accessConfigs': [{
                    'name': 'External NAT',
                    'type': 'ONE_TO_ONE_NAT'
                }],
            },
            {
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
            },
                {
                'network': ''.join([COMPUTE_URL_BASE, 'projects/',
                                    context.env['project'], '/global/networks/',
                                    context.properties['network2']]),
                'subnetwork': ''.join([COMPUTE_URL_BASE, 'projects/',
                                    context.env['project'], '/regions/',
                                    context.properties['region'], '/subnetworks/',
                                    context.properties['subnet2']]),
    }]
    # If not 'DYNAMIC'|'' assume a static address is needed
    mgmtSubnetAddress = context.properties['mgmtSubnetAddress'].upper()
    if mgmtSubnetAddress != "DYNAMIC" and mgmtSubnetAddress != "":
        network_interfaces[1]['networkIP'] = mgmtSubnetAddress
    subnet1Address = context.properties['subnet1Address'].upper()
    if subnet1Address != "DYNAMIC" and subnet1Address != "":
        network_interfaces[0]['networkIP'] = subnet1Address

    # Determine if service account has been supplied
    if context.properties['serviceAccount']:
        service_account = [{
                'email': str(context.properties['serviceAccount']),
                'scopes': ['https://www.googleapis.com/auth/compute']
        }]
    else:
         service_account = []
    # Build instance template
    instance = {
        'name': 'bigip1-' + context.env['deployment'],
        'type': 'compute.v1.instance',
        'properties': {
            'canIpForward': True,
            'description': 'F5 BIG-IP configured with three interfaces.',
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
            'machineType': ''.join([COMPUTE_URL_BASE, 'projects/',
                                    context.env['project'], '/zones/',
                                    context.properties['availabilityZone1'], '/machineTypes/',
                                    context.properties['instanceType']]),
            'networkInterfaces': network_interfaces,
            'serviceAccounts': service_account,
            'tags': {
                'items': ['mgmtfw-' + context.env['deployment'],'appfw-' + context.env['deployment']]
            },
            'zone': context.properties['availabilityZone1'],
            'metadata': Metadata(context)
        }
    }
    return instance
def Metadata(context):
    ALLOWUSAGEANALYTICS = context.properties['allowUsageAnalytics']
    if ALLOWUSAGEANALYTICS:
        CUSTHASH = 'CUSTOMERID=`curl -s "http://metadata.google.internal/computeMetadata/v1/project/numeric-project-id" -H "Metadata-Flavor: Google" |sha512sum|cut -d " " -f 1`;\nDEPLOYMENTID=`curl -s "http://metadata.google.internal/computeMetadata/v1/instance/id" -H "Metadata-Flavor: Google"|sha512sum|cut -d " " -f 1`;'
        SENDANALYTICS = ' --metrics "cloudName:google,region:' + context.properties['region'] + ',bigipVersion:' + context.properties['imageName'] + ',customerId:${CUSTOMERID},deploymentId:${DEPLOYMENTID},templateName:f5-existing-stack-byol-3nic-bigip.py,templateVersion:v2.1.0,licenseType:byol"'
    else:
        CUSTHASH = 'echo "No analytics."'
        SENDANALYTICS = ''
    ntp_servers = str(context.properties['ntpServer']).split()
    ntp_list = ''
    for ntp_server in ntp_servers:
        ntp_list = ntp_list + ' --ntp ' + ntp_server
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
                                    'echo expanding f5-cloud-libs.tar.gz\n',
                                    'tar xvfz /config/cloud/f5-cloud-libs.tar.gz -C /config/cloud/gce/node_modules/@f5devcentral',
                                    'echo expanding f5-cloud-libs-gce.tar.gz',
                                    'tar xvfz /config/cloud/f5-cloud-libs-gce.tar.gz -C /config/cloud/gce/node_modules/@f5devcentral',
                                    'echo cloud libs install complete',
                                    'touch /config/cloud/cloudLibsReady',
                                    'EOF',
                                    'cat <<\'EOF\' > /config/verifyHash',
                                    'cli script /Common/verifyHash {',
                                    'proc script::run {} {',
                                    '        if {[catch {',
                                    '            set hashes(f5-cloud-libs.tar.gz) 535059811324dbda9783df2c4f7ac8405acf6f198efd5696bc0d90f4f8f645b77c04efd42c3dc94261f0b92d76cbae87613412531968a5e646baf4177807b953',
                                    '            set hashes(f5-cloud-libs-aws.tar.gz) 076c969cbfff12efacce0879820262b7787c98645f1105667cc4927d4acfe2466ed64c777b6d35957f6df7ae266937dde42fef4c8b1f870020a366f7f910ffb5',
                                    '            set hashes(f5-cloud-libs-azure.tar.gz) eea34eb9bf1fc86702cc8d3adcd0cd4cd3e8ede0bad5d85ce55b7248aeb5726583b0314bd1ac9383dbfbf97c79d08d27a473539844de6972c9f6f5fea1a7b9aa',
                                    '            set hashes(f5-cloud-libs-gce.tar.gz) 605c13c0725dcf6ee96d24349aee68be59640c58fef16d42d69fe1b01fb2e59df14f2cd41f0718d21061b8fb52cdce57fcf6541ebc8610e54e0f7fe8e46d94cb',
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
                                    '            set hashes(f5.service_discovery.tmpl) 0c43a28d58ff8339891ef324763675c29275170f8984d39298a53f570385eef82bef6d5a273adebb5310fc529faffc9b225358ec8f65100115246915eff706fe',
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
                                    '    script-signature hCr5O6FtvOkjRk8Vn1499YU57spPEMbLXCfkgLVsVcmBCXnHbRw6zTIZOJlGkwk7CyCTpcuVuTR1SiGsQKnclgcQFkEDP5rw98jyIwvKpfYXiLxPI2SPsyadom41FDPXy9+b4aOAJGRPcp5/HhRP7+ky7x6jI5SEF4ZFExN6BwWXn61D+MwYe2Ajhes/6wuZv+b9i9teckZLkyB54OAbEyEug3S66YK2Jg916Y5JLNhDn7JNoOPoyFvYlyuDOutcjFHiwjdSFEgcOx/dka/5aHtjKEiMWuCsuaZnhGKSHc/ZCTH8oht1qUi28Dz5W2Gq6hRE9Zt5S4HmS3JKu2wlfg==',                                    '    signing-key /Common/f5-irule',
                                    '}',
                                    'EOF',
                                    '# empty new line chars get stripped, strip out place holder NEW_LINE',
                                    'sed -i "s/NEW_LINE//" /config/verifyHash',
                                    'cat <<\'EOF\' > /config/waitThenRun.sh',
                                    '#!/bin/bash',
                                    'while true; do echo \"waiting for cloud libs install to complete\"',
                                    '    if [ -f /config/cloud/cloudLibsReady ]; then',
                                    '        echo "Running f5-cloud-libs Version:"',
                                    '        f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/onboard.js --version',
                                    '        break',
                                    '    else',
                                    '        sleep 10',
                                    '    fi',
                                    'done',
                                    '\"$@\"',
                                    'EOF',
                                    'cat <<\'EOF\' > /config/cloud/gce/collect-interface.sh',
                                    '#!/bin/bash',
                                    'echo "MGMTADDRESS=$(curl -s -f --retry 20 \'http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/1/ip\' -H \'Metadata-Flavor: Google\')" >> /config/cloud/gce/interface.config',
                                    'echo "MGMTMASK=$(curl -s -f --retry 20 \'http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/1/subnetmask\' -H \'Metadata-Flavor: Google\')" >> /config/cloud/gce/interface.config',
                                    'echo "MGMTGATEWAY=$(curl -s -f --retry 20 \'http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/1/gateway\' -H \'Metadata-Flavor: Google\')" >> /config/cloud/gce/interface.config',
                                    'echo "INT1ADDRESS=$(curl -s -f --retry 20 \'http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/ip\' -H \'Metadata-Flavor: Google\')" >> /config/cloud/gce/interface.config',
                                    'echo "INT1MASK=$(curl -s -f --retry 20 \'http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/subnetmask\' -H \'Metadata-Flavor: Google\')" >> /config/cloud/gce/interface.config',
                                    'echo "INT1GATEWAY=$(curl -s -f --retry 20 \'http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/gateway\' -H \'Metadata-Flavor: Google\')" >> /config/cloud/gce/interface.config',
                                    'echo "INT2ADDRESS=$(curl -s -f --retry 20 \'http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/2/ip\' -H \'Metadata-Flavor: Google\')" >> /config/cloud/gce/interface.config',
                                    'echo "INT2MASK=$(curl -s -f --retry 20 \'http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/2/subnetmask\' -H \'Metadata-Flavor: Google\')" >> /config/cloud/gce/interface.config',
                                    'echo "INT2GATEWAY=$(curl -s -f --retry 20 \'http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/2/gateway\' -H \'Metadata-Flavor: Google\')" >> /config/cloud/gce/interface.config',
                                    'chmod 755 /config/cloud/gce/interface.config',
                                    'EOF',
                                    'cat <<\'EOF\' > /config/cloud/gce/custom-config.sh',
                                    '#!/bin/bash',
                                    'function mcp_running {',
                                    '  checks=0',
                                    '  while [ $checks -lt 120 ] ; do',
                                    '    /usr/bin/tmsh -a show sys mcp-state field-fmt | grep -q running',
                                    '    if [ $? == 0 ]; then',
                                    '      log "MCPD ready"',
                                    '      break',
                                    '    fi',
                                    '    log "MCPD not ready: $checks"',
                                    '    let checks=checks+1',
                                    '    sleep 5',
                                    '  done',
                                    '}',
                                    'mcp_running',
                                    'source /config/cloud/gce/interface.config',
                                    'MGMTNETWORK=$(/bin/ipcalc -n ${MGMTADDRESS} ${MGMTMASK} | cut -d= -f2)',
                                    'INT1NETWORK=$(/bin/ipcalc -n ${INT1ADDRESS} ${INT1MASK} | cut -d= -f2)',
                                    'INT2NETWORK=$(/bin/ipcalc -n ${INT2ADDRESS} ${INT2MASK} | cut -d= -f2)',
                                    'PROGNAME=$(basename $0)',
                                    'function error_exit {',
                                    'echo \"${PROGNAME}: ${1:-\\\"Unknown Error\\\"}\" 1>&2',
                                    'exit 1',
                                    '}',
                                    'declare -a tmsh=()',
                                    'date',
                                    'echo "starting custom-config.sh"',
                                    'useServiceDiscovery=' + str(context.properties['tagValue']),
                                    'if [ -n "${useServiceDiscovery}" ] && [ "${useServiceDiscovery}" != "None" ];then',
                                    '   tmsh+=('
                                    '   \'tmsh load sys application template /config/cloud/f5.service_discovery.tmpl\'',
                                    '   \'tmsh create /sys application service serviceDiscovery template f5.service_discovery variables add { basic__advanced { value no } basic__display_help { value hide } cloud__cloud_provider { value gce }  cloud__gce_region { value \"/#default#\" } monitor__frequency { value 30 } monitor__http_method { value GET } monitor__http_verison { value http11 } monitor__monitor { value \"/#create_new#\"} monitor__response { value \"\" } monitor__uri { value / } pool__interval { value 60 } pool__member_conn_limit { value 0 } pool__member_port { value 80 } pool__pool_to_use { value \"/#create_new#\" } pool__public_private {value private} pool__tag_key { value ' + str(context.properties['tagName']) + '} pool__tag_value { value ' + str(context.properties['tagValue']) + ' } }\')',
                                    'else',
                                    '   tmsh+=(',
                                    '   \'tmsh load sys application template /config/cloud/f5.service_discovery.tmpl\')',
                                    'fi',
                                    'tmsh+=(',
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
                                    '"tmsh create net self self_internal address ${INT2ADDRESS}/32 vlan internal"',
                                    '"tmsh create net route int_gw_interface network ${INT2GATEWAY}/32 interface internal"',
                                    '"tmsh create net route int_rt network ${INT2NETWORK}/${INT2MASK} gw ${INT2GATEWAY}"',
                                    '"tmsh save /sys config"',
                                    '"bigstart restart restnoded")',
                                    'for CMD in "${tmsh[@]}"',
                                    'do',
                                    '    if $CMD;then',
                                    '        echo \"command $CMD successfully executed."',
                                    '    else',
                                    '        error_exit "$LINENO: An error has occurred while executing $CMD. Aborting!"',
                                    '    fi',
                                    'done',
                                    'date',
                                    '### START CUSTOM TMSH CONFIGURATION',
                                    '### END CUSTOM TMSH CONFIGURATION',
                                    'EOF',
                                    'curl -s -f --retry 20 -o /config/cloud/f5-cloud-libs.tar.gz https://cdn.f5.com/product/cloudsolutions/f5-cloud-libs/v4.6.0/f5-cloud-libs.tar.gz',
                                    'curl -s -f --retry 20 -o /config/cloud/f5-cloud-libs-gce.tar.gz https://cdn.f5.com/product/cloudsolutions/f5-cloud-libs-gce/v2.3.2/f5-cloud-libs-gce.tar.gz',
                                    'curl -s -f --retry 20 -o /config/cloud/f5-appsvcs-3.5.1-5.noarch.rpm https://cdn.f5.com/product/cloudsolutions/f5-appsvcs-extension/v3.6.0/dist/lts/f5-appsvcs-3.5.1-5.noarch.rpm',
                                    'curl -s -f --retry 20 -o /config/cloud/f5.service_discovery.tmpl https://cdn.f5.com/product/cloudsolutions/iapps/common/f5-service-discovery/v2.2.3/f5.service_discovery.tmpl',
                                    'chmod 755 /config/verifyHash',
                                    'chmod 755 /config/installCloudLibs.sh',
                                    'chmod 755 /config/waitThenRun.sh',
                                    'chmod 755 /config/cloud/gce/custom-config.sh',
                                    'chmod 755 /config/cloud/gce/rm-password.sh',
                                    'chmod 755 /config/cloud/gce/collect-interface.sh',
                                    'mkdir -p /var/log/cloud/google',
                                    'nohup /config/installCloudLibs.sh &>> /var/log/cloud/google/install.log < /dev/null &',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/onboard.js --version &>> /var/log/cloud/google/install.log < /dev/null &',
                                    CUSTHASH,
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/onboard.js --db provision.managementeth:eth1 --port 443 --ssl-port ' + str(context.properties['mgmtGuiPort']) + ' -o /var/log/cloud/google/onboard.log --log-level ' + str(context.properties['logLevel']) + ' --install-ilx-package file:///config/cloud/f5-appsvcs-3.5.1-5.noarch.rpm --host localhost ' + ntp_list + ' --tz ' + str(context.properties['timezone']) + ' --module ltm:nominal --license ' + context.properties['licenseKey1'] + SENDANALYTICS + ' &>> /var/log/cloud/google/install.log < /dev/null &',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/runScript.js --file /config/cloud/gce/collect-interface.sh --cwd /config/cloud/gce -o /var/log/cloud/google/interface-config.log --log-level ' + str(context.properties['logLevel']) + ' --wait-for ONBOARD_DONE --signal INT_COLLECTION_DONE &>> /var/log/cloud/google/install.log < /dev/null &',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/network.js --host localhost --force-reboot -o /var/log/cloud/google/network.log --log-level ' + str(context.properties['logLevel']) + ' --wait-for INT_COLLECTION_DONE --signal NETWORK_CONFIG_DONE  &>> /var/log/cloud/google/install.log < /dev/null &',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/runScript.js --file /config/cloud/gce/custom-config.sh --cwd /config/cloud/gce -o /var/log/cloud/google/custom-config.log --log-level ' + str(context.properties['logLevel']) + ' --wait-for NETWORK_CONFIG_DONE --signal CUSTOM_CONFIG_DONE &>> /var/log/cloud/google/install.log < /dev/null &',
                                    'touch /config/startupFinished',
                                    ])
                            )
                }]
    }
    return metadata
def Outputs(context):
    outputs = [{
        'name': 'region',
        'value': context.properties['region']
    },
    {
        'name': 'selfLink',
        'value': '$(ref.{}.selfLink)'.format('bigip1-' + context.env['deployment'])
    },
    {
        'name': 'mgmtURL',
        'value': 'https://$(ref.bigip1-' + context.env['deployment'] + '.networkInterfaces[1].accessConfigs[0].natIP):' + str(context.properties['mgmtGuiPort'])
    },
    {
        'name': 'appTrafficAddress',
        'value': '$(ref.bigip1-' + context.env['deployment'] + '.networkInterfaces[0].accessConfigs[0].natIP)'
    }]
    return outputs
def GenerateConfig(context):
    ## set variables

    # build resources
    resources = [
        Instance(context),
        FirewallRuleApp(context),
        FirewallRuleMgmt(context),
    ]
    outputs = Outputs(context)
    return {'resources': resources, 'outputs': outputs}