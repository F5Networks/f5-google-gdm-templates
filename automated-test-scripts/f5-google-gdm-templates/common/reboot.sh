#  expectValue = "SUCCESS"
#  expectFailValue = "ERROR"
#  scriptTimeout = 4
#  replayEnabled = true
#  replayTimeout = 4

TMP_DIR=/tmp/<DEWPOINT JOB ID>
STATE_FILE=${TMP_DIR}/state.json

# source test functions
source ${TMP_DIR}/test_functions.sh

IP=$(cat ${STATE_FILE} | jq -r '.mgmtAddress')
IP2=$(cat ${STATE_FILE} | jq -r '.mgmtAddress2')
BASTION_IP=$(cat ${STATE_FILE} | jq -r '.proxyAddress')

# reboot system to verify configuration survived reboot - ESECLDTPLT-1696
reboot_bigip='tmsh reboot'
result=''
result2=''
if [[ "$IP" != "null" && "$IP2" != "null" ]]; then
    ssh-keygen -R $IP 2>/dev/null
    ssh-keygen -R $IP2 2>/dev/null
    response=$(make_ssh_request "$IP" "$reboot_bigip" "$BASTION_IP")
    response2=$(make_ssh_request "$IP2" "$reboot_bigip" "$BASTION_IP")
    echo "Response from IP $IP: $response"
    echo "Response from IP2 $IP2: $response2"
    if echo $response | grep "The system will be rebooted momentarily" && echo $response2 | grep "The system will be rebooted momentarily"; then
        echo "SUCCESS"
        echo "Systems have been rebooted"
        echo "sleeping for 60 seconds before next test"
        sleep 60
    else
        echo "Systems have not rebooted"
    fi
else
    ssh-keygen -R $IP 2>/dev/null
    response=$(make_ssh_request "$IP" "$reboot_bigip" "$BASTION_IP")
    echo "Response from IP $IP: $response"
    if echo $response | grep "The system will be rebooted momentarily"; then
        echo "SUCCESS"
        echo "System rebooting"
        echo "sleeping for 60 seconds before next test"
        sleep 60
    else
        echo "System has not rebooted"
    fi
fi