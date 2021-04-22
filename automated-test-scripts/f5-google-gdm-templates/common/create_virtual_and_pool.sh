#  expectValue = "dewpt-80"
#  scriptTimeout = 5
#  replayEnabled = false
#  replayTimeout = 0

TMP_DIR=/tmp/<DEWPOINT JOB ID>
STATE_FILE=${TMP_DIR}/state.json

# source test functions
source ${TMP_DIR}/test_functions.sh

IP=$(cat ${STATE_FILE} | jq -r '.mgmtAddress')
BASTION_IP=$(cat ${STATE_FILE} | jq -r '.proxyAddress')
APP_IP_INTERNAL=$(cat ${STATE_FILE} | jq -r '.applicationAddressInternal')

echo "Bigip Virtual Address = $IP"

make_ssh_request "$IP" "tmsh create ltm node www.google.com { fqdn { autopopulate enabled name www.google.com } }" "$BASTION_IP"
make_ssh_request "$IP" "tmsh create ltm pool dewpt-pool members add { www.google.com:80 } monitor http" "$BASTION_IP"
make_ssh_request "$IP" "tmsh create ltm virtual /Common/dewpt-80 { destination ${APP_IP_INTERNAL}:80 ip-protocol tcp pool /Common/dewpt-pool profiles replace-all-with { tcp { } http { } }  source 0.0.0.0/0 source-address-translation { type automap } translate-address enabled translate-port enabled }" "$BASTION_IP"
make_ssh_request "$IP" "tmsh list ltm virtual" "$BASTION_IP"
