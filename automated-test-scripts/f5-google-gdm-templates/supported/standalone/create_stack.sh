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
    mgmt_ip=$(get_ip "$(gcloud compute networks subnets describe subnet1 --region=<REGION> --format json | jq .ipCidrRange -r)" ${num})
    subnet1_ip=$(get_ip "$(gcloud compute networks subnets describe subnet2 --region=<REGION> --format json | jq .ipCidrRange -r)" ${num})
    subnet2_ip=$(get_ip "$(gcloud compute networks subnets describe subnet3 --region=<REGION> --format json | jq .ipCidrRange -r)" ${num})
    # stash values into file for later validation
    echo "mgmt_ip=${mgmt_ip}" >> ${TMP_DIR}/static_ip.conf
    echo "subnet1_ip=${subnet1_ip}" >> ${TMP_DIR}/static_ip.conf
    echo "subnet2_ip=${subnet2_ip}" >> ${TMP_DIR}/static_ip.conf
fi
map_to_use="MGMT_SUBNET_ADDRESS:${mgmt_ip},SUBNET1_SUBNET_ADDRESS:${subnet1_ip},SUBNET2_SUBNET_ADDRESS:${subnet2_ip}"
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
