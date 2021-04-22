#  expectValue = "Successful Traffic Test"
#  scriptTimeout = 3
#  replayEnabled = true
#  replayTimeout = 10

TMP_DIR=/tmp/<DEWPOINT JOB ID>
STATE_FILE=${TMP_DIR}/state.json

# source test functions
source ${TMP_DIR}/test_functions.sh

IP=$(cat ${STATE_FILE} | jq -r '.mgmtAddress')
BASTION_IP=$(cat ${STATE_FILE} | jq -r '.proxyAddress')
APP_IP=$(cat ${STATE_FILE} | jq -r '.applicationAddress')

echo "BIG-IP Application IP: $APP_IP"
## Curl IP for response
if [ -n "$APP_IP" ]; then
    # when bastion host connection is required, that should be the client
    if [ -n "$BASTION_IP" ]; then
        echo "Bastion VM IP:$BASTION_IP"
        response=$(ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 -i /etc/ssl/private/dewpt_private.pem dewpt@"$BASTION_IP" "curl http://$APP_IP")
    else
        response=$(curl http://$APP_IP)
    fi
fi
echo "Response: $response"

if echo $response | grep "www.google.com"; then
    echo "Successful Traffic Test"
fi