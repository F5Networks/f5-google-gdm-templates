#  expectValue = "Onboard Passed"
#  expectFailValue = "CLOUD_LIBS_ERROR"
#  scriptTimeout = 5
#  replayEnabled = true
#  replayTimeout = 120

TMP_DIR=/tmp/<DEWPOINT JOB ID>
STATE_FILE=${TMP_DIR}/state.json

# source test functions
source ${TMP_DIR}/test_functions.sh

IP=$(cat ${STATE_FILE} | jq -r '.mgmtAddress')
IP2=$(cat ${STATE_FILE} | jq -r '.mgmtAddress2')
BASTION_IP=$(cat ${STATE_FILE} | jq -r '.proxyAddress')
result=''
result2=''

# Set Signaling for standalone vs failover
SIGNAL="CUSTOM_CONFIG_DONE"
if [ -n "$IP2"  ] && [ "$IP2" != "null" ]; then
    SIGNAL="RM_PASSWORD_DONE"
fi
# list cloud libs directory - looking for ONBOARD_DONE
modify_auth_cmd='modify auth user admin shell bash'
list_cmd='ls -la /tmp/f5-cloud-libs-signals /config/cloud/gce 2>&1'
if [ -n "$IP" ]; then
    ssh-keygen -R $IP 2>/dev/null
    make_ssh_request "$IP" "$modify_auth_cmd" "$BASTION_IP"
    response=$(make_ssh_request "$IP" "$list_cmd" "$BASTION_IP")
    if echo $response | grep "$SIGNAL"; then
        result="SUCCESS"
        echo "BIG-IP1 onboard complete"
    fi
fi

# conditional - second device not required in all solution types
if [ -n "$IP2"  ] && [ "$IP2" != "null" ]; then
    ssh-keygen -R $IP2 2>/dev/null
    make_ssh_request "$IP" "$modify_auth_cmd" "$BASTION_IP"
    response2=$(make_ssh_request "$IP2" "$list_cmd" "$BASTION_IP")
    if echo $response2 | grep "$SIGNAL"; then
        result2="SUCCESS"
        echo "BIG-IP2 onboard complete"
    fi
else
    result2="SUCCESS"
fi

# Evaluate result variables
if [[ "$result" == "SUCCESS" && "$result2" == "SUCCESS" ]]; then
    echo "Onboard Passed"
else
    echo "Onboard Failed"
fi
