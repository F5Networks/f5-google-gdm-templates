#!/usr/bin/env bash
#  expectValue = "metadata.google.internal host set"
#  scriptTimeout = 3
#  replayEnabled = true
#  replayTimeout = 40

TMP_DIR="/tmp/<DEWPOINT JOB ID>"
STATE_FILE=${TMP_DIR}/state.json

# source test functions
source ${TMP_DIR}/test_functions.sh

IP=$(cat ${STATE_FILE} | jq -r '.mgmtAddress')
IP2=$(cat ${STATE_FILE} | jq -r '.mgmtAddress2')
BASTION_IP=$(cat ${STATE_FILE} | jq -r '.proxyAddress')


echo "Bigip1Url=$IP"
echo "Bigip2Url=$IP2"

# Metadata IP address for name: metadata.google.internal
expectedValue=169.254.169.254

result=''
result2=''

# Normalize failover
list_remote_host='tmsh list sys global-settings remote-host'
if [ -n "$IP2" ]; then
    ssh-keygen -R $IP2 2>/dev/null
    response=$(make_ssh_request "$IP2" "$list_remote_host" "$BASTION_IP")
    if echo $response | grep "$expectedValue"; then
        result="SUCCESS"
        echo "BIG-IP1 server set"
    fi
fi
if [ -n "$IP" ]; then
    ssh-keygen -R $IP 2>/dev/null
    response2=$(make_ssh_request "$IP" "$list_remote_host" "$BASTION_IP")
    if echo $response2 | grep "$expectedValue"; then
        result2="SUCCESS"
        echo "BIG-IP2 server set"
    fi
fi

# Evaluate result variables
if [[ "$result" == "SUCCESS" && "$result2" == "SUCCESS" ]]; then
    echo "metadata.google.internal host set"
else
    echo "metadata.google.internal is not set"
fi
