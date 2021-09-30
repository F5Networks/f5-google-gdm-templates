#  expectValue = "completed successfully"
#  scriptTimeout = 5
#  replayEnabled = false
#  replayTimeout = 0

TMP_DIR="/tmp/<DEWPOINT JOB ID>"

# source test functions
source ${TMP_DIR}/test_functions.sh

# determine test environment public ip address
source_cidr=$(get_env_public_ip)
echo "source_cidr=$source_cidr"

# TODO: Could test the yaml parameter file itself by downloading from template repo, using yaml
# parser (yq) to overlay parameter keys with dynamic values and then run gcloud with that file
tmpl_file='/tmp/f5-<STACK>-<LICENSE TYPE>-<NIC COUNT>nic-bigip.py'
# grab template and schema
#cd $TMP_DIR
curl -k <TEMPLATE URL> -o $tmpl_file
curl -k <TEMPLATE URL>.schema -o "${tmpl_file}.schema"

# setup subnets based on shared vpc
if [[ "<NIC COUNT>" == "1" ]]; then
    if [[ "<MGMT NETWORK SHARED VPC>" == "None" ]]; then
        mgmt_net='<NETWORK>'
        mgmt_subnet='<SUBNET1 AZ1>'
    else
        mgmt_net='dewpt'
        mgmt_subnet="subnet1"
    fi
else
    if [[ "<EXT NETWORK SHARED VPC>" == "None" ]]; then
        mgmt_net='<NETWORK>'
        mgmt_subnet='<SUBNET1 AZ1>'
        network1='<EXT NETWORK>'
        subnet1='<EXT SUBNET>'
    else
        mgmt_net='<NETWORK>'
        mgmt_subnet='<SUBNET1 AZ1>'
        network1='dewpt2'
        subnet1='subnet2'
    fi
fi

# TODO: Get static IP information, if necessary
mgmt_ip="DYNAMIC" ; subnet1_ip="DYNAMIC" ; subnet2_ip="DYNAMIC"
if [[ "<PRIVATE IP TYPE>" == *"STATIC"* ]]; then
    # adding random between 100-200 for last octet
    num=0   #initialize
    while [ "$num" -le 100 ]
    do
        num=$RANDOM
        let "num %= 200"  # Scales $num down within 100-200.
    done
    mgmt_ip=$(get_ip "$(gcloud compute networks subnets describe $mgmt_subnet --region=<REGION> --format json | jq .ipCidrRange -r)" ${num})
    echo "mgmt_ip=${mgmt_ip}" >> ${TMP_DIR}/static_ip.conf
    if [[ <NIC COUNT> -ge 2 ]]; then
        subnet1_ip=$(get_ip "$(gcloud compute networks subnets describe <EXT SUBNET> --region=<REGION> --format json | jq .ipCidrRange -r)" ${num})
        echo "subnet1_ip=${subnet1_ip}" >> ${TMP_DIR}/static_ip.conf
    fi
    if [[ <NIC COUNT> -ge 3 ]]; then    
        subnet2_ip=$(get_ip "$(gcloud compute networks subnets describe <INT SUBNET> --region=<REGION> --format json | jq .ipCidrRange -r)" ${num})
        echo "subnet2_ip=${subnet2_ip}" >> ${TMP_DIR}/static_ip.conf
    fi
fi


map_to_use="MGMT_SUBNET_ADDRESS:${mgmt_ip},SUBNET1_SUBNET_ADDRESS:${subnet1_ip},SUBNET2_SUBNET_ADDRESS:${subnet2_ip}, MGMT_NET:${mgmt_net}, MGMT_SUBNET:${mgmt_subnet}, NETWORK_1:${network1}, SUBNET_1:${subnet1}"
network_param=$(map "<NETWORK PARAM>" "$map_to_use")
# Run GDM template
# setup Optional parameters
if [[ "<USE SCHEMA>" == "yes" ]]; then
    optional_params=''
else
    optional_params=",mgmtGuiPort:<MGMT PORT>,ntpServer:'<NTP SERVER>',applicationPort:'<APP PORT>',timezone:'<TIMEZONE>',bigIpModules:'<BIGIP MODULES>'"
fi

# yaml input parameter files ideally should be simple key:value pairs and the create task builds parameters
# based on that, so this is working towards that goal
extra_params=''
if [[ "<PUBLIC IP>" == "True" ]]; then
    extra_params+=",provisionPublicIP:'yes'"
else
    extra_params+=",provisionPublicIP:'no'"
fi

# setup Required parameters - note, not able to handle spaces in <app port> and <ntp server>, spaces in syntax work fine when not using dewpoint.
properties="region:'<REGION>',availabilityZone1:'<AVAILABILITY ZONE>',imageName:'<IMAGE NAME>',instanceType:'<INSTANCE TYPE>',logLevel:'<LOG LEVEL>',restrictedSrcAddress:${source_cidr},restrictedSrcAddressApp:${source_cidr},declarationUrl:<DECLARATION URL>,allowUsageAnalytics:<ANALYTICS>,allowPhoneHome:<PHONEHOME><LICENSE PARAM>${network_param}${optional_params}${extra_params}"
labels="delete=true"
gcloud="gcloud deployment-manager deployments create <STACK NAME> --template $tmpl_file --labels $labels --properties $properties"
echo $gcloud
# Run command
$gcloud
