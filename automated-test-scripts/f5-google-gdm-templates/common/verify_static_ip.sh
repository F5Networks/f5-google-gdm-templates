#  expectValue = "STATIC is set"
#  scriptTimeout = 2
#  replayEnabled = true
#  replayTimeout = 30

TMP_DIR=/tmp/<DEWPOINT JOB ID>
STATE_FILE=${TMP_DIR}/state.json

# source test functions
source ${TMP_DIR}/test_functions.sh
# source static_ip conf
source $TMP_DIR/static_ip.conf

IP=$(cat ${STATE_FILE} | jq -r '.mgmtAddress')
IP2=$(cat ${STATE_FILE} | jq -r '.mgmtAddress2')
BASTION_IP=$(cat ${STATE_FILE} | jq -r '.proxyAddress')

## run test if using static ip's
if [[ "<PRIVATE IP TYPE>" == *"STATIC"* ]]; then
    ## grab and set instance interface values
    if [[ "<NIC COUNT>" == "1" ]]; then
        cloud_mgmt_ip=$(gcloud compute instances describe bigip1-<STACK NAME> --zone <AVAILABILITY ZONE> --format json |jq .networkInterfaces[0].networkIP -r)
    else
        cloud_mgmt_ip=$(gcloud compute instances describe bigip1-<STACK NAME> --zone <AVAILABILITY ZONE> --format json |jq .networkInterfaces[1].networkIP -r)
    fi
    if [[ "<NIC COUNT>" != "1" ]]; then
        cloud_subnet1_ip=$(gcloud compute instances describe bigip1-<STACK NAME> --zone <AVAILABILITY ZONE> --format json |jq .networkInterfaces[0].networkIP -r)
    fi
    if [[ "<NIC COUNT>" == "3" ]]; then
        cloud_subnet2_ip=$(gcloud compute instances describe bigip1-<STACK NAME> --zone <AVAILABILITY ZONE> --format json |jq .networkInterfaces[2].networkIP -r)
    fi
    ## evaluate against source values
    if [[ "<NIC COUNT>" == "3" ]]; then
        if [[ "$mgmt_ip" == "$cloud_mgmt_ip" && "$subnet1_ip" == "$cloud_subnet1_ip" && "$subnet2_ip" == "$cloud_subnet2_ip" ]];then
            echo "mgmt_ip:$mgmt_ip cloud_mgmt_ip:$cloud_mgmt_ip subnet1_ip:$subnet1_ip cloud_subnet1_ip:$cloud_subnet1_ip subnet2_ip:$subnet2_ip cloud_subnet2_ip:$cloud_subnet2_ip"
            echo "STATIC is set"
        else
            echo "mgmt_ip:$mgmt_ip cloud_mgmt_ip:$cloud_mgmt_ip subnet1_ip:$subnet1_ip cloud_subnet1_ip:$cloud_subnet1_ip subnet2_ip:$subnet2_ip cloud_subnet2_ip:$cloud_subnet2_ip"
            echo "FAILED"
        fi
    elif  [[ "<NIC COUNT>" == "2" ]]; then
        if [[ "$mgmt_ip" == "$cloud_mgmt_ip" && "$subnet1_ip" == "$cloud_subnet1_ip" ]];then
            echo "mgmt_ip:$mgmt_ip cloud_mgmt_ip:$cloud_mgmt_ip subnet1_ip:$subnet1_ip cloud_subnet1_ip:$cloud_subnet1_ip"            
            echo "STATIC is set"
        else
            echo "mgmt_ip:$mgmt_ip cloud_mgmt_ip:$cloud_mgmt_ip subnet1_ip:$subnet1_ip cloud_subnet1_ip:$cloud_subnet1_ip"
            echo "FAILED"
        fi
    elif  [[ "<NIC COUNT>" == "1" ]]; then
        if [[ "$mgmt_ip" == "$cloud_mgmt_ip" ]];then
            echo "mgmt_ip:$mgmt_ip cloud_mgmt_ip:$cloud_mgmt_ip"
            echo "STATIC is set"
        else
            echo "mgmt_ip:$mgmt_ip cloud_mgmt_ip:$cloud_mgmt_ip"
            echo "FAILED"
        fi    
    else
        echo "FAILED - unknown number of nics"
    fi
## Skip test if not set to STATIC
else
    echo "DYNAMIC IP being used, no need to test for static."
    echo "STATIC is set"    
fi