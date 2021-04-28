#  expectValue = "Virtual Creation Passed"
#  scriptTimeout = 5
#  replayEnabled = false
#  replayTimeout = 0

TMP_DIR=/tmp/<DEWPOINT JOB ID>
STATE_FILE=${TMP_DIR}/state.json
# source test functions
source ${TMP_DIR}/test_functions.sh

BASTION_IP=$(cat ${STATE_FILE} | jq -r '.proxyAddress')

# Locate bigip1 mgmt ip address
MGMTIP=$(cat ${STATE_FILE} | jq -r '.mgmtAddress')
echo "MGMT IP Address =$MGMTIP"
# Locate forwarding rule addresses: used for HA
COUNTER=0
while [  $COUNTER -lt <NUM FORWARDING RULES> ]; do
    IP=$(gcloud compute forwarding-rules describe <STACK NAME>-fr${COUNTER} --region <REGION> --format json |jq .IPAddress -r)
    echo "Response: $IP"
    IP_List="${IP_List} $IP"
    let COUNTER=COUNTER+1
done

# Locate internal forwarding rule addresses: used for HA
COUNTER=0
while [  $COUNTER -lt <NUM INTERNAL FORWARDING RULES> ]; do
    IP=$(gcloud compute forwarding-rules describe <STACK NAME>-intfr${COUNTER} --region <REGION> --format json |jq .IPAddress -r)
    echo "Response: $IP"
    IP_Int_List="${IP_Int_List} $IP"
    let COUNTER=COUNTER+1
done

# create virtual server for each forwarding rule created
COUNTER=0
for i in $IP_List; do
    # Only create node and pool on first iteration
    if [[ $COUNTER = 0 ]]; then
        make_ssh_request "$MGMTIP" "tmsh create ltm node www.google.com { fqdn { autopopulate enabled name www.google.com } }" "$BASTION_IP"
        make_ssh_request "$MGMTIP" "tmsh create ltm pool dewpt-pool members add { www.google.com:80 } monitor http" "$BASTION_IP"
    fi
    make_ssh_request "$MGMTIP" "tmsh create ltm virtual /Common/dewpt${COUNTER}-80 { destination ${i}:80 ip-protocol tcp pool /Common/dewpt-pool profiles replace-all-with { tcp { } http { } }  source 0.0.0.0/0 source-address-translation { type automap } translate-address enabled translate-port enabled }" "$BASTION_IP"
    # Check to see virtual successfully created
    verify=$(make_ssh_request "$MGMTIP" "tmsh list ltm virtual" "$BASTION_IP")
    if echo $verify | grep "dewpt${COUNTER}-80"; then
        result="$result SUCCESS"
        echo "/Common/dewpt${COUNTER}-80 exits, result set to SUCCESS"
    else
        result="$result FAILURE"
        echo "A failure has occured while creating /Common/dewpt${COUNTER}-80 virtual service."
    fi
    let COUNTER=COUNTER+1
done
# create virtual server for each internal forwarding rule created
COUNTER=0
for i in $IP_Int_List; do
    # Only create node and pool on first iteration
    if [[ $COUNTER = 0 ]]; then
        make_ssh_request "$MGMTIP" "tmsh create ltm node www.google.com { fqdn { autopopulate enabled name www.google.com } }" "$BASTION_IP"
        make_ssh_request "$MGMTIP" "tmsh create ltm pool dewpt-pool members add { www.google.com:80 } monitor http" "$BASTION_IP"
    fi
    make_ssh_request "$MGMTIP" "tmsh create ltm virtual /Common/dewptint${COUNTER}-80 { destination ${i}:80 ip-protocol tcp pool /Common/dewpt-pool profiles replace-all-with { tcp { } http { } }  source 0.0.0.0/0 source-address-translation { type automap } translate-address enabled translate-port enabled }" "$BASTION_IP"
    # Check to see virtual successfully created
    verify=$(make_ssh_request "$MGMTIP" "tmsh list ltm virtual" "$BASTION_IP")
    if echo $verify | grep "dewptint${COUNTER}-80"; then
        result="$result SUCCESS"
        echo "/Common/dewptint${COUNTER}-80 exits, result set to SUCCESS"
    else
        result="$result FAILURE"
        echo "A failure has occured while creating /Common/dewptint${COUNTER}-80 virtual service."
    fi
    let COUNTER=COUNTER+1
done
# Verify all virtuals where created
for i in $result; do
    if [[ "$i" == "FAILURE" ]]; then
        echo "There is a failed vs creation: $result"
        ssh-keygen -R $MGMTIP 2>/dev/null
        exit 1
    fi
done
echo "Virtual Creation Passed"
echo "Results: $result"
ssh-keygen -R $MGMTIP 2>/dev/null
