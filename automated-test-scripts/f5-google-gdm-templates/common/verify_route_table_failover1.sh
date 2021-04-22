#  expectValue = "SUCCESS"
#  scriptTimeout = 2
#  replayEnabled = true
#  replayTimeout = 5

# script expects stop instance2 ran and bigip1 is now active
# grab bigip1 address
bigip1_address=$(gcloud compute instances describe  bigip1-<STACK NAME> --format=json --zone=<AVAILABILITY ZONE> | jq -r .networkInterfaces[0].networkIP)

if [[ '<EXT NETWORK SHARED VPC>' == 'None' ]]; then
    # grab route table next hop address 
    nexthop=$(gcloud compute routes describe <STACK NAME> --format=json | jq -r .nextHopIp)
else
    echo "Route table not updated in shared vpc - setting test to success"
    nexthop="$bigip1_address"
fi
echo "Route nexthop: $nexthop"
echo "bigip1 address: $bigip1_address"

# Evaluate
if [[ "$nexthop" == "$bigip1_address" ]]; then
    result="SUCCESS"
else
    result="FAILED"
fi
echo "$result"
