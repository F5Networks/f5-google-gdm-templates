#  expectValue = "SUCCESS"
#  scriptTimeout = 2
#  replayEnabled = true
#  replayTimeout = 5

# script expects verify_failover2.sh ran and has made big-ip2 active
# grab bigip2 address
bigip2_address=$(gcloud compute instances describe  bigip2-<STACK NAME> --format=json --zone=<AVAILABILITY ZONE2> | jq -r .networkInterfaces[0].networkIP)

if [[ '<EXT NETWORK SHARED VPC>' == 'None' ]]; then
    # grab route table next hop address 
    nexthop=$(gcloud compute routes describe <STACK NAME> --format=json | jq -r .nextHopIp)
else
    echo "Route table not updated in shared vpc - setting test to success"
    nexthop="$bigip2_address"
fi
echo "Route nexthop: $nexthop"
echo "bigip2 address: $bigip2_address"

# Evaluate
if [[ "$nexthop" == "$bigip2_address" ]]; then
    result="SUCCESS"
else
    result="FAILED"
fi
echo "$result"
