#  expectValue = "good"
#  scriptTimeout = 5
#  replayEnabled = false
#  replayTimeout = 0

echo "Github Status"
curl -k https://raw.githubusercontent.com/F5Networks/f5-cloud-libs/master/dist/f5-cloud-libs.tar.gz -I

MGMTIP=$(gcloud compute instances describe bigip1-<STACK NAME> --zone=<AVAILABILITY ZONE> --format json|jq -r '.networkInterfaces[].accessConfigs[]?|select (.name=="Management NAT")|.natIP')
echo "MGMT IP Address =$MGMTIP"

if [ -n "$MGMTIP" ]; then
    echo "--- Verify virtual and pool exist ---"
    ssh -o "StrictHostKeyChecking no" -o ConnectTimeout=3 -i /etc/ssl/private/dewpt_private.pem admin@${MGMTIP} 'tmsh list ltm virtual'
    ssh -o "StrictHostKeyChecking no" -o ConnectTimeout=3 -i /etc/ssl/private/dewpt_private.pem admin@${MGMTIP} 'tmsh list ltm pool recursive'
    echo "--- Verify DNS to metadata server works ---"
    ssh -o "StrictHostKeyChecking no" -o ConnectTimeout=3 -i /etc/ssl/private/dewpt_private.pem admin@${MGMTIP} 'dig metadata.google.internal'
    ssh -o "StrictHostKeyChecking no" -o ConnectTimeout=3 -i /etc/ssl/private/dewpt_private.pem admin@${MGMTIP} 'ping -c 3 metadata.google.internal'
else
    echo "Bigip1Url not found in stack <STACK NAME>"
fi
ssh-keygen -R $MGMTIP 2>/dev/null
