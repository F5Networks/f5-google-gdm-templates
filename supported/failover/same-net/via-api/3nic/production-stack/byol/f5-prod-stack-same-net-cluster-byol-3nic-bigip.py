# Copyright 2018 F5 Networks All rights reserved.
#
# Version v2.1.3

"""Creates BIG-IP"""
COMPUTE_URL_BASE = 'https://www.googleapis.com/compute/v1/'
def Metadata(context, group, storageName, licenseType):
  # SETUP VARIABLES
  ## Template Analytics
  ALLOWUSAGEANALYTICS = context.properties['allowUsageAnalytics']
  if ALLOWUSAGEANALYTICS == "yes":
    CUSTHASH = 'CUSTOMERID=`curl -s "http://metadata.google.internal/computeMetadata/v1/project/numeric-project-id" -H "Metadata-Flavor: Google" |sha512sum|cut -d " " -f 1`;\nDEPLOYMENTID=`curl -s "http://metadata.google.internal/computeMetadata/v1/instance/id" -H "Metadata-Flavor: Google"|sha512sum|cut -d " " -f 1`;'
    SENDANALYTICS = ' --metrics "cloudName:google,region:' + context.properties['region'] + ',bigipVersion:' + context.properties['imageName'] + ',customerId:${CUSTOMERID},deploymentId:${DEPLOYMENTID},templateName:f5-prod-stack-same-net-cluster-byol-3nic-bigip.py,templateVersion:v2.1.1,licenseType:byol"'
  else:
    CUSTHASH = '# No template analytics'
    SENDANALYTICS = ''
  ## PREFIX
  DOTMASK = 'dotmask=`prefix2mask ' + context.properties['mask1'] + '`'
  DOTMASK2 = 'dotmask2=`prefix2mask ' + context.properties['mask2'] + '`'
  ## Service Discovery
  USESD = 'useServiceDiscovery=\'' + context.properties['tagValue'] + '\''
  SDAPP = '   \'tmsh create /sys application service serviceDiscovery template f5.service_discovery variables add { basic__advanced { value no } basic__display_help { value hide } cloud__cloud_provider { value gce }  cloud__gce_region { value \"/#default#\" } monitor__frequency { value 30 } monitor__http_method { value GET } monitor__http_verison { value http11 } monitor__monitor { value \"/#create_new#\"} monitor__response { value \"\" } monitor__uri { value / } pool__interval { value 60 } pool__member_conn_limit { value 0 } pool__member_port { value 80 } pool__pool_to_use { value \"/#create_new#\" } pool__public_private {value private} pool__tag_key { value ' + context.properties['tagName'] + ' } pool__tag_value { value ' + context.properties['tagValue'] + ' } }\')'
  ## Routes
  EXTRT = '\"tmsh create net route ext_rt network ${network}/' + context.properties['mask1'] + ' gw ${GATEWAY}\"'
  INTRT = '\"tmsh create net route int_rt network ${network2}/' + context.properties['mask2'] + ' gw ${GATEWAY2}\"'
  ## Onboard
  if group == "create" and licenseType == "byol":
    LICENSE = '--license '+ context.properties['licenseKey1']
  elif group == "join" and licenseType == "byol":
    LICENSE = '--license ' + context.properties['licenseKey2']
  else:
    LICENSE = ''
  ONBOARDJS = ' '.join ([ "nohup /config/waitThenRun.sh",
                          "f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/onboard.js",
                          "--port 443",
                          "--ssl-port",
                          "'" + context.properties['mgmtGuiPort'] + "'",
                          "--wait-for ADMIN_CREATED",
                          "-o /var/log/cloud/google/onboard.log",
                          "--log-level debug",
                          "--no-reboot",
                          "--install-ilx-package file:///config/cloud/f5-appsvcs-3.5.1-5.noarch.rpm",
                          "--host localhost",
                          "--user admin",
                          "--password-url file:///config/cloud/gce/.adminPassword",
                          "--password-encrypted",
                          "--hostname $(curl -s -f --retry 20 \"http://metadata.google.internal/computeMetadata/v1/instance/hostname\" -H \"Metadata-Flavor: Google\")",
                          "--ntp 0.us.pool.ntp.org",
                          "--ntp 1.us.pool.ntp.org",
                          "--tz UTC",
                          "--module ltm:nominal",
                          LICENSE + SENDANALYTICS,
                          "&>> /var/log/cloud/google/install.log < /dev/null &"
                        ])
  ## Cluster
  if group == "create":
    CLUSTERJS = ' '.join(["HOSTNAME=$(curl -s -f --retry 20 \"http://metadata.google.internal/computeMetadata/v1/instance/hostname\" -H \"Metadata-Flavor: Google\");INT2ADDRESS=$(curl -s -f --retry 20 \"http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/2/ip\" -H \"Metadata-Flavor: Google\");nohup /config/waitThenRun.sh",
                          "f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/cluster.js",
                          "--wait-for CUSTOM_CONFIG_DONE",
                          "--signal CLUSTER_DONE",
                          "-o /var/log/cloud/google/cluster.log",
                          "--log-level silly",
                          "--host localhost",
                          "--user admin",
                          "--password-url file:///config/cloud/gce/.adminPassword",
                          "--password-encrypted",
                          "--cloud gce",
                          "--provider-options 'region:" + context.properties['region'] + ",storageBucket:" + storageName  + "'",
                          "--master",
                          "--config-sync-ip ${INT2ADDRESS}",
                          "--create-group",
                          "--device-group failover_group",
                          "--sync-type sync-failover",
                          "--network-failover",
                          "--device ${HOSTNAME}",
                          "--auto-sync",
                          "&>> /var/log/cloud/google/install.log < /dev/null &"
    ])
  elif group == "join":
    CLUSTERJS = ' '.join(["INT2ADDRESS=$(curl -s -f --retry 20 \"http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/2/ip\" -H \"Metadata-Flavor: Google\");nohup /config/waitThenRun.sh",
                          "f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/cluster.js",
                          "--wait-for CUSTOM_CONFIG_DONE",
                          "--signal CLUSTER_DONE",
                          "-o /var/log/cloud/google/cluster.log",
                          "--log-level silly",
                          "--host localhost",
                          "--user admin",
                          "--password-url file:///config/cloud/gce/.adminPassword",
                          "--password-encrypted",
                          "--cloud gce",
                          "--provider-options 'region:" + context.properties['region'] + ",storageBucket:" + storageName  + "'",
                          "--config-sync-ip ${INT2ADDRESS}",
                          "--join-group",
                          "--device-group failover_group",
                          "--remote-host ",
                          "$(ref.bigip1-" + context.env['deployment'] + ".networkInterfaces[0].networkIP)",
                          "&>> /var/log/cloud/google/install.log < /dev/null &"
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
                                    'touch /config/cloud/cloudLibsReady',
                                    'EOF',
                                    'cat <<\'EOF\' > /config/verifyHash',
                                    'cli script /Common/verifyHash {',
                                    'proc script::run {} {',
                                    '        if {[catch {',
                                    '            set hashes(f5-cloud-libs.tar.gz) 18f1d7db0fe52eceb72aa2f2b56152926c126d153f0f65953441fea79a756c3c5ff847da2ed7b70c153da5490ffd54e3f93eaab33e8d6df46619a525b26e3505',
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
                                    '    script-signature Nbpb2UCK1Rcn2WrsZvPhOlXQ7N6CMLcFtjCm+VnfPVYiAONJvsqEOAv8ohgg7yiTV95sL7uwNUwAfxBwzJ1oSXSHBz4/VSMEopvH0+GmdrvHzHFmWT9VOJYm+OMzd/xngMfFZesFrtWcJ9BwhnBcmqVfEv1ueGOPYbXvbz2NuyT8CTNqy4MizzWYhouYqTX8OeTk1ts+nCd+D6fm31xKhUgChx1bw5H6VnuTntbe2kWw5R+KW+Jk2J45EEk4/5rrzYqH9uJhVNegPEPf0QckniILC5WBUPtvOqKoAHxpLgJntnEVzMDnWQdqYoOvtgAKHzYFDFlWZrcsGq7/ywE4vQ==',                                    '    signing-key /Common/f5-irule',
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
                                    'cat <<\'EOF\' > /config/cloud/gce/custom-config.sh',
                                    '#!/bin/bash',
                                    'HOSTNAME=$(curl -s -f --retry 20 \"http://metadata.google.internal/computeMetadata/v1/instance/hostname\" -H \"Metadata-Flavor: Google\")',
                                    '# Grab ip address assined to 1.1',
                                    'INT1ADDRESS=`curl -s -f --retry 20 \"http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/1/ip\" -H \"Metadata-Flavor: Google\"`',
                                    '# Grab ip address assined to 1.2',
                                    'INT2ADDRESS=`curl -s -f --retry 20 \"http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/2/ip\" -H \"Metadata-Flavor: Google\"`',
                                    '# Determine network from self ip and netmask given',
                                    'prefix2mask() {',
                                    '   local i mask=""',
                                    '   local octets=$(($1/8))',
                                    '   local part_octet=$(($1%8))',
                                    '   for ((i=0;i<4;i+=1)); do',
                                    '       if [ $i -lt $octets ]; then',
                                    '           mask+=255',
                                    '       elif [ $i -eq $octets ]; then',
                                    '           mask+=$((256 - 2**(8-$part_octet)))',
                                    '       else',
                                    '           mask+=0',
                                    '       fi',
                                    '       test $i -lt 3 && mask+=.',
                                    '   done',
                                    '   echo $mask',
                                    '}',
                                    DOTMASK,
                                    DOTMASK2,
                                    'IFS=. read -r i1 i2 i3 i4 <<< ${INT1ADDRESS}',
                                    'IFS=. read -r m1 m2 m3 m4 <<< ${dotmask}',
                                    'network=`printf "%d.%d.%d.%d" "$((i1 & m1))" "$((i2 & m2))" "$((i3 & m3))" "$((i4 & m4))"`',
                                    'GATEWAY=$(echo "`echo $network |cut -d"." -f1-3`.$((`echo $network |cut -d"." -f4` + 1))")',
                                    'IFS=. read -r i1 i2 i3 i4 <<< ${INT2ADDRESS}',
                                    'IFS=. read -r m1 m2 m3 m4 <<< ${dotmask2}',
                                    'network2=`printf "%d.%d.%d.%d" "$((i1 & m1))" "$((i2 & m2))" "$((i3 & m3))" "$((i4 & m4))"`',
                                    'GATEWAY2=$(echo "`echo $network2 |cut -d"." -f1-3`.$((`echo $network2 |cut -d"." -f4` + 1))")',
                                    'PROGNAME=$(basename $0)',
                                    'function error_exit {',
                                    'echo \"${PROGNAME}: ${1:-\\\"Unknown Error\\\"}\" 1>&2',
                                    'exit 1',
                                    '}',
                                    'date',
                                    'declare -a tmsh=()',
                                    'echo \'starting custom-config.sh\'',
                                    USESD,
                                    'if [ -n "${useServiceDiscovery}" ];then',
                                    '   tmsh+=('
                                    '   \'tmsh load sys application template /config/cloud/f5.service_discovery.tmpl\'',
                                    SDAPP,
                                    'else',
                                    '   tmsh+=(',
                                    '   \'tmsh load sys application template /config/cloud/f5.service_discovery.tmpl\')',
                                    'fi',
                                    'tmsh+=(',
                                    '\"tmsh create net vlan external interfaces add { 1.1 } mtu 1460\"',
                                    '\"tmsh create net self ${INT1ADDRESS}/32 vlan external\"',
                                    '\"tmsh create net route ext_gw_int network ${GATEWAY}/32 interface external\"',
                                    EXTRT,
                                    '\"tmsh create net route default gw ${GATEWAY}\"',
                                    '\"tmsh create net vlan internal interfaces add { 1.2 } mtu 1460\"',
                                    '\"tmsh create net self ${INT2ADDRESS}/32 vlan internal allow-service add { tcp:4353 udp:1026 }\"',
                                    '\"tmsh create net route int_gw_int network ${GATEWAY2}/32 interface internal\"',
                                    '\"tmsh modify cm device ${HOSTNAME} unicast-address { { effective-ip ${INT2ADDRESS} effective-port 1026 ip ${INT2ADDRESS} } }\"',
                                    '\"tmsh modify sys db failover.selinuxallowscripts value enable\"',
                                    INTRT,
                                    '\'tmsh save /sys config\'',
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
                                    '           response_code=$(/usr/bin/curl -skvvu admin:$passwd -w "%{http_code}" -X POST -H "Content-Type: application/json" https://localhost:${mgmtGuiPort}/mgmt/shared/appsvcs/declare -d @$file_loc -o /dev/null)',
                                    '           if [[ $response_code == 200 || $response_code == 502 ]]; then',
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
                                    'aliasIpsList=$(echo \'' + context.properties['aliasIp'] + '\' | tr ";" " ")',
                                    'for ip in $aliasIpsList; do',
                                    '   addr=$(echo $ip | cut -d "/" -f1)',
                                    '   echo "creating virtual address: $addr"',
                                    '   /usr/bin/tmsh create ltm virtual-address $addr address $addr',
                                    'done',
                                    '/usr/bin/tmsh save sys config',
                                    '# run failover to ensure objects are on the correct BIG-IP',
                                    '/config/failover/tgactive',
                                    'date',
                                    'EOF',
                                    'curl -s -f --retry 20 -o /config/cloud/f5-cloud-libs.tar.gz https://cdn.f5.com/product/cloudsolutions/f5-cloud-libs/v4.8.1/f5-cloud-libs.tar.gz',
                                    'curl -s -f --retry 20 -o /config/cloud/f5-cloud-libs-gce.tar.gz https://cdn.f5.com/product/cloudsolutions/f5-cloud-libs-gce/v2.3.4/f5-cloud-libs-gce.tar.gz',
                                    'curl -s -f --retry 20 -o /config/cloud/f5-appsvcs-3.5.1-5.noarch.rpm https://cdn.f5.com/product/cloudsolutions/f5-appsvcs-extension/v3.6.0/dist/lts/f5-appsvcs-3.5.1-5.noarch.rpm',
                                    'curl -s -f --retry 20 -o /config/cloud/f5.service_discovery.tmpl https://cdn.f5.com/product/cloudsolutions/iapps/common/f5-service-discovery/v2.3.2/f5.service_discovery.tmpl',
                                    'chmod 755 /config/verifyHash',
                                    'chmod 755 /config/installCloudLibs.sh',
                                    'chmod 755 /config/waitThenRun.sh',
                                    'chmod 755 /config/cloud/gce/custom-config.sh',
                                    'chmod 755 /config/cloud/gce/rm-password.sh',
                                    'chmod 755 /config/cloud/gce/create-va.sh',
                                    'mkdir -p /var/log/cloud/google',
                                    'nohup /usr/bin/setdb provision.1nicautoconfig disable &>> /var/log/cloud/google/install.log < /dev/null &',
                                    'nohup /config/installCloudLibs.sh &>> /var/log/cloud/google/install.log < /dev/null &',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/runScript.js --signal PASSWORD_CREATED --file f5-rest-node --cl-args \'/config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/generatePassword --file /config/cloud/gce/.adminPassword --encrypt\' --log-level verbose -o /var/log/cloud/google/generatePassword.log &>> /var/log/cloud/google/install.log < /dev/null &',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/runScript.js --wait-for PASSWORD_CREATED --signal ADMIN_CREATED --file /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/createUser.sh --cl-args \'--user admin --password-file /config/cloud/gce/.adminPassword --password-encrypted\' --log-level debug -o /var/log/cloud/google/createUser.log &>> /var/log/cloud/google/install.log < /dev/null &',
                                    CUSTHASH,
                                    ONBOARDJS,
                                    'CONFIG_FILE=\'/config/cloud/.deployment\'',
                                    'CLOUD_LIBS_DIR=\'/config/cloud/gce/node_modules/@f5devcentral\'',
                                    'echo \'{"tagKey":"f5_deployment","tagValue":"' + context.env['deployment'] + '"}\' > $CONFIG_FILE',
                                    'echo "/usr/bin/f5-rest-node ${CLOUD_LIBS_DIR}/f5-cloud-libs-gce/scripts/failover.js" >> /config/failover/tgactive',
                                    'echo "/usr/bin/f5-rest-node ${CLOUD_LIBS_DIR}/f5-cloud-libs-gce/scripts/failover.js" >> /config/failover/tgrefresh',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/runScript.js --file /config/cloud/gce/custom-config.sh --cwd /config/cloud/gce -o /var/log/cloud/google/custom-config.log --log-level debug --wait-for ONBOARD_DONE --signal CUSTOM_CONFIG_DONE &>> /var/log/cloud/google/install.log < /dev/null &',
                                    CLUSTERJS,
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/runScript.js --file /config/cloud/gce/rm-password.sh --cwd /config/cloud/gce -o /var/log/cloud/google/rm-password.log --log-level debug --wait-for CLUSTER_DONE --signal PASSWORD_REMOVED &>> /var/log/cloud/google/install.log < /dev/null &',
                                    'nohup /config/waitThenRun.sh f5-rest-node /config/cloud/gce/node_modules/@f5devcentral/f5-cloud-libs/scripts/runScript.js --file /config/cloud/gce/create-va.sh --cwd /config/cloud/gce --log-level debug --wait-for CLUSTER_DONE --signal VIRTUAL_ADDRESSES_CREATED &>> /var/log/cloud/google/install.log < /dev/null &',
                                    'touch /config/startupFinished',
                                    ])
                            )
            }]
        }
  return metadata
