#!/usr/bin/env bash
#  expectValue = "CFE is installed"
#  scriptTimeout = 3
#  replayEnabled = true
#  replayTimeout = 30

TMP_DIR=/tmp/<DEWPOINT JOB ID>
STATE_FILE=${TMP_DIR}/state.json

# source test functions
source ${TMP_DIR}/test_functions.sh

IP=$(cat ${STATE_FILE} | jq -r '.mgmtAddress')
IP2=$(cat ${STATE_FILE} | jq -r '.mgmtAddress2')
BASTION_IP=$(cat ${STATE_FILE} | jq -r '.proxyAddress')
result=''
result2=''

if [ -n "$IP" ]; then
    ssh-keygen -R $IP 2>/dev/null
    response=$(make_ssh_request "$IP" "tmsh list mgmt shared iapp installed-packages" "$BASTION_IP")
    if [[ $response == *"f5-cloud-failover"* ]]; then
        result="SUCCESS"
        echo "CFE installed on BIG-IP1"
    fi
fi
if [ -n "$IP2"  ] && [ "$IP2" != "null" ]; then
    ssh-keygen -R $IP2 2>/dev/null
    response2=$(make_ssh_request "$IP2" "tmsh list mgmt shared iapp installed-packages" "$BASTION_IP")
    if [[ $response2 == *"f5-cloud-failover"* ]]; then
        result2="SUCCESS"
        echo "CFE installed on BIG-IP2"
    fi
else
    echo "No ip address for big-ip2, no test for big-ip2 needed."
    result2="SUCCESS"
fi

# Evaluate result variables
if [[ "$result" == "SUCCESS" && "$result2" == "SUCCESS" ]]; then
    echo "CFE is installed"
else
    echo "CFE is not installed"
fi
