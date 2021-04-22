#  expectValue = "SUCCESS"
#  scriptTimeout = 10
#  replayEnabled = false
#  replayTimeout = 0

if [[ '<EXT NETWORK SHARED VPC>' == 'None' ]]; then
    self_ip=$(gcloud compute instances describe  bigip1-<STACK NAME> --format=json --zone=<AVAILABILITY ZONE> | jq -r .networkInterfaces[0].networkIP)
    response=$(gcloud compute routes create <STACK NAME> --format=json --destination-range=192.0.2.0/24 --next-hop-address=${self_ip} --network=<EXT NETWORK> --description='f5_cloud_failover_labels={"f5_cloud_failover_label":"<STACK NAME>"}')
else
    echo "route table not required for test"
    response='[{"name": "<STACK NAME>"}]'
fi
echo "Route create response: $response"

# Evaluate
if echo $response | jq -r .[].name | grep '<STACK NAME>'; then
    result="SUCCESS"
else
    result="FAILED"
fi
echo "$result"
