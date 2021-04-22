#  expectValue = "Successful Traffic Test"
#  scriptTimeout = 2
#  replayEnabled = true
#  replayTimeout = 10

TMP_DIR=/tmp/<DEWPOINT JOB ID>
STATE_FILE=${TMP_DIR}/state.json
# source test functions
source ${TMP_DIR}/test_functions.sh

BASTION_IP=$(cat ${STATE_FILE} | jq -r '.proxyAddress')
echo "Bastion Host: $BASTION_IP"

# Locate bigip1 mgmt ip address
MGMTIP=$(cat ${STATE_FILE} | jq -r '.mgmtAddress')
echo "MGMT IP Address =$MGMTIP"

## using fqdn node www.google.com for backend pool
expected_response='www.google.com'

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

# Test each forwarding IP address
for i in $IP_List; do
    echo "Bigip App Traffic IP = $i"
    response=$(curl http://$i)
    if echo $response | grep "$expected_response"; then
        result="$result SUCCESS"
        echo "Success for traffic test to ${i}: $response"
    else
        result="$result FAILURE"
        echo "Failure for traffic test to ${i}: $response"
    fi
done
# Test each internal forwarding IP address
for i in $IP_Int_List; do
    echo "Bigip App Traffic IP = $i"
    response=$(make_ssh_request "$MGMTIP" "curl http://${i}" "$BASTION_IP")
    if echo $response | grep "$expected_response"; then
        result="$result SUCCESS"
        echo "Success for traffic test to ${i}: $response"
    else
        result="$result FAILURE"
        echo "Failure for traffic test to ${i}: $response"
    fi
done
# Test result status
for i in $result; do
    if [[ "$i" == "FAILURE" ]]; then
        echo "There was a failed test: $result"
        ssh-keygen -R $MGMTIP 2>/dev/null
        exit 1
    fi
done
echo "Successful Traffic Test"
echo "Results: $result"
ssh-keygen -R $MGMTIP 2>/dev/null