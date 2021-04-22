#  expectValue = "Deleted"
#  scriptTimeout = 10
#  replayEnabled = false
#  replayTimeout = 0

if [[ '<EXT NETWORK SHARED VPC>' == 'None' ]]; then
    gcloud compute routes delete <STACK NAME> --quiet
else
    echo "Deleted"
    echo "Route table not created for test"
fi