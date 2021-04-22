#!/usr/bin/env bash
#  expectValue = "SUCCESS"
#  scriptTimeout = 2
#  replayEnabled = true
#  replayTimeout = 10

TMP_DIR="/tmp/<DEWPOINT JOB ID>"

# source test functions
source ${TMP_DIR}/test_functions.sh

IP=$(cat ${STATE_FILE} | jq -r '.mgmtAddress')
IP2=$(cat ${STATE_FILE} | jq -r '.mgmtAddress2')
BASTION_IP=$(cat ${STATE_FILE} | jq -r '.proxyAddress')

# Verify BIG-IP1 is active, if not make active
show_failover='tmsh show sys failover'
run_cmd='tmsh run sys failover standby'
ssh-keygen -R $IP 2>/dev/null
ssh-keygen -R $IP2 2>/dev/null
bigip2_failover_state=$(make_ssh_request "$IP2" "$show_failover" "$BASTION_IP")
if echo $bigip2_failover_state | grep "active"; then
    make_ssh_request "$IP2" "$run_cmd" "$BASTION_IP"
    echo "BIGIP1 set to active:"
    make_ssh_request "$IP" "$show_failover" "$BASTION_IP"
else
    echo "bigip1 is already active:"
    make_ssh_request "$IP" "$show_failover" "$BASTION_IP"
fi
# Collect External target pool state and evaluate against active bigip
BIGIP="bigip1-<STACK NAME>"
if [[ "<NUM FORWARDING RULES>" != "0" ]] ; then
    capture_unhealthy_tp=$(gcloud compute target-pools get-health <STACK NAME>-tp --region <REGION> --format json |jq -c '[.[].healthStatus[] |select( .healthState == "UNHEALTHY")|.instance]')
    capture_healthy_tp=$(gcloud compute target-pools get-health <STACK NAME>-tp --region <REGION> --format json |jq -c '[.[].healthStatus[] |select( .healthState == "HEALTHY")|.instance]')
    echo "check target pool failed over to bigip1: $capture_healthy_tp"
    for rule in $(echo $capture_healthy_tp | jq -c -r '.[]') ; do
        # if any fowarding rule ip has our instance as the target we know it failed over
        if echo $rule | grep --silent $BIGIP ; then
            echo "Rule: $rule"
            forwardingRuleTestPass=true
        fi
    done
else
    # no forwarding rules, mark as pass
    forwardingRuleTestPass=true
    capture_unhealthy_tp="none"
    capture_healthy_tp="none"
fi
# Verify BIG-IP2 is active, if not make active
bigip1_failover_state=$(make_ssh_request "$IP" "$show_failover" "$BASTION_IP")
if echo $bigip1_failover_state | grep "active"; then
    make_ssh_request "$IP" "$run_cmd" "$BASTION_IP"
    echo "BIGIP2 set to active:"
    make_ssh_request "$IP2" "$show_failover" "$BASTION_IP"
else
    echo "bigip2 is already active:"
    make_ssh_request "$IP2" "$show_failover" "$BASTION_IP"
fi
# wait a few seconds for failover
sleep 10

# Collect target pool state and evaluate against active bigip
BIGIP="bigip2-<STACK NAME>"
if [[ "<NUM FORWARDING RULES>" != "0" ]] ; then
    capture_unhealthy_tp2=$(gcloud compute target-pools get-health <STACK NAME>-tp --region <REGION> --format json |jq -c '[.[].healthStatus[] |select( .healthState == "UNHEALTHY")|.instance]')
    capture_healthy_tp2=$(gcloud compute target-pools get-health <STACK NAME>-tp --region <REGION> --format json |jq -c '[.[].healthStatus[] |select( .healthState == "HEALTHY")|.instance]')
    echo "check target pool failed over to bigip2: $capture_healthy_tp2"
    for rule in $(echo $capture_healthy_tp2 | jq -c -r '.[]') ; do
        # if any fowarding rule ip has our instance as the target we know it failed over
        if echo $rule | grep --silent $BIGIP ; then
            echo "Rule: $rule"
            forwardingRuleTestPass2=true
        fi
    done
else
    # no forwarding rules, mark as pass
    forwardingRuleTestPass2=true
fi

echo "forwardingRuleTestPass: $forwardingRuleTestPass forwardingRuleTestPass2: $forwardingRuleTestPass2"
if $forwardingRuleTestPass && $forwardingRuleTestPass2 ; then
    echo "SUCCESS"
else
    echo "FAILED"
    echo "capture_unhealthy_fp: $capture_unhealthy_fp"
    echo "capture_healthy_fp: $capture_healthy_fp"
    echo "capture_unhealthy_fp2: $capture_unhealthy_fp2"
    echo "capture_healthy_fp2: $capture_healthy_fp2"
fi