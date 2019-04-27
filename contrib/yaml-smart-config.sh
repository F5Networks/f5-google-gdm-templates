#!/usr/bin/env bash
set -e

function print_help() {
  echo "use: $0 <deployment name> <yaml file> [<project name>]"
  echo "examples:"
  echo " $0 myBigip1 f5-existing-stack-byol-3nic-bigip.yaml"
  echo " $0 myBigip2 ../bigip2/f5-existing-stack-byol-3nic-bigip.yaml my-non-default-GCPprojectName"
  echo; echo -e "Description: This script tries to be smart in updating some fields in the gdm yaml file.\nIn particular it tries to set vpc network names based on the specified subnet (retrieved via gcloud cmds) and creates static addresses for each of the networks as well. The region field is derieved from the defined availabilityZone1 field and ntpServer is set to the default GCP 169.254.169.254 value.\nUsing this script the following parameters are set automatically:\n- region (based on availabilityZone1)\n- mgmtNetwork (based on mgmtSubnet)\n- network1 (based on subnet1)\n- network2 (based on subnet2)\n- ntpServer\n- Address fields are populated with reserved addresses (created by gcloud)\n\nAny field which has no default value will not be populated, except for *Address fields, which are always updated."
  echo -e "\nThe following fields must be configured before running this script:\n - availabilityZone1\n - mgmtSubnet\n - subnet1 (if it exists in template)\n - subnet2 (if it exists in template)"
  exit 0
}
function gcp_create_address() {
  local addrname=$1 addrsubnet=$2
  gcloud $project compute addresses create $addrname --region $region --subnet=$addrsubnet 2>/dev/null
  echo $(gcloud $project compute addresses describe $addrname --region $region | grep -oP '^address: \K.+')
}
function update_yaml() {
  local key=$1 value=$2
  sed -i -e "s/$key:.*/$key: $value/" $yaml
}
function read_yaml_value() {
  local key=$1
  echo $(grep -oP "${key}:\s*\K.+" $yaml | sed -e 's/"//g' -e "s/'//g")
}
function yaml_key_exists() {
  local key=$1
  grep " $key:" $yaml >/dev/null
}

# print help
[[ "$1" == "--help" ]] && print_help; [[ "$1" == "-help" ]] && print_help; [[ "$1" == "-h" ]] && print_help;

## read parameters
[[ -z "$1" ]] && echo "error: deployment name not specified" && print_help && exit 1
name=$1

# check if yaml file exists
[[ ! -f "$2" ]] && echo "error: yaml file not specified" && print_help && exit 1
yaml=$2

# read project from second optional parameter or from gcloud settings
project=""
[[ $# == 3 ]] && project="$3" || project=$(gcloud config get-value project)
[[ -z "$project" ]] && echo "error: no project specified nor default project set" && print_help && exit 1

echo -e "* starting yaml update for:\n   deployment:$name\n   yaml file:$yaml\n   project:$project"
project="--project $project"

# read each key from yaml and set shell variable to its value
for key in region availabilityZone1 mgmtSubnet subnet1 subnet2 ntpServer mgmtNetwork network1 network2
do
  export $key="$(read_yaml_value $key)"
done

# basic checks - could probably need enhancement, eg. using gcloud commands to check if values actually match existing networks
echo "* checking if required yaml keys are set: availabilityZone1, mgmtSubnet, (subnet1, subnet2)"
[[ $availabilityZone1 =~ ^\<.*$ ]] && echo "error: availabilityZone1 not set" && exit 1
[[ $mgmtSubnet =~ ^\<.*$ ]] && echo "error: mgmtSubnet not set " && exit 1
yaml_key_exists subnet1 && [[ $subnet1 =~ ^\<.*$ ]] && echo "error: subnet1 not set" && exit 1
yaml_key_exists subnet2 && [[ $subnet2 =~ ^\<.*$ ]] && echo "error: subnet2 not set" && exit 1

# set region based on availabilityZone1
[[ $region =~ ^\<.*$ ]] && \
  region=$(echo $availabilityZone1 | awk -F"-" '{print $1"-"$2}') && \
  update_yaml region $region && \
  echo "* updated region:$region based on availabilityZone1:$availabilityZone1"

# set ntpServer to GCP default
[[ $ntpServer =~ ^\<.*$ ]] && \
  ntpServer=169.254.169.254 && \
  update_yaml ntpServer $ntpServer && \
  echo "* updated ntpServer:$ntpServer (GCP default)"

# set mgmtNetwork from mgmtSubnet
[[ $mgmtNetwork =~ ^\<.*$ ]] && \
  mgmtNetwork=$(gcloud $project compute networks subnets describe $mgmtSubnet --region $region | grep -oP '^network:.+networks/\K.+') && \
  update_yaml mgmtNetwork $mgmtNetwork && \
  echo "* updated mgmtNetwork:$mgmtNetwork based on mgmtSubnet:$mgmtSubnet"

# set network1 from subnet1 
[[ $network1 =~ ^\<.*$ ]] && \
  network1=$(gcloud $project compute networks subnets describe $subnet1 --region $region | grep -oP '^network:.+networks/\K.+') && \
  update_yaml network1 $network1 && \
  echo "* updated network1:$network1 based on subnet1:$subnet1"

# set network2 from subnet2
[[ $network2 =~ ^\<.*$ ]] && \
  network2=$(gcloud $project compute networks subnets describe $subnet2 --region $region | grep -oP '^network:.+networks/\K.+') && \
  update_yaml network2 $network2 && \
  echo "* updated network2:$network2 based on subnet2:$subnet2"

echo "* creating static IP addresses:"
mgmtSubnetAddress=$(gcp_create_address ${name}-mgmt $mgmtSubnet)
subnet1Address=$(gcp_create_address ${name}-1 $subnet1)
subnet2Address=$(gcp_create_address ${name}-2 $subnet2)
update_yaml mgmtSubnetAddress $mgmtSubnetAddress
echo "   mgmtSubnetAddress:$mgmtSubnetAddress"
update_yaml subnet1Address $subnet1Address
echo -n "   subnet1Address:$subnet1Address"
update_yaml subnet2Address $subnet2Address
echo "   subnet2Address:$subnet2Address"

echo "to proceed with the deployment run:"
echo "# gcloud deployment-manager deployments create $name --config $yaml --description \"<optional-deployment-description>\""