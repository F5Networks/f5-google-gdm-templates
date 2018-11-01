# Deploying the BIG-IP VE in Google - Auto Scale BIG-IP WAF (LTM + ASM) - Frontend via Layer 4 LB (TCP)

[![Slack Status](https://f5cloudsolutions.herokuapp.com/badge.svg)](https://f5cloudsolutions.herokuapp.com)
[![Releases](https://img.shields.io/github/release/f5networks/f5-google-gdm-templates.svg)](https://github.com/f5networks/f5-google-gdm-templates/releases)
[![Issues](https://img.shields.io/github/issues/f5networks/f5-google-gdm-templates.svg)](https://github.com/f5networks/f5-google-gdm-templates/issues)

## Contents

- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Important Configuration Notes](#important-configuration-notes)
- [Security](#security)
- [Getting Help](#help)
- [Installation](#installation)
- [Configuration Example](#configuration-example)
- [Service Discovery](#service-discovery)

## Introduction

This solution uses a GDM template to launch the deployment of F5 BIG-IP Local Traffic Manager (LTM) and Application Security Manager (ASM) Virtual Edition (VE) instances in a Google Instance Group that is configured for auto scaling. Traffic flows from the Google load balancer to the BIG-IP VE (cluster) and then to the application servers. The BIG-IP VE(s) are configured in single-NIC mode. Auto scaling means that as certain thresholds are reached, the number of BIG-IP VE instances automatically increases or decreases accordingly. Scaling events are triggered based on the utilization of the BIG-IP VE CPU (you configure the thresholds in the template), specifically the F5 TMM (Traffic Management Microkernel) CPU.

In this solution, the BIG-IP VEs have the [LTM](https://f5.com/products/big-ip/local-traffic-manager-ltm) and [ASM](https://f5.com/products/big-ip/application-security-manager-asm) modules enabled to provide advanced traffic management and web application security functionality.


**Networking Stack Type:** This template deploys into an existing networking stack; so the networking infrastructure MUST be available prior to deploying. See the [Template Parameters Section](#template-parameters) for required networking objects.

## Prerequisites
The following are prerequisites for the F5 auto scale single NIC GDM template:

- You must have installed the [Google Cloud SDK](https://cloud.google.com/sdk/downloads)
- A Google Cloud Platform (GCP) network with one subnet.  The subnet requires a route and access to the Internet for the initial configuration to download the BIG-IP cloud library.
- Key pair for SSH access to BIG-IP VE (you can create or import this in Google Cloud)
- This solution uses the SSH key to enable access to the BIG-IP system. If you want access to the BIG-IP web-based Configuration utility, you must first SSH into the BIG-IP VE using the SSH key you provided in the template.  You can then create a user account with admin-level permissions on the BIG-IP VE to allow access if necessary.
- You must use a BIG-IP instance that has at least 2 vCPU and 4 GB memory. For each additional vCPU, add at least 2 GB of memory. Note: Because of this requirement, the *n1-highcpu* instance types are not supported. 
- **Important**: This solution uses calls to the GCE REST API to read and update GCE resources such as storage accounts, network interfaces, and route tables.  For the solution to function correctly, you must ensure that the BIG-IP(s) can connect to the GCE REST API on port 443.
- This solution uses calls to the GCE REST API to read and update GCE resources, this has specifically been tested in GCE Commercial Cloud. 

## Important configuration notes

- F5 GDM templates do not reconfigure existing GCE resources, such as network security groups.  Depending on your configuration, you may need to configure these resources to allow the BIG-IP VE(s) to receive traffic for your application.
- This template supports service discovery.  See the [Service Discovery section](#service-discovery) for details.
- This template can send non-identifiable statistical information to F5 Networks to help us improve our templates.  See [Sending statistical information to F5](#sending-statistical-information-to-f5).
- F5 has created a matrix that contains all of the tagged releases of the F5 GDM templates for GCE and the corresponding BIG-IP versions, license types and throughput levels available for a specific tagged release. See [google-bigip-version-matrix](https://github.com/F5Networks/f5-google-gdm-templates/blob/master/google-bigip-version-matrix.md).
- F5 GDM templates now capture all deployment logs to the BIG-IP VE in **/var/log/cloud/google**.  Depending on which template you are using, this includes deployment logs (stdout/stderr), f5-cloud-libs execution logs, recurring solution logs (failover, metrics, and so on), and more.
- This template includes a master election feature, which ensures that if the existing master BIG-IP VE is unavailable, a new master is selected from the BIG-IP VEs in the cluster.
- After deploying the template, we recommend going to [this section](#backup-big-ip-configuration-for-cluster-recovery) to create and store a backup of your BIG-IP configuration.
- Important: After the template successfully deploys, you must log into one of the BIG-IP VEs to modify the Application Security Synchronization settings.  Log in to the BIG-IP VE, and then click **Security > Options > Synchronization > Application Security Synchronization**.  From the **Device Group** list, select **Sync**, and then click **Save**. This ensures any changes to the ASM security policy are synchronized to other devices in the cluster.
- For important information on choosing a metric on which to base autoscaling events and the thresholds used by the template, see [Scaling Thresholds](#scaling-thresholds).

## Security

This GDM template downloads helper code to configure the BIG-IP system. If you want to verify the integrity of the template, you can open the template and ensure the following lines are present. See [Security Detail](#security-details) for the exact code.
In the *variables* section:

- In the *verifyHash* variable: **script-signature** and then a hashed signature.
- In the *installCloudLibs* variable: **tmsh load sys config merge file /config/verifyHash**.
- In the *installCloudLibs* variable: ensure this includes **tmsh run cli script verifyHash /config/cloud/f5-cloud-libs.tar.gz**.

Additionally, F5 provides checksums for all of our supported templates. For instructions and the checksums to compare against, see [checksums-for-f5-supported-cft-and-gdm-templates-on-github](https://devcentral.f5.com/codeshare/checksums-for-f5-supported-google-cloud-gdm-templates-on-github-1091).

## Supported BIG-IP versions

The following is a map that shows the available options for the template parameter **bigIpVersion** as it corresponds to the BIG-IP version itself. Only the latest version of BIG-IP VE is posted in the GCE Marketplace. For older versions, see downloads.f5.com.

| Google BIG-IP Image Version | BIG-IP Version |
| --- | --- |
| 13.1.10000 | 13.1.1 Build 0.0.4 |


## Help
While this template has been created by F5 Networks, it is in the **experimental** directory and therefore has not completed full testing and is subject to change.  F5 Networks does not offer technical support for templates in the experimental directory. For supported templates, see the templates in the **supported** directory.

### Community Help

We encourage you to use our [Slack channel](https://f5cloudsolutions.herokuapp.com) for discussion and assistance on F5 GDM templates. There are F5 employees who are members of this community who typically monitor the channel Monday-Friday 9-5 PST and will offer best-effort assistance. This slack channel community support should **not** be considered a substitute for F5 Technical Support for supported templates. See the [Slack Channel Statement](https://github.com/F5Networks/f5-google-gdm-templates/blob/master/slack-channel-statement.md) for guidelines on using this channel.

## Installation

This solution uses a YAML file for containing the parameters necessary to deploy the BIG-IP instance in Google Cloud.  The YAML file you use will be PAYG:  

- PAYG: [**f5-payg-autoscale-bigip-waf.yaml**](https://github.com/F5Networks/f5-google-gdm-templates/blob/master/experimental/autoscale/waf/via-lb/existing-stack/payg/f5-payg-autoscale-bigip-waf.yaml)

You ***must edit the YAML file*** to include information for your deployment before using the file to launch the BIG-IP VE instance.

1. Make sure you have completed all of the [prerequisites](#prerequisites).
2. [Edit the parameters](#edit-the-yaml-file) in the **f5-payg-autoscale-bigip-waf.yaml** YAML file in this repository as described in this section.
3. [Save the YAML and Python files](#save-the-yaml-and-python-files).
4. [Deploy the Solution](#Deploy-the-Solution) from the command line.

### Edit the YAML file

After completing the prerequisites, edit the YAML file.  You must replace the following parameters with the appropriate values. For more information about the Service Discovery fields, see [Service Discovery section](#service-discovery).

| Parameter | Required | Description |
| --- | --- | --- |
| region | Yes | The Google region in which you want to deploy BIG-IP, for example **us-west1** |
| availabilityZone1 | Yes | The availability zone where you want to deploy the BIG-IP VE instance, for example **us-west1-a** |
| mgmtNetwork | Yes | Name of the network you want to use for management traffic |
| mgmtSubnet | Yes | Name of the subnet you want to use for management traffic |
| imageName | Yes | BIG-IP image you want to deploy |
| instanceType | Yes | The BIG-IP instance type you want to use, such as **n1-standard-4** |
| manGuiPort | Yes | BIG-IP management port.  The default is **8443** |
| serviceAccount | Yes | If using service discovery, enter the Google service account to use for discovery. Leave single quotes with nothing between when not using service discovery |
| tagName | No | If using service discovery, enter the tag name used on servers for discovery. Leave single quotes with nothing between if not using service discovery |
| tagValue | No | If using service discovery, enter the tag value used on servers for discovery. Leave single quotes with nothing between if not using service discovery |
| targetSize | Yes | The number of instances you want to start with |
| minReplicas | Yes | The minimum number of BIG-IP instances the autoscale policy scales down to |
| maxReplicas | Yes | The maximum number of BIG-IP instances the autoscale policy allows |
| cpuUtilization | Yes | Target percent of BIG-IP managed instance group utilization. A new instance is created once this target is met for the entire group. |
| coolDownPeriod | Yes | How long to wait before collecting information from a new instance. This should be at least the time it takes to initialize the instance. In most cases, default value of 10 minutes (600 seconds) should be used. |
| policyLevel | Yes | The WAF (ASM) blocking level you want to use. Options are high, medium, low.  See the ASM documentation for a description of these levels. |
| applicationPort | Yes | The port for your application |
| applicationDnsName | Yes | The DNS name for your application. |
| allowUsageAnalytics | No | This deployment can send anonymous statistics to F5 to help us determine how to improve our solutions. If you select **No** statistics are not sent. |


### Save the YAML and Python files

After you have edited the YAML file with the appropriate values, save the YAML file in a location accessible from the gcloud command line.  Save the [python file](https://github.com/F5Networks/f5-google-gdm-templates/blob/master/experimental/autoscale/waf/via-lb/existing-stack/payg/f5-payg-autoscale-bigip-waf.py) in the same location.

### Deploy the Solution

The final task is to deploy the solution by running the following command from the **gcloud** command line:

```gcloud deployment-manager deployments create <your-deployment-name> --config <your-file-name.yaml>```

Keep in mind the following:  

- *your-deployment-name*<br>This name must be unique.<br>
- *your-file-name.yaml*<br>  If your file is not in the same directory as the Google SDK, include the full file path in the command.

### Backup BIG-IP configuration for cluster recovery

The template now automatically saves a BIG-IP back up UCS file (into the **backup** container of the storage account ending in **data000**) every night at 12am, and saves 7 days of back up UCS files.  If you make manual changes to the configuration, we recommend immediately making a backup of your BIG-IP configuration manually and storing the resulting UCS file in the backup container to ensure the master election process functions properly.  Note: If it is necessary to recover from this UCS backup, the system picks the backup file with the latest timestamp.

To manually save the BIG-IP configuration to a UCS file:

1. Backup your BIG-IP configuration (ideally the cluster primary) by creating a [UCS](https://support.f5.com/csp/article/K13132) archive.  Use the following syntax to save the backup UCS file:
    - From the CLI command: ```# tmsh save /sys ucs /var/tmp/original.ucs```
    - From the Configuration utility: **System > Archives > Create**
2. Upload the UCS into the **backup** container of the storage account ending in **data000**.

## Service Discovery

This Google GDM template supports Service Discovery.  If you enable it in the YAML file, the template runs the Service Discovery iApp template on the BIG-IP VE. Once you have properly tagged the servers you want to include, and then entered the corresponding tags (**tagName** and **tagValue**) and Google service account in the YAML file, the BIG-IP VE programmatically discovers (or removes) members using those tags. See our [Service Discovery video](https://www.youtube.com/watch?v=ig_pQ_tqvsI) to see this feature in action.

**Important**: Even if you don't plan on using the Service Discovery iApp initially, if you think you may want to use it in the future, you must specify the Google service account (**serviceAccount**) in the YAML file before deploying the template.

### Tagging

In Google, you tag objects using the **labels** parameter within the virtual machine.  The Service Discovery iApp uses these tags to discover nodes with this tag. Note that you select public or private IP addresses within the iApp.

- *Tag a VM resource*

The BIG-IP VE will discover the primary public or private IP addresses for the primary NIC configured for the tagged VM.


**Important**: Make sure the tags and IP addresses you use are unique. You should not tag multiple GDM nodes with the same key/tag combination if those nodes use the same IP address.


When enabled, the template runs the iApp template automatically.  If you need to modify the template after this initial configuration has taken place, use the following guidance.

1. From the BIG-IP VE web-based Configuration utility, on the Main tab, click **iApps > Application Services**.
2. From the list of application services, click **serviceDiscovery**.
3. You can now modify the template settings as applicable.  For assistance, from the *Do you want to see inline help?* question, select **Yes, show inline help**.
4. When you are done, click the **Finished** button.

If you want to verify the integrity of the template, from the BIG-IP VE Configuration utility click **iApps > Templates**. In the template list, look for **f5.service_discovery**. In the Verification column, you should see **F5 Verified**.


## Filing Issues

If you find an issue, we would love to hear about it.
You have a choice when it comes to filing issues:

- Use the **Issues** link on the GitHub menu bar in this repository for items such as enhancement or feature requests and non-urgent bug fixes. Tell us as much as you can about what you found and how you found it.
- Contact us at [solutionsfeedback@f5.com](mailto:solutionsfeedback@f5.com?subject=GitHub%20Feedback) for general feedback or enhancement requests.
- Use our [Slack channel](https://f5cloudsolutions.herokuapp.com) for discussion and assistance on F5 cloud templates.  There are F5 employees who are members of this community who typically monitor the channel Monday-Friday 9-5 PST and will offer best-effort assistance.
- For templates in the **supported** directory, contact F5 Technical support via your typical method for more time sensitive changes and other issues requiring immediate support.

## Copyright

Copyright 2014-2018 F5 Networks Inc.

## License

### Apache V2.0

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this file except in compliance with the License. You may obtain a copy of the
License [here](http://www.apache.org/licenses/LICENSE-2.0).

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and limitations
under the License.

### Contributor License Agreement

Individuals or business entities who contribute to this project must have
completed and submitted the F5 Contributor License Agreement.