def Instance(context, group, storageName, licenseType):
  aliasIps = []
  if group == 'create':
    aliasIps = [{'ipCidrRange': ip} for ip in context.properties['aliasIp'].split(';')]
  instance = {
        'zone': context.properties['availabilityZone1'],
        'canIpForward': True,
        'tags': {
          'items': ['intfw-' + context.env['deployment'],'no-ip']
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
                            context.properties['mgmtNetwork']]),
            'subnetwork': ''.join([COMPUTE_URL_BASE, 'projects/',
                            context.env['project'], '/regions/',
                            context.properties['region'], '/subnetworks/',
                            context.properties['mgmtSubnet']]),
          },
          {
            'network': ''.join([COMPUTE_URL_BASE, 'projects/',
                            context.env['project'], '/global/networks/',
                            context.properties['network1']]),
            'subnetwork': ''.join([COMPUTE_URL_BASE, 'projects/',
                            context.env['project'], '/regions/',
                            context.properties['region'], '/subnetworks/',
                            context.properties['subnet1']]),
            'aliasIpRanges': aliasIps,
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
def GenerateConfig(context):
  import random
  storageNumber = str(random.randint(10000, 99999))
  storageName = 'f5-bigip-' + context.env['deployment'] + '-' + storageNumber
  resources = [{
    'name': 'bigip1-' + context.env['deployment'],
    'type': 'compute.v1.instance',
    'properties': Instance(context, 'create', storageName, 'byol')
  },{
    'name': 'bigip2-' + context.env['deployment'],
    'type': 'compute.v1.instance',
    'properties': Instance(context, 'join', storageName, 'byol')
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
  }]
  return {'resources': resources}
