#!/usr/bin/env bash
#  expectValue = "NETWORK CREATION PASSED"
#  scriptTimeout = 3
#  replayEnabled = true
#  replayTimeout = 3

# Script confirms config file and resources created in gcloud match using network names.
network_names=($(/usr/bin/yq e .resources[].name <DEWPOINT JOB ID>.yaml))
unique_string=$(/usr/bin/yq e .resources[0].properties.uniqueString <DEWPOINT JOB ID>.yaml)
dash="-"
networks=()

for i in "${network_names[@]}"; do
    networks+=("$unique_string$dash$i${dash}network")
done

networks_gcloud=$(gcloud compute networks list --format json | jq -r --arg n "<DEWPOINT JOB ID>" '.[] | select(.name | contains($n)) | .name')


if echo "${networks[*]}" | grep "$networks_gcloud"; then
    echo "NETWORK CREATION PASSED"
else
    echo "Network names do not match"
    echo "Config File:${networks[*]}"
    echo "Resources Created:$networks_gcloud"
fi