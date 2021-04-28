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

## validate all items in list are in response
provisioned_list=$(echo "<BIGIP MODULES>" | sed 's/-/ /g')
matched_list=()
matched_list2=()
for module in ${provisioned_list[@]}; do
    i_length=$((i_length+1))
    IFS=':' # colon is set as delimiter
    read -ra MOD_LEV <<< "$module" # str is read into an array as tokens separated by IFS
	  echo "Checking for module: $module"
    if [ -n "$IP" ]; then
      response=$(make_ssh_request "$IP" "tmsh list /sys provision ${MOD_LEV[0]}" "$BASTION_IP")
      for i in $response; do
        if echo $i | grep "${MOD_LEV[1]}" --silent; then
          echo "match: $i $module"
          matched_list+=("$module")
        fi
      done
    r_length=${#matched_list[@]}
    echo "i_length: $i_length r_length: $r_length"
    if (( "$r_length" >= "$i_length" )); then
      result="SUCCESS"
    else
      result="FAILURE"  
    fi
  fi
  if [ -n "$IP2"  ] && [ "$IP2" != "null" ]; then
    response2=$(make_ssh_request "$IP2" "tmsh list /sys provision ${MOD_LEV[0]}" "$BASTION_IP")
    for i in $response2; do
      if echo $i | grep "${MOD_LEV[1]}" --silent; then
        echo "match: $i $module"
        matched_list2+=("$module")
      fi
    done
    r2_length=${#matched_list2[@]}
    if (( "$r2_length" >= "$i_length" )); then
	    result2="SUCCESS"
    else
      result2="FAILURE"
    fi
  else
    response2="No BIGIP2 to evaluate"
    result2="SUCCESS"
  fi
done

# Evaluate result variables
if [[ "$result" == "SUCCESS" && "$result2" == "SUCCESS" ]]; then
    echo "SUCCESS"
    echo "Response for bigip1: $response"
    echo "Response for bigip2: $response2"
else
    echo "FAILURE"
    echo "Response for bigip1: $response"
    echo "Response for bigip2: $response2"
fi