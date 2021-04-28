#!/usr/bin/env bash
#  expectValue = "AS3 declaration is installed"
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


# No need to test Declaration URL when 'default'
if [[ "<DECLARATION URL>" == "default" || "<DECLARATION URL>" == "none" ]]; then
    echo "AS3 declaration is installed"
fi

if [ -n "$IP" ]; then
    response=$(make_ssh_request "$IP" "tmsh list auth partition" "$BASTION_IP")
    if [[ $response == *"Sample_02"*"Updated by AS3"* ]]; then
        result="SUCCESS"
    fi
fi
if [ -n "$IP2"  ] && [ "$IP2" != "null" ]; then
    response2=$(make_ssh_request "$IP2" "tmsh list auth partition" "$BASTION_IP")
    if [[ $response == *"Sample_02"*"Updated by AS3"* ]]; then
        result2="SUCCESS"
    fi
else
    echo "No ip address for big-ip2, no test for big-ip2 needed."
    result2="SUCCESS"
fi

# Evaluate result variables
if [[ "$result" == "SUCCESS" && "$result2" == "SUCCESS" ]]; then
    echo "AS3 declaration is installed"
else
    echo "AS3 declaration is not installed"
fi