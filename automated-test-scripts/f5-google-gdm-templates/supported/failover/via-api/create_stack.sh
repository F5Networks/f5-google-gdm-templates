#  expectValue = "completed successfully"
#  scriptTimeout = 5
#  replayEnabled = false
#  replayTimeout = 0

TMP_DIR="/tmp/<DEWPOINT JOB ID>"

# source test functions
source ${TMP_DIR}/test_functions.sh

tmpl_file='/tmp/deployment-<DEWPOINT JOB ID>.py'
rm -f $tmpl_file
curl -k <TEMPLATE URL> -o $tmpl_file

# yaml input parameter files ideally should be simple key:value pairs and the create task builds parameters
# based on that, so this is working towards that goal
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

if [[ "<ALIAS IP>" == "True" ]]; then
    network=$(gcloud compute networks subnets describe <EXT SUBNET> --region=<REGION> --format json | jq .ipCidrRange -r)
    number=0   #initialize
    while [ "$number" -le 10 ]
    do
        number=$RANDOM
        let "number %= 250"  # Scales $number down within 10-250.
    done
    alias_ip_01="$(get_ip ${network} ${number})/32"

    number=0   #initialize
    while [ "$number" -le 10 ]
    do
        number=$RANDOM
        let "number %= 250"  # Scales $number down within 10-250.
    done
    alias_ip_02="$(get_ip ${network} ${number})/32"
    set_state "aliasIP" "$alias_ip_01" # save alias IP in state file, for use by later tests

    extra_params+=",aliasIp:'${alias_ip_01};${alias_ip_02}'"
else
    alias_ip='None'
    set_state "aliasIP" "$alias_ip"
    extra_params+=",aliasIp:'${alias_ip}'"
fi
echo "Extra parameters: ${extra_params}"

# setup shared vpc
if [[ "<EXT NETWORK SHARED VPC>" == "None" ]]; then
    network1='<EXT NETWORK>'
    subnet1='<EXT SUBNET>'
else
    network1='dewpt2'
    subnet1='subnet2'
fi
# Run GDM template
if [[ "<NIC COUNT>" == "3" ]]; then
    gcloud deployment-manager deployments create <STACK NAME> --template $tmpl_file --labels "delete=true" --properties "region:'<REGION>',availabilityZone1:'<AVAILABILITY ZONE>',availabilityZone2:'<AVAILABILITY ZONE2>',mgmtNetwork:'<NETWORK>',mgmtSubnet:'<SUBNET1 AZ1>',network1:${network1},network1SharedVpc:'<EXT NETWORK SHARED VPC>',subnet1:${subnet1},mask1:'<EXT PREFIX>',network2:'<INT NETWORK>',subnet2:'<INT SUBNET>',mask2:'<INT PREFIX>',imageName:'<IMAGE NAME>',instanceType:'<INSTANCE TYPE>',logLevel:'silly',mgmtGuiPort:'<MGMT PORT>',bigIpModules:'<BIGIP MODULES>',serviceAccount:'<SERVICE ACCOUNT>',allowUsageAnalytics:'<ANALYTICS>',allowPhoneHome:<PHONEHOME>,declarationUrl:'<DECLARATION URL>',numberOfForwardingRules:'<NUM FORWARDING RULES>',ntpServer:'<NTP SERVER>',timezone:'<TIMEZONE>'<LICENSE PARAM>${extra_params}"
elif [[ "<NIC COUNT>" == "2"  ]]; then
    gcloud deployment-manager deployments create <STACK NAME> --template $tmpl_file --labels "delete=true" --properties "region:'<REGION>',availabilityZone1:'<AVAILABILITY ZONE>',availabilityZone2:'<AVAILABILITY ZONE2>',mgmtNetwork:'<NETWORK>',mgmtSubnet:'<SUBNET1 AZ1>',network1:${network1},network1SharedVpc:'<EXT NETWORK SHARED VPC>',subnet1:${subnet1},mask1:'<EXT PREFIX>',imageName:'<IMAGE NAME>',instanceType:'<INSTANCE TYPE>',logLevel:'silly',mgmtGuiPort:'<MGMT PORT>',bigIpModules:'<BIGIP MODULES>',serviceAccount:'<SERVICE ACCOUNT>',allowUsageAnalytics:'<ANALYTICS>',allowPhoneHome:<PHONEHOME>,declarationUrl:'<DECLARATION URL>',numberOfForwardingRules:'<NUM FORWARDING RULES>',ntpServer:'<NTP SERVER>',timezone:'<TIMEZONE>'<LICENSE PARAM>${extra_params}"
fi
# clean up file on disk
rm -f $tmpl_file
