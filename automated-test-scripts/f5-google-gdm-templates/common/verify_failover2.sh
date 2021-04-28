#  expectValue = "Test Passed"
#  scriptTimeout = 2
#  replayEnabled = true
#  replayTimeout = 5

TMP_DIR="/tmp/<DEWPOINT JOB ID>"
STATE_FILE=${TMP_DIR}/state.json

# source test functions
source ${TMP_DIR}/test_functions.sh

IP=$(cat ${STATE_FILE} | jq -r '.mgmtAddress')
IP2=$(cat ${STATE_FILE} | jq -r '.mgmtAddress2')
BASTION_IP=$(cat ${STATE_FILE} | jq -r '.proxyAddress')

# Verify BIG-IP2 is active, if not make active
show_failover='tmsh show sys failover'
run_cmd='tmsh run sys failover standby'
ssh-keygen -R $IP 2>/dev/null
ssh-keygen -R $IP2 2>/dev/null
bigip1_failover_state=$(make_ssh_request "$IP" "$show_failover" "$BASTION_IP")
if echo $bigip1_failover_state | grep "active"; then
    make_ssh_request "$IP" "$run_cmd" "$BASTION_IP"
    echo "BIGIP2 set to active:"
    make_ssh_request "$IP2" "$show_failover" "$BASTION_IP"
else
    echo "bigip2 is already active:"
    make_ssh_request "$IP2" "$show_failover" "$BASTION_IP"
fi
# wait a few seconds for CFE to fialover
sleep 10

aliasIpTestPass=false
forwardingRuleTestPass=false

BIGIP='bigip2-<STACK NAME>'
vmInterfaces=$(gcloud compute instances describe $BIGIP --zone=<AVAILABILITY ZONE2> --format json | jq -c .networkInterfaces)
alias_ip=$(get_state aliasIP)

# if alias IP is in our network interfaces we know it failed over
echo "check alias ips failed over: $vmInterfaces"
echo "Alias IP: $alias_ip"
if echo $vmInterfaces | grep --silent $(echo ${alias_ip} | cut -d ';' -f1) || [[ '<ALIAS IP>' == 'False' ]]; then
    aliasIpTestPass=true
fi

if [[ "<STACK>" == *"existing"* && "<NUM FORWARDING RULES>" != "0" ]] ; then
    forwardingRules=$(gcloud compute forwarding-rules list --format json --filter="name~'<STACK NAME>*'"| jq -c .)
    echo "check forwarding rules failed over: $forwardingRules"
    for rule in $(echo $forwardingRules | jq -c -r '.[]') ; do
        # if any rule has our instance as the target we know it failed over
        if echo $rule | grep --silent $BIGIP ; then
            echo "Rule: $rule"
            forwardingRuleTestPass=true
        fi
    done
else
    # no forwarding rules, mark as pass
    forwardingRuleTestPass=true
fi

echo "aliasIpTestPass: $aliasIpTestPass forwardingRuleTestPass: $forwardingRuleTestPass"
if $aliasIpTestPass && $forwardingRuleTestPass ; then
    echo "Test Passed"
fi