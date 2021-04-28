#!/usr/bin/env bash
#  expectValue = "SUCCESS"
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


# Grab CFE declaration

if [ -n "$IP" ]; then
    response=$(make_ssh_request "$IP" "curl -sku admin:none https://localhost:<MGMT PORT>/mgmt/shared/cloud-failover/declare |jq ." "$BASTION_IP")
fi

echo "CFE Declaration: $response"

# Evaluate
if echo $response | jq -r .message | grep 'success'; then
    result="SUCCESS"
else
    result="FAILED"
fi
echo "$result"