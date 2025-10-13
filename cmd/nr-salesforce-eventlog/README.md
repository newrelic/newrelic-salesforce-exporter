# New Relic Salesforce Event Log Integration

## Introduction

The Event Log integration can collect the following types of data from Salesforce:

- [Event Logs](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile.htm)
- [Standard Objects](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_list.htm)
- [Tooling Objects](https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/reference_objects_list.htm)
- [API Limits](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_limits.htm)

## Build

Install [Go](https://go.dev/doc/install) first. The minimum required version is
`1.23.2`.

From the folder `cmd/nr-salesforce-eventlog/`, run:

```bash
go build nr-salesforce-eventlog.go
```

It will generate a binary `nr-salesforce-eventlog` in the same folder.

## Setup

The event log integration obtains the configuration from a YAML file. There is
a [sample config file](../../config_sample_eventlog.yml) you can use as a
template to create your own.

The following is a list of the required keys and a description for each.

### Version

The version key is mandatory and must contain the value `2.0`:

```yaml
version: "2.0"
```

### Event Log

The `eventLog` key contains the following structure:

```yaml
eventLog:
  integrationName: "MY INTEGRATION NAME"
  requestTimeout: 10
  instances:
    - name: "FIRST INSTANCE NAME HERE"
      apiVer: "64.0"
      requestTimeout: 10
      initialTimeInterval:
        # Initial time interval section, described later

      auth:
        # Auth section, described later
      cache:
        # Cache section, described later

      skipLogFiles: false
      eventTypes:
        # Event types section
      fieldMapping:
        # Field mapping section, described later
      fieldMappingFile: event_type_fields.yml

      customQueries:
        # Custom queries section, described later
      customQueryFiles:
        # Custom queries files section, described later

      limits:
        # Limits section, described later

    - name: # ... other instances
```

Any value within the `eventLog` section can be specified with an environment
variable. To do that, just set `$ENV_VAR_NAME` as the value. Example:

```yaml
eventLog:
  integrationName: $INTEGRATION
```

It will get the value of `integragtionName` from the environment variable named
`INTEGRATION`.

Each one of the config keys within `eventLog` are described in the following
sections.

#### - `integrationName`

| Valid Values | Required | Default |
| --- | --- | --- |
| Text | Yes | N/A |

It must contain a descriptive name for the integration. Something like
`com.newrelic.labs.sfdc.eventlog` is recommended.

#### - `requestTimeout`

| Valid Values | Required | Default |
| --- | --- | --- |
| Integer number | No | 5 |

Timeout in seconds for API requests sent to Salesforce.

#### - `instances`

| Valid Values | Required | Default |
| --- | --- | --- |
| List of instance structures | Yes | N/A |

Is a list of `instance` structures, each one contains the description of a single
Salesforce instance. It must contain at least one instance. Each instance contains
the following keys:

##### - `name`

| Valid Values | Required | Default |
| --- | --- | --- |
| Text | Yes | N/A |

A descriptive instance name. Names can't be repeated, each instance must have a
different name.

##### - `apiVer`

| Valid Values | Required | Default |
| --- | --- | --- |
| SFDC API version | No | 55.0 |

API version numbers used to access the Salesforce APIs.

> NOTE: API version is not checked. User is responsible for providing a valid
> [Salesforce API version](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/dome_versions.htm).

##### - `requestTimeout`

| Valid Values | Required | Default |
| --- | --- | --- |
| Integer number | No | Integration level timeout |

Timeout in seconds for API requests sent to Salesforce, for current instance. If
defined, it has precedence over the `requestTimeout` defined for the entire
integration.

##### - `initialTimeInterval`

| Valid Values | Required | Default |
| --- | --- | --- |
| Initial time interval structure | No | 1 hours, 0 minutes |

The initial time interval has the following structure:

```yaml
  initialTimeInterval:
    hours: 6
    minutes: 30
```

It defines the time interval for the first API request, since
`initialTimeInterval` ago until now. After the first request, this value is not
used anymore, because the following time intervals are calculated using the time
of the previous request (`last_run_ts`). This `last_run_ts` is stored in the
cache. If the cache is not present, then `initialTimeInterval` will be used for
every request, not only the first one.

##### - `auth`

| Valid Values | Required | Default |
| --- | --- | --- |
| Auth structure | Yes | N/A |

It describes the credentials to connect to the Salesforce API. It has the
following structure:

```yaml
  auth:
    tokenUrl: "<TOKEN URL HERE>"
    userPass:
      clientId: "<CLIENT ID HERE>"
      clientSecret: "<CLIENT SECRET HERE>"
      username: "<USER NAME HERE>"
      password: "<PASSWORD HERE>"
```

- `tokenUrl`: base url to access the Slaesforce API. Use to be something like
`https://my-company--staging.sandbox.my.salesforce.com`.
- `clientId`: Client ID for the OAuth User-Password flow.
- `clientSecret`: Client Secret for the OAuth User-Password flow.
- `username`: Username for the OAuth User-Password flow.
- `Password`: Password for the OAuth User-Password flow.

##### - `cache`

| Valid Values | Required | Default |
| --- | --- | --- |
| Cache structure | No | Empty |

Setting up the cache is optional but **strongly recommended**. The cache is used
for multiple purposes: de-duplicate logs, store authentication token, and 
calculate time ranges for API requests. Not setting up a cache will limit the
performance of this integration.

Currently we support Redis DB:

```yaml
  cache:
    redis:
      host: "<REDIS SERVER HOST HERE>"
      port: 6379
      dbNumber: 0
      password: "<PASSWORD HERE or empty if no password>"
      expireDays: 1
```

- `host`: Redis server address.
- `port`: Redis server port. Usually `6379`.
- `dbNumber`: Redis database number. Usually `0`.
- `password`: Redis password. Or `""` if no password.
- `expireDays`: Expiration time for keys in days. `0` means no expiration time.

##### - `skipLogFiles`

| Valid Values | Required | Default |
| --- | --- | --- |
| Boolean | No | false |

If `true`, it won't request event log files.

##### - `eventTypes`

| Valid Values | Required | Default |
| --- | --- | --- |
| List of event types | No | Empty |

It has the following structure:

```yaml
  eventTypes:
    - Login
    - URI
    - API
    # ... other event types
```

If present, the integration will request the listed [event types](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_supportedeventtypes.htm)
only. If not present or empty, it will request all event types.

##### - `fieldMapping`

| Valid Values | Required | Default |
| --- | --- | --- |
| Field mapping structure | No | Empty |

It has the following structure:

```yaml
  fieldMapping:
    # format: "event_type : list_of_attributes"
    Login: ["RUN_TIME", "LOGIN_TYPE", "API_TYPE"]
    URI: ["URI", "CLIENT_IP", "USER_ID"]
    # ... other mappings
```

Each entry is an event type and a list of attributes. It will filter the listed
attributes for each event type. Events use to have a lot of attributes, in case
not all attributes are required, we can filter and only get the events we need.

If not present, all attributes will be reported.

##### - `fieldMappingFile`

| Valid Values | Required | Default |
| --- | --- | --- |
| File path | No | Empty |

In addition to defining the list of field mappings in situ, we can define them
in an external file, like [this sample](../../event_type_fields.yml).

The file has the following format:

```yaml
  mapping:
    # format: "event_type : list_of_attributes"
    Login: ["RUN_TIME", "LOGIN_TYPE", "API_TYPE"]
    URI: ["URI", "CLIENT_IP", "USER_ID"]
    # ... other mappings
```

`fieldMapping` and `fieldMappingFile` are mutually exclusive, if both are
defined, `fieldMappingFile` takes precedence.

##### - `customQueries`

| Valid Values | Required | Default |
| --- | --- | --- |
| List of query structures | No | Empty |

It has the following structure:

```yaml
  customQueries:
    - soql:
      # ...
    - soql:
      # ...
    # ... other queries
```

It defines a list of custom SOQL queries to request using the SFDC query API.
Unlike EventLogFiles, these queries can request data from any of the
[standard objects](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_list.htm)
or the [tooling objects](https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/reference_objects_list.htm).
Each entry in the list has the following structure:

```yaml
  - soql:
      select: [Action, CreatedDate]
      from: "SetupAuditTrail"
      where: "Action = 'changedApexClass'"
    apiVer: "64.0"
    timestamp: CreatedDate
    apiName: rest
```

- `select`: List of attributes from the object. Required.
- `from`: Object type. Required.
- `where`: Conditions. Optional.
- `apiVer`: The API version to use for this request. If not present, it will use
the API version defined in the instance, or the integration. Optional.
- `timestamp`: Which attribute from the object represents the timestamp. Required.
- `apiName`: Which API we want to use, `rest` or `tooling`. Default `rest`. Optional.

##### - `customQueryFiles`

| Valid Values | Required | Default |
| --- | --- | --- |
| List of file paths | No | Empty |

If has the following structure:

```yaml
  customQueryFiles:
    - "/path/to/query_one.yml"
    - "/path/to/query_two.yml"
```

It defines custom queries, just like `customQueries`, but in external files.
Each file has the following structure:

```yaml
  queries:
    - soql:
      # ...
    - soql:
      # ...
    # ... other queries
```

Where each entry in `queries` is a query structure like the ones defined before,
in the `customQueries` section.

##### - `limits`

| Valid Values | Required | Default |
| --- | --- | --- |
| Limits structure | No | Empty |

It has the following structure:

```yaml
  limits:
    apiVer: "58.0"
    names:
      - ActiveScratchOrgs
      - DailyApiRequests
      # ...
```

- `apiVer`: API version to use for the Limits API request. If not present, it
will use the version defined for the instance or the integration. Optional.
- `names`: List of limit names to report. Optional.

The list of limits to report from the [Limits API](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_limits.htm).
If empty, all limits will be reported.

### New Relic credentials

After the `eventLog` config, we have the New Relic credentials, required to 
inject data.

```yaml
licenseKey: "<LICENSE KEY HERE>"
accountId: "<ACCOUNT ID HERE>"
region: "<REGION HERE>"
format: "<FORMAT HERE>"
```

#### - `licenseKey`

| Valid Values | Required | Default |
| --- | --- | --- |
| String | Yes | N/A |

A New Relic license key with permissions to inject data. It can
also be specified using the `NR_LICENSE_KEY` environment variable.


#### - `accountId`

| Valid Values | Required | Default |
| --- | --- | --- |
| Numeric string | Yes | N/A |

The account ID where the license key was created. It can also be
specified using the `NR_ACCOUNT_ID` environment variable.

#### - `region`

| Valid Values | Required | Default |
| --- | --- | --- |
| "US" or "EU" | No | US |

The region of your account ID: Either `US` or `EU`.

#### - `format`

| Valid Values | Required | Default |
| --- | --- | --- |
| "events" or "logs" | Yes | N/A |

The data format we want to inject to New Relic: Either `events` or
`logs`.

### Integration lifecycle

The last block of config keys contains settings for the integration lifecycles.

```yaml
runAsService: false 

pipeline:
  harvestInterval: 120

interval: 30
```

#### - `runAsService`

| Valid Values | Required | Default |
| --- | --- | --- |
| Boolean | No | false |

If `true` the integration will run continuously. If `false`, it will run one
cycle and finish. A single cycle is composed of:

  1. Downloading event log files
  1. Requesting custom queries
  1. Getting limits

For each one of the `instances` defined in the config file.

#### - `harvestInterval`

| Valid Values | Required | Default |
| --- | --- | --- |
| Number | No | 60 |

Data harvest interval in seconds. If `runAsService` is true, it defines the
periods in which the integration will send data to New Relic.

#### - `interval`

| Valid Values | Required | Default |
| --- | --- | --- |
| Number | No | 60 |

Integration execution interval. If `runAsService` is true, it defines the periods
in which the integration will run a cycle.