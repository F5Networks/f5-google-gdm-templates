#  expectValue = "SUCCESS"
#  scriptTimeout = 3
#  replayEnabled = false
#  replayTimeout = 1

TMP_DIR=/tmp/<DEWPOINT JOB ID>
STATE_FILE=${TMP_DIR}/state.json

## Grab network and subnet information
network=$(gcloud compute instances describe bigip1-<STACK NAME> --zone <AVAILABILITY ZONE> --format json |jq -c .networkInterfaces[].network)
subnet=$(gcloud compute instances describe bigip1-<STACK NAME> --zone <AVAILABILITY ZONE> --format json |jq -c .networkInterfaces[].subnetwork)
sharedVpcPassed=false
sharedSubVpcPassed=false
# Set Project info for each network based on number of nics
case <NIC COUNT> in
1)
    case "<MGMT NETWORK SHARED VPC>" in
    None)
        mgmtSharedVpc="f5-7656-pdsoleng-dev" ;;
    *)
        mgmtSharedVpc="<MGMT NETWORK SHARED VPC>" ;;
    esac
    net_filter="\<${mgmtSharedVpc}/global/networks/dewpt\>"
    sub_filter="${mgmtSharedVpc}/regions/<REGION>/subnetworks/subnet1" ;;
*)
    case "<EXT NETWORK SHARED VPC>" in
    None)
        network1SharedVpc="f5-7656-pdsoleng-dev" ;;
    *)
        network1SharedVpc="<EXT NETWORK SHARED VPC>" ;;
    esac
    net_filter="${network1SharedVpc}/global/networks/dewpt2"
    sub_filter="${network1SharedVpc}/regions/<REGION>/subnetworks/subnet2" ;;
esac

## evaluate network and subnet results
for net in $network; do
    if echo $net | grep "${net_filter}"; then
        sharedVpcPassed=true
    fi
done
for sub in $subnet; do
    if echo $sub | grep "${sub_filter}"; then
        sharedSubVpcPassed=true
    fi
done

## evaluate all varables true
if [ $sharedVpcPassed ] && [ $sharedSubVpcPassed ]; then
    echo "SUCCESS"
    echo "sharedNet:$sharedVpcPassed, sharedSub:$sharedSubVpcPassed"
else
    echo "FAILED"
    echo "sharedNet:$sharedVpcPassed, sharedSub:$sharedSubVpcPassed"
fi