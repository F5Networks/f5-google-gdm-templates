#  expectValue = "completed successfully"
#  scriptTimeout = 5
#  replayEnabled = false
#  replayTimeout = 0

template_url=<TEMPLATE URL>
yaml_url=${template_url/%py/yaml}
echo "template_url = $template_url"
echo "yaml_url = $yaml_url"
template_file=$(basename "$template_url")
yaml_file=$(basename "$yaml_url")
echo "template_file = $template_file"
echo "yaml_file = $yaml_file"
tmpl_file="/tmp/$template_file"
tmpl_file2="/tmp/$yaml_file"
echo "tmpl_file = $tmpl_file"
echo "tmpl_file2 = $tmpl_file2"
rm -f $tmpl_file $tmpl_file2

curl -k $template_url -o $tmpl_file
curl -k $yaml_url -o $tmpl_file2

# Run GDM template
properties="region:'<REGION>',availabilityZone1:'<AVAILABILITY ZONE>',mgmtNetwork:'dewpt',mgmtSubnet:'subnet1',imageName:'<IMAGE NAME>',instanceType:'<INSTANCE TYPE>',manGuiPort:8443,bigIpModules:'<BIGIP MODULES>',serviceAccount:'dewpt-autoscale-service-acount@f5-7656-pdsoleng-dev.iam.gserviceaccount.com',targetSize:2,minReplicas:2,maxReplicas:8,cpuUtilization:0.8,coolDownPeriod:600,policyLevel:'low',applicationPort:80,applicationDnsName:'www.example.com',allowUsageAnalytics:'<ANALYTICS>',declarationUrl:'<DECLARATION URL>'"
echo $properties
gcloud deployment-manager deployments create <STACK NAME> --template $tmpl_file --labels "delete=true" --properties $properties

# gcloud deployment-manager deployments create <STACK NAME> --config $tmpl_file2

# clean up file on disk
rm -f $tmpl_file $tmpl_file2