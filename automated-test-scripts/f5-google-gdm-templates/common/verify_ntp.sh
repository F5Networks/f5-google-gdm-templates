#!/usr/bin/env bash
#  expectValue = "NTP is set"
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

if [[ "<USE SCHEMA>" == "yes" ]]; then
    ntpserver=time.google.com
else
    ntpserver=<NTP SERVER>
fi

# configure auth user shell here too - race condition?
make_ssh_request "$IP" "modify auth user admin shell bash" "$BASTION_IP"

# list ntp - looking for expected value
if [ -n "$IP" ]; then
    response=$(make_ssh_request "$IP" "tmsh list sys ntp" "$BASTION_IP")
    if echo $response | grep "$ntpserver"; then
        result="SUCCESS"
        echo "BIG-IP1 server set"
    else
        echo "DEBUG: response= $response"
    fi
fi
if [ -n "$IP2"  ] && [ "$IP2" != "null" ]; then
    response2=$(make_ssh_request "$IP2" "tmsh list sys ntp" "$BASTION_IP")
    if echo $response2 | grep "$ntpserver"; then
        result2="SUCCESS"
        echo "BIG-IP2 server set"
    else
        echo "DEBUG: response= $response2"
    fi
else
    echo "No ip address for big-ip2, no test for big-ip2 needed."
    result2="SUCCESS"
fi

# Evaluate result variables
if [[ "$result" == "SUCCESS" && "$result2" == "SUCCESS" ]]; then
    echo "NTP is set"
else
    echo "NTP servers not set"
fi
