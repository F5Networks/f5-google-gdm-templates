#  expectValue = "completed successfully"
#  scriptTimeout = 10
#  replayEnabled = false
#  replayTimeout = 0

TMP_DIR=/tmp/<DEWPOINT JOB ID>
STATE_FILE=${TMP_DIR}/state.json

# source test functions
source ${TMP_DIR}/test_functions.sh

IP=$(cat ${STATE_FILE} | jq -r '.mgmtAddress')
IP2=$(cat ${STATE_FILE} | jq -r '.mgmtAddress2')
BASTION_IP=$(cat ${STATE_FILE} | jq -r '.proxyAddress')

# Verify BIG-IP2 is active, if not make active -  need to have this in order to delete resources
show_failover='tmsh show sys failover'
run_cmd='tmsh run sys failover standby'
ssh-keygen -R $IP 2>/dev/null
ssh-keygen -R $IP2 2>/dev/null
bigip1_failover_state=$(make_ssh_request "$IP" "$show_failover" "$BASTION_IP")
if echo $bigip1_failover | grep "active"; then
    make_ssh_request "$IP" "$run_cmd" "$BASTION_IP"
    echo "BIGIP2 set to active:"
    make_ssh_request "$IP2" "$show_failover" "$BASTION_IP"
else
    echo "bigip2 is already active:"
    make_ssh_request "$IP2" "$show_failover" "$BASTION_IP"
fi
# wait a few seconds for CFE to fialover
sleep 5
# clean up dewpoint tmp directory
rm -rf /tmp/<DEWPOINT JOB ID>
gcloud deployment-manager deployments delete <STACK NAME> -q

if [[ "<PUBLIC IP>" == "False" ]]; then

    echo "This is no public ip case; deleting Bastion VM"
    gcloud deployment-manager deployments delete bastion-<DEWPOINT JOB ID> -q

fi