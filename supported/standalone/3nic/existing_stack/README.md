# Deploying the BIG-IP in Google Cloud - 3 NIC

[![Slack Status](https://f5cloudsolutions.herokuapp.com/badge.svg)](https://f5cloudsolutions.herokuapp.com)

**Contents**

 - [Introduction](#introduction) 
 - [Prerequisites](#prerequisites-and-notes)
 - [Security](#security)
 - [Deploying the Template](#deploying-the-template)
 
 
## Introduction
This solution uses a Google Deployment Manager Template to launch a 3 NIC deployment a BIG-IP VE in an Google Virtual Private Cloud. Traffic flows from the BIG-IP VE to the application servers. This is the standard "on-premise like" cloud design where the compute instance of F5 is running with a management, front-end application traffic (virtual server), and a back-end application interface.  

The BIG-IP VE has the <a href="https://f5.com/products/big-ip/local-traffic-manager-ltm">Local Traffic Manager</a> (LTM) module enabled to provide advanced traffic management functionality. This means you can also configure the BIG-IP VE to enable F5's L4/L7 security features, access control, and intelligent traffic management.
 
The **existing stack** Google Deployment Manager template incorporates existing networks.


## Prerequisites
The following are prerequisites for the F5 3 NIC GDM template:
  - You must have installed the Google Cloud SDK (https://cloud.google.com/sdk/downloads)
  - If using BYOL licensing only: An F5 Networks BYOL license (Bring Your Own License) available.
  - Two Google Cloud Platform (GCP) networks with at least one subnet in each. The subnet for the management network requires a route and access to the Internet for the initial configuration to download the BIG-IP cloud library.
  - Key pair for SSH access to BIG-IP VE (you can create or import this in Google Cloud).
  - An Google Firewall rule with the following inbound rules:
    - Port 22 for SSH access to the BIG-IP VE.
    - Port 443 (or other port) for accessing the BIG-IP web-based Configuration utility.
    - A port for accessing your applications via the BIG-IP virtual server.
  - This solution uses the SSH key to enable access to the BIG-IP system. If you want access to the BIG-IP web-based Configuration utility, you must first SSH into the BIG-IP VE using the SSH key you provided in the template.  You can then create a user account with admin-level permissions on the BIG-IP VE to allow access if necessary.
  - You must use a BIG-IP instance that has at least 4 vCPU and 8 GB memory. For each additional vCPU, add at least 2 GB of memory.   
  **Important**: For this 3 NIC template, you MUST use a machine type of at least **n1-standard-4**.  See https://cloud.google.com/vpc/docs/create-use-multiple-interfaces#max-interfaces for more information about required vCPUs and interfaces.  
  Note: Because of this requirement, the *n1-highcpu* instance types are not supported.  

## Important configuration notes
  - This template supports service discovery.  See the [Service Discovery section](#service-discovery) for details.  
  - F5 has created a matrix that contains all of the tagged releases of the F5 Google GDM templates, and the corresponding BIG-IP versions, license types and throughput levels available for a specific tagged release. See https://github.com/F5Networks/f5-google-gdm-templates/blob/master/google-bigip-version-matrix.md.


  
### Security
This GDM template downloads helper code to configure the BIG-IP system. If you want to verify the integrity of the template, you can open the GDM template and ensure the following lines are present. See [Security Detail](#securitydetail) for the exact code in each of the following sections.
  - In the */config/verifyHash* section: **script-signature** and then a hashed signature
  - In the */config/installCloudLibs.sh* section **"tmsh load sys config merge file /config/verifyHash"**
  
  Additionally, F5 provides checksums for all of our supported Google Deployment Manager templates. For instructions and the checksums to compare against, see https://devcentral.f5.com/codeshare/checksums-for-f5-supported-cft-and-arm-templates-on-github-1014.
  


### Help 
**F5 Support**  
Because this template has been created and fully tested by F5 Networks, it is fully supported by F5. This means you can get assistance if necessary from [F5 Technical Support](https://support.f5.com/csp/article/K25327565).

**Community Support**  
We encourage you to use our [Slack channel](https://f5cloudsolutions.herokuapp.com) for discussion and assistance on F5 Google GDM templates. There are F5 employees who are members of this community who typically monitor the channel Monday-Friday 9-5 PST and will offer best-effort assistance. This slack channel community support should **not** be considered a substitute for F5 Technical Support. See the [Slack Channel Statement](https://github.com/F5Networks/f5-google-gdm-templates/blob/master/slack-channel-statement.md) for guidelines on using this channel.



## Deploying the template
This solution uses a YAML file for containing the parameters necessary to deploy the BIG-IP instance in Google Cloud.  The YAML file you use depends on whether you are using BYOL or PAYG (Pay As You Go) licensing:  
  - BYOL: [**f5-existing-stack-byol-3nic-bigip.yaml**](https://github.com/F5Networks/f5-google-gdm-templates/blob/master/supported/standalone/3nic/existing_stack/BYOL/f5-existing-stack-byol-3nic-bigip.yaml)  
  - PAYG: [**f5-existing-stack-payg-3nic-bigip.yaml**](https://github.com/F5Networks/f5-google-gdm-templates/blob/master/supported/standalone/3nic/existing_stack/PAYG/f5-existing-stack-byol-3nic-bigip.yaml)
  
You ***must edit the YAML file*** to include information for your deployment before using the file to launch the BIG-IP VE instance.
1. Make sure you have completed all of the [prerequisites](#prerequisites). 
2. [Edit the parameters](#edit-the-yaml-file) in the appropriate YAML file as described in this section.
3. [Save the YAML file](#save-the-yaml-file).
4. [Deploy the BIG-IP VE](#deploy-the-big-ip-ve) from the command line. 

### Edit the YAML file
After completing the prerequisites, edit the YAML file.  You must replace the following parameters with the appropriate values:


| Parameter | Description |
| --- | --- |
| region | The Google region where you want to deploy the BIG-IP VE, for example, **us-west1** |
| availabilityZone1 | The availability zone where you want to deploy the BIG-IP VE instance, such as **us-west1-a** |
| mgmtNetwork | The network you want to use for management traffic |
| network1 | The network name you want to use for BIG-IP external application traffic. |
| network2 | The network name you wan tto use for BIG-IP internal application traffic. |
| mgmtSubnet | The name of your subnet for management. |
| licenseKey1 | BYOL only: Your F5 BIG-IP BYOL license key |
| imageName | The F5 image name (such as f5-byol-bigip-13-0-0-2-3-1671-best) that is accessible by the Project launching the deployment template. | 
| instanceType | The BIG-IP instance type you want to use, such as **n1-standard-2** |
| subnet1 | The name of your subnet for network1. |
| subnet2 | The name of your subnet for network2. |
| manGuiPort | The BIG-IP VE management port.  The default is 443. |



### Save the YAML file
After you have edited the YAML file with the appropriate values, save the YAML file in a location accessible from the gcloud command line.

### Deploy the BIG-IP VE
The final task is to deploy the BIG-IP VE by running the following command from the **gcloud** command line:

```gcloud deployment-manager deployments create <your-deployment-name> --config <your-file-name.yaml>```

Keep in mind the following:  
+ *your-deployment-name*<br>This name must be unique.<br> 
+ *your-file-name.yaml*<br>  If your file is not in the same directory as the Google SDK, include the full file path in the command.


<br>
## Service Discovery
This Google GDM template supports Service Discovery.  If you enable it in the YAML file, the template runs the Service Discovery iApp template on the BIG-IP VE. Once you have properly tagged the servers you want to include, and then entered the corresponding tags (**tagName** and **tagValue**) and Google service account in the YAML file, the BIG-IP VE programmatically discovers (or removes) members using those tags. See our [Service Discovery video](https://www.youtube.com/watch?v=ig_pQ_tqvsI) to see this feature in action.

**Important**: Even if you don't plan on using the Service Discovery iApp initially, if you think you may want to use it in the future, you must specify the Google service account (**serviceAccount**) in the YAML file before deploying the template. At a minimum, the service account requires "Compute Viewer" or "Compute Engine - Read Only" permissions and should be specified using FQDN account name.

### Tagging
In Google, you tag objects using the **labels** parameter within the virtual machine.  The Service Discovery iApp uses these tags to discover nodes with this tag. Note that you select public or private IP addresses within the iApp.
  - *Tag a VM resource*<br>
The BIG-IP VE will discover the primary public or private IP addresses for the primary NIC configured for the tagged VM.


**Important**: Make sure the tags and IP addresses you use are unique. You should not tag multiple GDM nodes with the same key/tag combination if those nodes use the same IP address.


When enabled, the template runs the iApp template automatically.  If you need to modify the template after this initial configuration has taken place, use the following guidance.
  1.	From the BIG-IP VE web-based Configuration utility, on the Main tab, click **iApps > Application Services**.
  2.	From the list of application services, click **serviceDiscovery**.
  4.	You can now modify the template settings as applicable.  For assistance, from the *Do you want to see inline help?* question, select **Yes, show inline help**.
  5.	When you are done, click the **Finished** button.
  
If you want to verify the integrity of the template, from the BIG-IP VE Configuration utility click **iApps > Templates**. In the template list, look for **f5.service_discovery**. In the Verification column, you should see **F5 Verified**.



## Security Details <a name="securitydetail"></a>
This section has the entire code snippets for each of the lines you should ensure are present in your template file if you want to verify the integrity of the helper code in the template.

**/config/verifyHash section**

Note the hashes and script-signature may be different in your template. The important thing to check is that there is a script-signature line present in the location.<br>


```json
"/config/verifyHash": {
                "content": {
                  "Fn::Join": [
                    "\n",
                    [
                      "cli script /Common/verifyHash {",
                      "proc script::run {} {",
                      "    set file_path  [lindex $tmsh::argv 1]",
                      "    set expected_hash 73d01a6b4f27032fd31ea7eba55487430ed858feaabd949d4138094c26ce5521b4578c8fc0b20a87edc8cb0d9f28b32b803974ea52b10038f068e6a72fdb2bbd",
                      "    set computed_hash [lindex [exec /usr/bin/openssl dgst -r -sha512 $file_path] 0]",
                      "    if { $expected_hash eq $computed_hash } {",
                      "        exit 0",
                      "    }",
                      "    exit 1",
                      "}",
                      "    script-signature OGvFJVFxyBm/YlpBsOf8/AIyo5+p7luzrE11v8t7wJ1u24MBeit5pL/McqLxjydPJplymTcJ0qDEtXPZv09TTUF5hrF0g1pJ+z70omzJ6J9kOfOO8lyWP4XU/qM+ywEgAGoc8o8kGjKX01XcmB1e3rq6Mj5gE7CEkxKEcNzF3n5nDIFyBbpG6pJ8kg/7f6gtU14bJo0+ipNAiX+gBmT/10aUKKeJESU5wz+QqnEOE1WuTzdURArxditpk0+qqROZaSULD61w72hEy7kBC/miO+As7q8wjM5/H2yUHLoFLmBWP0jMWqIuzqnG+tgAFjJbZ1UJJDzWiYZK1TG1MsxfPg==",
                      "}"
                    ]
                  ]
                },
                "mode": "000755",
                "owner": "root",
                "group": "root"
              }
```
<br><br>
**/config/installCloudLibs.sh section**


```json
"/config/installCloudLibs.sh": {
                "content": {
                  "Fn::Join": [
                    "\n",
                    [
                      "#!/bin/bash",
                      "echo about to execute",
                      "checks=0",
                      "while [ $checks -lt 120 ]; do echo checking mcpd",
                      "    tmsh -a show sys mcp-state field-fmt | grep -q running",
                      "    if [ $? == 0 ]; then",
                      "        echo mcpd ready",
                      "        break",
                      "    fi",
                      "    echo mcpd not ready yet",
                      "    let checks=checks+1",
                      "    sleep 10",
                      "done",
                      "echo loading verifyHash script",
                      "tmsh load sys config merge file /config/verifyHash",
                      "if [ $? != 0 ]; then",
                      "    echo cannot validate signature of /config/verifyHash",
                      "    exit",
                      "fi",
                      "echo loaded verifyHash",
                      "echo verifying f5-cloud-libs.targ.gz",
                      "tmsh run cli script verifyHash /config/cloud/f5-cloud-libs.tar.gz",
                      "if [ $? != 0 ]; then",
                      "    echo f5-cloud-libs.tar.gz is not valid",
                      "    exit",
                      "fi",
                      "echo verified f5-cloud-libs.tar.gz",
                      "echo expanding f5-cloud-libs.tar.gz",
                      "tar xvfz /config/cloud/f5-aws-autoscale-cluster.tar.gz -C /config/cloud",
                      "tar xvfz /config/cloud/asm-policy-linux.tar.gz -C /config/cloud",
                      "tar xvfz /config/cloud/f5-cloud-libs.tar.gz -C /config/cloud/aws/node_modules",
                      "cd /config/cloud/aws/node_modules/f5-cloud-libs",
                      "echo installing dependencies",
                      "npm install --production /config/cloud/f5-cloud-libs-aws.tar.gz",
                      "touch /config/cloud/cloudLibsReady"
                    ]
                  ]
                },
                "mode": "000755",
                "owner": "root",
                "group": "root"
              }
```




## Filing Issues
If you find an issue, we would love to hear about it. 
You have a choice when it comes to filing issues:
  - Use the **Issues** link on the GitHub menu bar in this repository for items such as enhancement or feature requests and non-urgent bug fixes. Tell us as much as you can about what you found and how you found it.
  - Contact us at [solutionsfeedback@f5.com](mailto:solutionsfeedback@f5.com?subject=GitHub%20Feedback) for general feedback or enhancement requests. 
  - Use our [Slack channel](https://f5cloudsolutions.herokuapp.com) for discussion and assistance on F5 cloud templates. There are F5 employees who are members of this community who typically monitor the channel Monday-Friday 9-5 PST and will offer best-effort assistance.
  - For templates in the **supported** directory, contact F5 Technical support via your typical method for more time sensitive changes and other issues requiring immediate support.



## Copyright

Copyright 2014-2018 F5 Networks Inc.


## License


### Apache V2.0

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this file except in compliance with the License. You may obtain a copy of the
License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and limitations
under the License.

### Contributor License Agreement

Individuals or business entities who contribute to this project must have
completed and submitted the F5 Contributor License Agreement.
