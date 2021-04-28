#  expectValue = "Stopping instance"
#  scriptTimeout = 10
#  replayEnabled = false
#  replayTimeout = 0

# stop instance - required in certain cases such as failover which won't delete if
# forwarding rules are not on the original box

gcloud compute instances stop bigip2-<STACK NAME> --zone=<AVAILABILITY ZONE2>