#  expectValue = "completed successfully"
#  scriptTimeout = 5
#  replayEnabled = false
#  replayTimeout = 0

TMP_DIR="/tmp/<DEWPOINT JOB ID>"

# source test functions
source ${TMP_DIR}/test_functions.sh

# TODO: Could test the yaml parameter file itself by downloading from template repo, using yaml
# parser (yq) to overlay parameter keys with dynamic values and then run gcloud with that file
tmpl_file='/tmp/f5-<STACK>-same-net-cluster-<LICENSE TYPE>-<NIC COUNT>nic-bigip.py'
rm -f $tmpl_file
# grab template and schema
#cd $TMP_DIR
curl -k <TEMPLATE URL> -o $tmpl_file
curl -k <TEMPLATE URL>.schema -o "${tmpl_file}.schema"

# determine test environment public ip address
if [[ "<PUBLIC IP>" == "True" ]]; then
  source_ip=$(curl ifconfig.me)/32
  source_cidr="${source_ip} 10.0.0.0/8"
else
  source_cidr='0.0.0.0/0'
fi
echo "source_cidr=$source_cidr"

extra_params=",restrictedSrcAddress:${source_cidr}"
if [[ "<PUBLIC IP>" == "True" ]]; then
    extra_params+=",provisionPublicIP:'yes'"
else
    extra_params+=",provisionPublicIP:'no'"
fi
echo "Extra parameters: ${extra_params}"

# Run GDM template
# setup Optional parameters
if [[ "<USE SCHEMA>" == "yes" ]]; then
    optional_parm=''
else
    optional_parm=",mgmtGuiPort:<MGMT PORT>,ntpServer:'<NTP SERVER>',timezone:'<TIMEZONE>'"
fi
if [[ "<NUM INTERNAL FORWARDING RULES>" = 1 ]]; then
    optional_parm="${optional_parm},restrictedSrcAddressIntApp:'0.0.0.0/0',applicationIntPort:'<APP INTERNAL PORT>'"
fi

# yaml input parameter files ideally should be simple key:value pairs and the create task builds parameters
# based on that, so this is working towards that goal
# setup shared vpc
if [[ "<EXT NETWORK SHARED VPC>" == "None" ]]; then
    network1='<EXT NETWORK>'
    subnet1='<EXT SUBNET>'
else
    network1='dewpt2'
    subnet1='subnet2'
fi
map_to_use="NETWORK_1:${network1}, SUBNET_1:${subnet1}"
network_param=$(map "<NETWORK PARAM>" "$map_to_use")
echo "Network Parm: $network_param"

gcloud deployment-manager deployments create <STACK NAME> --template $tmpl_file --labels "delete=true" --properties "region:'<REGION>',availabilityZone1:'<AVAILABILITY ZONE>',imageName:'<IMAGE NAME>',instanceType:'<INSTANCE TYPE>',logLevel:'<LOG LEVEL>',numberOfForwardingRules:<NUM FORWARDING RULES>,numberOfIntForwardingRules:<NUM INTERNAL FORWARDING RULES>,applicationPort:'<APP PORT>',restrictedSrcAddressApp:'0.0.0.0/0',bigIpModules:'<BIGIP MODULES>',serviceAccount:'<SERVICE ACCOUNT>',declarationUrl:'<DECLARATION URL>',allowUsageAnalytics:<ANALYTICS>,allowPhoneHome:<PHONEHOME><LICENSE PARAM>${network_param}${optional_parm}${extra_params}"

# clean up file on disk
rm -f $tmpl_file
