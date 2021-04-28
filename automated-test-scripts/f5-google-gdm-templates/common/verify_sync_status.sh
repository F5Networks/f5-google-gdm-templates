#  expectValue = "Sync State Successful"
#  expectFailValue = "ERROR"
#  scriptTimeout = 3
#  replayEnabled = true
#  replayTimeout = 20

TMP_DIR=/tmp/<DEWPOINT JOB ID>
STATE_FILE=${TMP_DIR}/state.json

# source test functions
source ${TMP_DIR}/test_functions.sh

IP=$(cat ${STATE_FILE} | jq -r '.mgmtAddress')
IP2=$(cat ${STATE_FILE} | jq -r '.mgmtAddress2')
BASTION_IP=$(cat ${STATE_FILE} | jq -r '.proxyAddress')


sync_status='tmsh show cm sync-status'
run_cmd='tmsh run sys failover standby'
result=''
result2=''
ssh-keygen -R $IP 2>/dev/null
# Normalize failover for future tests
make_ssh_request "$IP" "$run_cmd" "$BASTION_IP"
# Check Sync Status
response=$(make_ssh_request "$IP" "$sync_status" "$BASTION_IP")
echo "Response from IP $IP: $response"
if echo $response | grep "In Sync"; then
    result="SUCCESS"
fi
ssh-keygen -R $IP2 2>/dev/null
response2=$(make_ssh_request "$IP2" "$sync_status" "$BASTION_IP")
echo "Response from IP2 $IP2: $response2"
if echo $response2 | grep "In Sync"; then
    result2="SUCCESS"
fi
# Evaluate result variables
if [[ "$result" == "SUCCESS" && "$result2" == "SUCCESS" ]]; then
    echo "Sync State Successful"
else
    echo "Sync state wrong"
fi