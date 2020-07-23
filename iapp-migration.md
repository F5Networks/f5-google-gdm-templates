# F5 iApp Migration

All v1 iApp templates have been deprecated and removed from F5 Google Deployment templates. This guide provides mappings between the f5.service_discovery and f5.cloud_logger iApp templates and example declarations that can be used with F5 Application Services 3 Extension and F5 Telemetry Services Extension.

## Service Discovery iApp

```bash
tmsh list sys application service sd
```

```tcl
sys application service sd.app/sd {
    device-group none
    inherited-devicegroup true
    inherited-traffic-group true
    template f5.service_discovery
    traffic-group traffic-group-1
    variables {
        basic__advanced {
            value no
        }
        basic__display_help {
            value hide
        }
        cloud__cloud_provider {
            value gce
        }
        cloud__gce_bigip_in_gc {
            value yes
        }
        cloud__gce_region {
            value <region>
        }
        monitor__frequency {
            value <monitor_frequency>
        }
        monitor__http_method {
            value <http_method>
        }
        monitor__http_version {
            value <http_version>
        }
        monitor__monitor {
            value "/#create_new#"
        }
        monitor__response { 
            value <monitor_response>
        }
        monitor__type {
            value <monitor_type>
        }
        monitor__uri {
            value <monitor_uri>
        }
        pool__interval {
            value <discovery_interval>
        }
        pool__member_conn_limit {
            value <connection_limit>
        }
        pool__member_port {
            value <member_port>
        }
        pool__pool_to_use {
            value "/#create_new#"
        }
        pool__public_private {
            value <ip_type>
        }
        pool__tag_key {
            value <tag_key>
        }
        pool__tag_value {
            value <tag_value>
        }
    }
}
```

### Example AS3 declaration - Creates dynamically populated pool based on GCE resource tags
To send this declaration to AS3, use the POST method to the URI https://<BIG-IP>/mgmt/shared/appsvcs/declare and put the declaration in the body of the post. A Postman collection for AS3 can be found on the f5-appsvcs-extension [releases page.](https://github.com/F5Networks/f5-appsvcs-extension/releases/)

```json
{
    "webPool": {
        "class": "Pool",
        "members": [
            {
                "servicePort": <member_port>,
                "addressDiscovery": "gce",
                "updateInterval": <discovery_interval>,
                "tagKey": "<tag_key>",
                "tagValue": "<tag_value>",
                "addressRealm": "<ip_type>",
                "region": "<region>",
                "encodedCredentials": "<encodedCredentials>"
            }
        ],
        "monitors": [
            { "use": "httpMonitor" }
        ]
    },
    "httpMonitor": {
        "class": "Monitor",
        "label": "http monitor",
        "monitorType": "<monitor_type>",
        "send": "<http_method> <monitor_uri> <http_version>",
        "receive": "<monitor_response>",
        "interval": <monitor_frequency>,
        "connectionLimit": <connection_limit>
    }
}
```