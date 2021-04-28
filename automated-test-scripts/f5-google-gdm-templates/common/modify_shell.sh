#  expectValue = "Bash shell set"
#  expectFailValue = "ERROR"
#  scriptTimeout = 2
#  replayEnabled = true
#  replayTimeout = 60

TMP_DIR=/tmp/<DEWPOINT JOB ID>
STATE_FILE=${TMP_DIR}/state.json

# source test functions
source ${TMP_DIR}/test_functions.sh

IP=$(cat ${STATE_FILE} | jq -r '.mgmtAddress')
IP2=$(cat ${STATE_FILE} | jq -r '.mgmtAddress2')
BASTION_IP=$(cat ${STATE_FILE} | jq -r '.proxyAddress')

# configure auth user shell to be bash
# list the admin shell - looking for bash
modify_auth_cmd='modify auth user admin shell bash'
save_config_cmd='source /usr/lib/bigstart/bigip-ready-functions;wait_bigip_ready;tmsh save sys config'
verify_cmd='tmsh list auth user admin shell'
result=''
result2=''
if [ "$IP" != "null" ]; then
    ssh-keygen -R $IP 2>/dev/null
    make_ssh_request "$IP" "$modify_auth_cmd" "$BASTION_IP"
    response=$(make_ssh_request "$IP" "$verify_cmd" "$BASTION_IP")
    echo "Response from IP $IP: $response"

    if echo $response | grep "shell bash"; then
        result="SUCCESS"
        echo "Modified on BIG-IP1"
        echo "Saving Config"
        make_ssh_request "$IP" "$save_config_cmd" "$BASTION_IP"
    fi
fi

# conditional - second device not required in all solution types
if [ "$IP2" != "null" ]; then
    ssh-keygen -R $IP2 2>/dev/null
    make_ssh_request "$IP2" "$modify_auth_cmd" "$BASTION_IP"
    response2=$(make_ssh_request "$IP2" "$verify_cmd" "$BASTION_IP")
    echo "Response from IP2 $IP2: $response2"

    if echo $response2 | grep "shell bash"; then
        result2="SUCCESS"
        echo "Modified on BIG-IP2"
        echo "Saving Config"
        make_ssh_request "$IP" "$save_config_cmd" "$BASTION_IP"
    fi
else
    result2="SUCCESS"
fi

# Evaluate result variables
if [[ "$result" == "SUCCESS" && "$result2" == "SUCCESS" ]]; then
    echo "Bash shell set"
else
    echo "Shell not yet set"
fi
