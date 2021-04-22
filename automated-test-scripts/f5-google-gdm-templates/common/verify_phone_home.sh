#!/usr/bin/env bash
#  expectValue = "Phonehome verified"
#  scriptTimeout = 3
#  replayEnabled = true
#  replayTimeout = 30

TMP_DIR=/tmp/<DEWPOINT JOB ID>
STATE_FILE=${TMP_DIR}/state.json

# source test functions
source ${TMP_DIR}/test_functions.sh

# set phonehome
case <PHONEHOME> in
yes)
  phonehome='enabled' ;;
no)
  phonehome='disabled' ;;
*)
  echo "Phonehome missing from test parameters!"
  exit 1 ;;
esac

IP=$(cat ${STATE_FILE} | jq -r '.mgmtAddress')
IP2=$(cat ${STATE_FILE} | jq -r '.mgmtAddress2')
BASTION_IP=$(cat ${STATE_FILE} | jq -r '.proxyAddress')
result=''
result2=''

if [[ -n "$IP" ]]; then
    ssh-keygen -R $IP 2>/dev/null
    response=$(make_ssh_request "$IP" "tmsh list sys software update auto-phonehome" "$BASTION_IP")
    if echo $response | grep $phonehome ; then
        result="SUCCESS"
        echo "Phonehome verified on BIG-IP1"
    fi
fi
if [[ -n "$IP2"  ]] && [[ "$IP2" != "null" ]]; then
    ssh-keygen -R $IP2 2>/dev/null
    response=$(make_ssh_request "$IP2" "tmsh list sys software update auto-phonehome" "$BASTION_IP")
    if echo $response | grep $phonehome ; then
        result2="SUCCESS"
        echo "Phonehome verified on BIG-IP2"
    fi
else
    echo "No ip address for big-ip2, no command for big-ip2 needed."
    result2="SUCCESS"
fi

# Evaluate result variables
if [[ "$result" == "SUCCESS" && "$result2" == "SUCCESS" ]]; then
    echo "Phonehome verified"
else
    echo "Phonehome not verified"
fi