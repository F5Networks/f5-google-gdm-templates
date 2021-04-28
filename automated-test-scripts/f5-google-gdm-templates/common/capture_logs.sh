#  expectValue = "--- <DEWPOINT JOB ID> install.log"
#  scriptTimeout = 5
#  replayEnabled = false
#  replayTimeout = 0

TMP_DIR=/tmp/<DEWPOINT JOB ID>
STATE_FILE=${TMP_DIR}/state.json

# source test functions
source ${TMP_DIR}/test_functions.sh

IP=$(cat ${STATE_FILE} | jq -r '.mgmtAddress')
IP2=$(cat ${STATE_FILE} | jq -r '.mgmtAddress2')
BASTION_IP=$(cat ${STATE_FILE} | jq -r '.proxyAddress')
result=''
result2=''

# Grab logs for failover test
if [ -n "$IP2"  ] && [ "$IP2" != "null" ]; then
    echo "MGMT IP Address bigip1 =$IP"
    echo "MGMT IP Address bigip2 =$IP2"
    LOGS="cloudLibsError.log install.log mgmt-swap.log interface-config.log onboard.log custom-config.log cluster.log generatePassword.log createUser.log rm-password.log create-va.log cfn-init.log ltm restjavad.0.log restnoded.log cfe_config.json tgactive"
    for LOG in $LOGS; do
        if [ "cfn-init.log" = ${LOG} ] || [ "ltm" = ${LOG} ] || [ "restjavad.0.log" = "${LOG}" ]; then
            base='/var/log/'
        elif [ "restnoded.log" = ${LOG} ]; then
            base='/var/log/restnoded/'
        elif [ "cfe_config.json" = ${LOG} ]; then
            base='/config/cloud/'
        elif [ "tgactive" = ${LOG} ]; then
            base='/config/failover/'
        else
            base='/var/log/cloud/google/'
        fi
        echo "--- <DEWPOINT JOB ID> ${LOG} bigip1 ---"
        make_scp_request "$IP" "$base" "${LOG}" "$BASTION_IP"
        cat /tmp/<DEWPOINT JOB ID>-${LOG} 2>/dev/null
        echo
        rm /tmp/<DEWPOINT JOB ID>-${LOG}
        echo "--- <DEWPOINT JOB ID> ${LOG} bigip2 ---"
        make_scp_request "$IP2" "$base" "${LOG}" "$BASTION_IP"
        cat /tmp/<DEWPOINT JOB ID>-${LOG} 2>/dev/null
        echo
    done
# Grab logs for autoscale and standalone
else
    echo "MGMT IP Address =$IP"
    LOGS="cloudLibsError.log install.log mgmt-swap.log interface-config.log onboard.log custom-config.log cfn-init.log ltm restjavad.0.log restnoded.log" 
    for LOG in $LOGS; do
        if [ "cfn-init.log" = ${LOG} ] || [ "ltm" = ${LOG} ] || [ "restjavad.0.log" = "${LOG}" ]; then
            base='/var/log/'
        elif [ "restnoded.log" = ${LOG} ]; then
            base='/var/log/restnoded/'
        else
            base='/var/log/cloud/google/'
        fi
        echo "--- <DEWPOINT JOB ID> $LOG ---"
        make_scp_request "$IP" "$base" "$LOG" "$BASTION_IP"
        cat /tmp/<DEWPOINT JOB ID>-${LOG} 2>/dev/null
        echo
        rm /tmp/<DEWPOINT JOB ID>-${LOG}
    done
fi