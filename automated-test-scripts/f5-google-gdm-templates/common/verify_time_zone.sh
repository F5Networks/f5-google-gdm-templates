#!/usr/bin/env bash
#  expectValue = "Timezone is set"
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

# setup response variables
if [[ "<USE SCHEMA>" == "yes" ]]; then
    timezone=UTC
else
    timezone=<TIMEZONE>
fi

if [ -n "$IP" ]; then
    response=$(make_ssh_request "$IP" "tmsh list sys ntp timezone" "$BASTION_IP")
    if echo $response | grep "$timezone"; then
        result="SUCCESS"
        echo "BIG-IP1 server set"
    fi
fi
if [ -n "$IP2"  ] && [ "$IP2" != "null" ]; then
    response2=$(make_ssh_request "$IP2" "tmsh list sys ntp timezone" "$BASTION_IP")
    if echo $response2 | grep "$timezone"; then
        result2="SUCCESS"
        echo "BIG-IP2 server set"
    fi
else
    echo "No ip address for big-ip2, no test for big-ip2 needed."
    result2="SUCCESS"
fi

# Evaluate result variables
if [[ "$result" == "SUCCESS" && "$result2" == "SUCCESS" ]]; then
    echo "Timezone is set"
else
    echo "Timezone not set"
fi
