[![Slack Status](https://f5cloudsolutions.herokuapp.com/badge.svg)](https://f5cloudsolutions.herokuapp.com)
[![Releases](https://img.shields.io/github/release/f5networks/f5-google-gdm-templates.svg)](https://github.com/f5networks/f5-google-gdm-templates/releases)
[![Issues](https://img.shields.io/github/issues/f5networks/f5-google-gdm-templates.svg)](https://github.com/f5networks/f5-google-gdm-templates/issues)
## BIG-IP Version Matrix for Google Deployment Manager Templates
The following table contains all of the tagged releases of the F5 Google Deployment Manager (GDM) templates, and the corresponding BIG-IP versions, license types and throughput levels available for a specific tagged release.  To view a Tag, from the f5-google-gdm-templates repo (https://github.com/F5Networks/f5-google-gdm-templates or a sub directory), click the Branch < current branch > button, and then click the *Tags* tab.  You see a list of all of the F5 tagged releases.

| Release Tag | Template Family | BIG-IP Versions | PAYG License Bundles and Throughput | BYOL Image options (v13.1.1 and later) |
| --- | --- | --- | --- | --- |
| [v3.0.2](https://github.com/F5Networks/f5-google-gdm-templates/releases/tag/v3.0.1) | Standalone | BIG-IP v14.2.0 | Good/Better/Best: 5Gbps, 1Gbps, 200Mbps, 25Mbps | AllTwoBootLocations, LTMTwoBootLocations |
| [v3.0.1](https://github.com/F5Networks/f5-google-gdm-templates/releases/tag/v3.0.1) | Standalone | BIG-IP v14.1.0 | Good/Better/Best: 5Gbps, 1Gbps, 200Mbps, 25Mbps | AllTwoBootLocations, LTMTwoBootLocations |
| [v3.0.0](https://github.com/F5Networks/f5-google-gdm-templates/releases/tag/v3.0.0) | Standalone | BIG-IP v14.1.0 | Good/Better/Best: 5Gbps, 1Gbps, 200Mbps, 25Mbps | AllTwoBootLocations, LTMTwoBootLocations |
| [v2.2.0](https://github.com/F5Networks/f5-google-gdm-templates/releases/tag/v2.2.0) | Standalone | BIG-IP v13.1.1 | Good/Better/Best: 5Gbps, 1Gbps, 200Mbps, 25Mbps | AllTwoBootLocations, LTMTwoBootLocations |
| [v2.1.3](https://github.com/F5Networks/f5-google-gdm-templates/releases/tag/v2.1.3) | Standalone | BIG-IP v13.1.1 | Good/Better/Best: 5Gbps, 1Gbps, 200Mbps, 25Mbps | AllTwoBootLocations, LTMTwoBootLocations |
| [v2.1.2](https://github.com/F5Networks/f5-google-gdm-templates/releases/tag/v2.1.2) | Standalone | BIG-IP v13.1.1 | Good/Better/Best: 5Gbps, 1Gbps, 200Mbps, 25Mbps | AllTwoBootLocations, LTMTwoBootLocations |
| [v2.1.1](https://github.com/F5Networks/f5-google-gdm-templates/releases/tag/v2.1.1) | Standalone | BIG-IP v13.1.1 | Good/Better/Best: 5Gbps, 1Gbps, 200Mbps, 25Mbps | AllTwoBootLocations, LTMTwoBootLocations |
| [v2.1.0](https://github.com/F5Networks/f5-google-gdm-templates/releases/tag/v2.1.0) | Standalone | BIG-IP v13.1.1 | Good/Better/Best: 5Gbps, 1Gbps, 200Mbps, 25Mbps | AllTwoBootLocations, LTMTwoBootLocations |
| [v2.0.0](https://github.com/F5Networks/f5-google-gdm-templates/releases/tag/v2.0.0) | Standalone | BIG-IP v13.1.1 | Good/Better/Best: 5Gbps, 1Gbps, 200Mbps, 25Mbps | AllTwoBootLocations, LTMTwoBootLocations |
| [v1.5.1](https://github.com/F5Networks/f5-google-gdm-templates/releases/tag/v1.5.1) | Standalone | BIG-IP v13.1.1 | Good/Better/Best: 5Gbps, 1Gbps, 200Mbps, 25Mbps | AllTwoBootLocations, LTMTwoBootLocations |
| [v1.5.0](https://github.com/F5Networks/f5-google-gdm-templates/releases/tag/v1.5.0) | Standalone | BIG-IP v13.1.1 | Good/Better/Best: 5Gbps, 1Gbps, 200Mbps, 25Mbps | AllTwoBootLocations, LTMTwoBootLocations |
| [v1.4.0](https://github.com/F5Networks/f5-google-gdm-templates/releases/tag/v1.4.0) | Standalone | BIG-IP v13.1.0.2 | Good/Better/Best: 5Gbps, 1Gbps, 200Mbps, 25Mbps | |
| [v1.3.1](https://github.com/F5Networks/f5-google-gdm-templates/releases/tag/v1.3.1) | Standalone | BIG-IP v13.1.0.2 | Good/Better/Best: 5Gbps, 1Gbps, 200Mbps, 25Mbps | |
| [v1.3.0](https://github.com/F5Networks/f5-google-gdm-templates/releases/tag/v1.3.0) | Standalone | BIG-IP v13.1.0.2 | Good/Better/Best: 5Gbps, 1Gbps, 200Mbps, 25Mbps | |
| [v1.2.0](https://github.com/F5Networks/f5-google-gdm-templates/releases/tag/v1.2.0) | Standalone | BIG-IP v13.0 | Good/Better/Best: 5Gbps, 1Gbps, 200Mbps, 25Mbps | |
| [v1.1.0](https://github.com/F5Networks/f5-google-gdm-templates/releases/tag/v1.1.0) | Standalone | BIG-IP v13.0 | Good/Better/Best: 5Gbps, 1Gbps, 200Mbps, 25Mbps | |
| [v1.0.0](https://github.com/F5Networks/f5-google-gdm-templates/releases/tag/v1.0.0) | Standalone | BIG-IP v13.0 | Good/Better/Best: 5Gbps, 1Gbps, 200Mbps, 25Mbps | |

If you would like to view all available images, run the following command from the **gcloud** command line: 

```$ gcloud compute images list --project f5-7626-networks-public | grep f5```

## Copyright

Copyright2014-2019 F5 Networks Inc.


## License

### Apache V2.0

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this file except in compliance with the License. You may obtain a copy of the
License at:

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and limitations
under the License.


### Contributor License Agreement

Individuals or business entities who contribute to this project must have
completed and submitted the `F5 Contributor License Agreement`
