#  expectValue = "SUCCESS"
#  expectFailValue = "FAILED"
#  scriptTimeout = 2
#  replayEnabled = true
#  replayTimeout = 30

TMP_DIR='/tmp/<DEWPOINT JOB ID>'
STATE_FILE=${TMP_DIR}/state.json

# source test functions
source ${TMP_DIR}/test_functions.sh

IP=$(cat ${STATE_FILE} | jq -r '.mgmtAddress')
IP2=$(cat ${STATE_FILE} | jq -r '.mgmtAddress2')
BASTION_IP=$(cat ${STATE_FILE} | jq -r '.proxyAddress')

# Check if a bastion host/deployment was created. If so, check whether it's provisioned
if [[ "<PUBLIC IP>" == "False" ]]; then
# add fw tag
    gcloud compute instances add-tags bastion-<DEWPOINT JOB ID> --tags=mgmtfw-<STACK NAME> --zone=<AVAILABILITY ZONE>
    # Have Dewdrop implicitly check GDM for 'failure case' (where response is expectFailValue)
    # Not using an explicit succcess check here; success check is preformed by checking 'verify_response'
    gcloud deployment-manager deployments describe bastion-<DEWPOINT JOB ID>

    # NOTE: Its possible for sshguard to consider our recurring SSH requests as SSH attacks, and will blacklist
    # IP addresses it deems as attackers. Explicitly add our IP address to sshguard's whitelist
    source_ip=$(curl https://ipecho.net/plain)
    echo "source_ip = $source_ip"

    ssh-keygen -R $BASTION_IP 2>/dev/null
    whitelist_cmd="echo ${source_ip} | sudo tee -a /etc/sshguard/whitelist"
    response=$(ssh -o "StrictHostKeyChecking=no" -o ConnectTimeout=3 -i /etc/ssl/private/dewpt_private.pem dewpt@"$BASTION_IP" "${whitelist_cmd}")

    verify_cmd="cat /etc/sshguard/whitelist"
    verify_response=$(ssh -o "StrictHostKeyChecking=no" -o ConnectTimeout=3 -i /etc/ssl/private/dewpt_private.pem dewpt@"$BASTION_IP" "${verify_cmd}")

    if echo $verify_response | grep "${source_ip}"; then
        echo "SUCCESS"
        echo "Source IP Address whitelisted"
    else
        echo "Address not yet whitelised"
    fi
else
    echo "SUCCESS"
    echo "Bastion host verification not needed - bastion host not needed"
fi
