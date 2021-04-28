#  expectValue = "all devices are available"
#  expectFailValue = "ERROR"
#  scriptTimeout = 4
#  replayEnabled = true
#  replayTimeout = 120

TMP_DIR=/tmp/<DEWPOINT JOB ID>
STATE_FILE=${TMP_DIR}/state.json

# source test functions
source ${TMP_DIR}/test_functions.sh

IP=$(cat ${STATE_FILE} | jq -r '.mgmtAddress')
IP2=$(cat ${STATE_FILE} | jq -r '.mgmtAddress2')
BASTION_IP=$(cat ${STATE_FILE} | jq -r '.proxyAddress')

if [[ "$IP" != "null" ]]; then
    response=$(make_nc_request "$IP" "$BASTION_IP")
    echo "Response from $IP: $response"

    if echo $response | grep -Eq "succeeded|open"; then
        result="SUCCESS"
        echo "BIG-IP1 available"
    fi
fi

if [[ "$IP2" != "null" ]]; then
    response2=$(make_nc_request "$IP2" "$BASTION_IP")
    echo "Response from $IP2: $response2"

    if echo $response2 | grep -Eq "succeeded|open"; then
        result2="SUCCESS"
        echo "BIG-IP2 available"
    fi
else
    result2="SUCCESS"
fi

# Evaluate result variables
if [[ "$result" == "SUCCESS" && "$result2" == "SUCCESS" ]]; then
    echo "all devices are available"
fi

