#  expectValue = "Starting instance"
#  scriptTimeout = 10
#  replayEnabled = false
#  replayTimeout = 0

# start instance - required to grab logs in cases 
# where big-ip was shutdown during test.

gcloud compute instances start bigip2-<STACK NAME> --zone=<AVAILABILITY ZONE>