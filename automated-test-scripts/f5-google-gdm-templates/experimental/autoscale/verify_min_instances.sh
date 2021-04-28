#  expectValue = "PASS"
#  scriptTimeout = 5
#  replayEnabled = false
#  replayTimeout = 0

tp=`gcloud deployment-manager deployments describe <STACK NAME>|grep "targetPool"|cut -d " " -f1`
echo "tp=$tp"
healthy=`gcloud compute target-pools get-health $tp --region <REGION>|grep "healthState: HEALTHY"|wc -l`
echo "healthy=$healthy"

if [ $healthy -eq 2 ]; then
    echo "PASS"
else
    echo "FAIL"
fi