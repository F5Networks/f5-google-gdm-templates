# Deploying the BIG-IP in Google Cloud - Single NIC - Learning Stack

[![Slack Status](https://f5cloudsolutions.herokuapp.com/badge.svg)](https://f5cloudsolutions.herokuapp.com)
[![Releases](https://img.shields.io/github/release/f5networks/f5-google-gdm-templates.svg)](https://github.com/f5networks/f5-google-gdm-templates/releases)
[![Issues](https://img.shields.io/github/issues/f5networks/f5-google-gdm-templates.svg)](https://github.com/f5networks/f5-google-gdm-templates/issues)

## Contents

- [Introduction](#introduction)
- [Prerequisites](#prerequisites-and-notes)
- [Security](#security)
- [Deploying the Template](#deploying-the-template)
- [Configuration Example](#config)

## Introduction

This solution uses a Google Deployment Manager Template to launch a single NIC deployment a BIG-IP VE in an Google Virtual Private Cloud. Traffic flows from the BIG-IP VE to the application servers.  This is the standard Cloud design where the compute instance of
F5 is running with a single interface, which processes both management and data plane traffic.  This is a traditional model in the cloud where the deployment is considered one-armed.  

The BIG-IP VE has the [Local Traffic Manager](https://f5.com/products/big-ip/local-traffic-manager-ltm) (LTM) module enabled to provide advanced traffic management functionality. This means you can also configure the BIG-IP VE to enable F5's L4/L7 security features, access control, and intelligent traffic management.

This template deploys as a **learning stack** Google Deployment Manager template incorporated into an existing network. That means it creates and configures the BIG-IP, the Google Cloud infrastructure, as well as a backend webserver.

## Prerequisites and notes

The following are prerequisites and configuration notes for the F5 single NIC GDM template:

- You must have installed the [Google Cloud SDK](https://cloud.google.com/sdk/downloads)
- BYOL licensing only: An F5 Networks BYOL license (Bring Your Own License) available
- A Google Cloud Platform (GCP) network with one subnet.  The subnet requires a route and access to the Internet for the initial configuration to download the BIG-IP cloud library.
- Key pair for SSH access to BIG-IP VE (you can create or import this in Google Cloud)
- An Google Firewall rule with the following inbound rules:
  - Port 22 for SSH access to the BIG-IP VE
  - Port 8443 (or other port) for accessing the BIG-IP web-based Configuration utility
  - A port for accessing your applications via the BIG-IP virtual server
- This solution uses the SSH key to enable access to the BIG-IP system. If you want access to the BIG-IP web-based Configuration utility, you must first SSH into the BIG-IP VE using the SSH key you provided in the template.  You can then create a user account with admin-level permissions on the BIG-IP VE to allow access if necessary.
- You must use a BIG-IP instance that has at least 2 vCPU and 4 GB memory. For each additional vCPU, add at least 2 GB of memory. Note: Because of this requirement, the *n1-highcpu* instance types are not supported.  The following are the minimum and default Google Cloud Instance sizes:
  - Good: minimum – **n1-standard-1**; default – **n1-standard-2**
  - Better: minimum – **n1-standard-2**;  default – **n1-standard-4**
  - Best: minimum – **n1-standard-2**;  default – **n1-standard-4**

### Security

This GDM template downloads helper code to configure the BIG-IP system. If you want to verify the integrity of the template, you can open the GDM template and ensure the following lines are present. See [Security Detail](#securitydetail) for the exact code in each of the following sections.

- In the */config/verifyHash* section: **script-signature** and then a hashed signature
- In the */config/installCloudLibs.sh* section **"tmsh load sys config merge file /config/verifyHash"**
  
  Additionally, F5 provides checksums for all of our supported Google Deployment Manager templates. For instructions and the checksums to compare against, see this [link](https://devcentral.f5.com/codeshare/checksums-for-f5-supported-cft-and-arm-templates-on-github-1014).
  
### Help

**F5 Support**  
While this template has been created by F5 Networks, it is in the experimental directory and therefore has not completed full testing and is subject to change.  F5 Networks does not offer technical support for templates in the experimental directory. For supported templates, see the templates in the **supported** directory.

**Community Support**  
We encourage you to use our [Slack channel](https://f5cloudsolutions.herokuapp.com) for discussion and assistance on F5 Google GDM templates. There are F5 employees who are members of this community who typically monitor the channel Monday-Friday 9-5 PST and will offer best-effort assistance. This slack channel community support should **not** be considered a substitute for F5 Technical Support. See the [Slack Channel Statement](https://github.com/F5Networks/f5-google-gdm-templates/blob/master/slack-channel-statement.md) for guidelines on using this channel.

## Deploying the template

This solution uses a YAML file for containing the parameters necessary to deploy the BIG-IP instance in Google Cloud.  The YAML file you use will be BYOL:  

- BYOL: [**f5-learning-stack-byol-1nic-bigip.yaml**](https://github.com/F5Networks/f5-google-gdm-templates/blob/master/experimental/standalone/1nic/learning-stack/byol/f5-learning-stack-byol-1nic-bigip.yaml)

You ***must edit the YAML file*** to include information for your deployment before using the file to launch the BIG-IP VE instance.

1. Make sure you have completed all of the [prerequisites](#prerequisites).
2. [Edit the parameters](#edit-the-yaml-file) in the **f5-learning-stack-byol-1nic-bigip.yaml** YAML file in this repository as described in this section.
3. [Save the YAML file](#save-the-yaml-file).
4. [Deploy the BIG-IP VE](#deploy-the-big-ip-ve) from the command line.

### Edit the YAML file

After completing the prerequisites, edit the YAML file.  You must replace the following parameters with the appropriate values:

| Parameter | Description |
| --- | --- |
| region | Google Region to deploy BIG-IP, such as **us-west1** |
| availabilityZone1 | The availability zone where you want to deploy the BIG-IP VE instance, such as **us-west1-a** |
| network | Network name in which you want to deploy BIG-IP  |
| licenseKey1 | BYOL only: Your F5 BIG-IP BYOL license key |
| imageName | BIG-IP image you want to deploy |
| instanceType | The BIG-IP instance type you want to use, such as **n1-standard-2** |
| manGuiPort | BIG-IP management port.  The default is **8443** |
| subnet1 | The name of your subnet |
| allowUsageAnalytics | This deployment can send anonymous statistics to F5 to help us determine how to improve our solutions. If you select **No** statistics are not sent. |

### Save the YAML file

After you have edited the YAML file with the appropriate values, save the YAML file in a location accessible from the gcloud command line.

### Deploy the BIG-IP VE

The final task is to deploy the BIG-IP VE by running the following command from the **gcloud** command line:

```gcloud deployment-manager deployments create <your-deployment-name> --config <your-file-name.yaml>```

Keep in mind the following:
- *your-deployment-name*<br>This name must be unique.<br>
- *your-file-name.yaml*<br>  If your file is not in the same directory as the Google SDK, include the full file path in the command.


## Configuration Example <a name="config"></a>

The following is a simple configuration diagram for this single NIC deployment. In this scenario, all access to the BIG-IP VE appliance is through the same IP address and virtual network interface (vNIC).  This interface processes both management and data plane traffic.

![Single NIC configuration example](../images/google_setup.png)

### Documentation

The ***BIG-IP Virtual Edition and Google Cloud Platform: Setup*** [guide](https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-ve-setup-google-cloud-platform-13-0-0.html) details how to create the configuration manually without using the template.  This document also describes the configuration in more detail.

## Security Details <a name="securitydetail"></a>

This section has the entire code snippets for each of the lines you should ensure are present in your template file if you want to verify the integrity of the helper code in the template.

### /config/verifyHash section

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

### /config/installCloudLibs.sh section


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
