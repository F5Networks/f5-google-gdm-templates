#  expectValue = "COMPLETED"
#  scriptTimeout = 10
#  replayEnabled = false
#  replayTimeout = 0

TMP_DIR='/tmp/<DEWPOINT JOB ID>'

# Provision a bastion host (via a GDM template) if needed
if [[ "<PUBLIC IP>" == "False" ]]; then
    echo "No public ip case; preparing for bastion vm provisioning"
    tmpl_file="${TMP_DIR}/f5-bastion-template.py"
    curl -k file://$PWD/automated-test-scripts/f5-google-gdm-templates/common/f5-bastion-template.py -o $tmpl_file
    echo "Starting provisioning bastion host"
    if [[ "<NIC COUNT>" == "1" ]]; then
        shared_vpcs=",network1SharedVpc:'<MGMT NETWORK SHARED VPC>'"
    else
        shared_vpcs=",network1SharedVpc:'<EXT NETWORK SHARED VPC>'" 
    fi
    # setup shared vpc
    if [[ "<NIC COUNT>" == "1" ]]; then
        if [[ "<MGMT NETWORK SHARED VPC>" == "None" ]]; then
            mgmt_net='<NETWORK>'
            mgmt_subnet='<SUBNET1 AZ1>'
            network1='dd-<DEWPOINT JOB ID>-network1-network'
            subnet1='dd-<DEWPOINT JOB ID>-subnet1-subnet'
        else
            mgmt_net='dewpt'
            mgmt_subnet="subnet1"
            network1='dd-<DEWPOINT JOB ID>-network1-network'
            subnet1='dd-<DEWPOINT JOB ID>-subnet1-subnet'
        fi
    else
        if [[ "<EXT NETWORK SHARED VPC>" == "None" ]]; then
            mgmt_net='<NETWORK>'
            mgmt_subnet='<SUBNET1 AZ1>'
            network1='<EXT NETWORK>'
            subnet1='<EXT SUBNET>'
        else
            mgmt_net='<NETWORK>'
            mgmt_subnet='<SUBNET1 AZ1>'
            network1='dewpt2'
            subnet1='subnet2'
        fi
    fi
    properties="region:'<REGION>',zone:'<AVAILABILITY ZONE>',instanceType:'n1-standard-1',osImage:'projects/ubuntu-os-cloud/global/images/family/ubuntu-1604-lts',mgmtNetwork:'${mgmt_net}',mgmtSubnet:'${mgmt_subnet}',network1:'${network1}',subnet1:'${subnet1}'${shared_vpcs}"
    echo $properties
    gcloud deployment-manager deployments create bastion-<DEWPOINT JOB ID>  --labels "delete=true" --template ${TMP_DIR}/f5-bastion-template.py --properties $properties
else
    echo "COMPLETED"
fi