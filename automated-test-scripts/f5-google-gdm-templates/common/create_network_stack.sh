#  expectValue = "completed successfully"
#  scriptTimeout = 5
#  replayEnabled = false
#  replayTimeout = 0

# set vars
tmpl_file='/tmp/network.py'

# grab template and schema
curl -k file://$PWD/automated-test-scripts/f5-google-gdm-templates/common/network.py -o $tmpl_file
curl -k file://$PWD/automated-test-scripts/f5-google-gdm-templates/common/network.py.schema -o "${tmpl_file}.schema"


# Create Base config file with no optional properties
i=0
((c=<NUMBER NETWORKS>-1))
until [ $i -gt $c ]; do
    if [ $i = 0 ]; then
        /usr/bin/yq e -n ".imports[${i}].path = \"${tmpl_file}\"" > <DEWPOINT JOB ID>.yaml
    fi
    /usr/bin/yq e ".resources[${i}].name = \"network${i}\"" -i <DEWPOINT JOB ID>.yaml
    /usr/bin/yq e ".resources[${i}].type = \"network.py\"" -i <DEWPOINT JOB ID>.yaml
    /usr/bin/yq e ".resources[${i}].properties.uniqueString = \"dd-<DEWPOINT JOB ID>\"" -i <DEWPOINT JOB ID>.yaml
    /usr/bin/yq e ".resources[${i}].properties.name = \"network${i}\"" -i <DEWPOINT JOB ID>.yaml
    /usr/bin/yq e ".resources[${i}].properties.provisionPublicIp = <PUBLIC IP>" -i <DEWPOINT JOB ID>.yaml
    /usr/bin/yq e ".resources[${i}].properties.region = \"<REGION>\"" -i <DEWPOINT JOB ID>.yaml
    /usr/bin/yq e ".resources[${i}].properties.subnets[0].name = \"subnet${i}\"" -i <DEWPOINT JOB ID>.yaml
    /usr/bin/yq e ".resources[${i}].properties.subnets[0].region = \"<REGION>\"" -i <DEWPOINT JOB ID>.yaml
    /usr/bin/yq e ".resources[${i}].properties.subnets[0].ipCidrRange = \"10.0.${i}.0/24\"" -i <DEWPOINT JOB ID>.yaml
    ((i=i+1))
done


# print out config file
/usr/bin/yq e <DEWPOINT JOB ID>.yaml

labels="delete=true"

gcloud="gcloud deployment-manager deployments create network-<STACK NAME> --labels $labels --config <DEWPOINT JOB ID>.yaml"
$gcloud
