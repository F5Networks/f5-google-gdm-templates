#  expectValue = "PASS"
#  scriptTimeout = 5
#  replayEnabled = false
#  replayTimeout = 0


`gcloud compute instance-groups managed set-autoscaling --min-num-replicas=3 --max-num-replicas=3 --cool-down-period=1200 --target-cpu-utilization=0.8 --zone=<REGION>-b <STACK NAME>-igm`
echo "PASS"
