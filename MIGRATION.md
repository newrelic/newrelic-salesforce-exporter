# Migrating from `v2` (legacy) to `v3` (latest)

The New Relic Salesforce Exporter version 3 uses a different format for
configuration files, which is similar but incompatible with previous versions.
This guide explains the differences and how to adapt old config files. It
applies to the Event Log integration only, since the Event Stream is a brand
new integration, so there is nothing to migrate from.

## Example

First, let's see a simple example of a v2 config file and how it translates to
v3:

```yaml
#
# v2 (legacy) config
#

integration_name: com.newrelic.labs.sfdc.eventlogfiles

run_as_service: False
cron_interval_minutes: 120 # 2 hours

instances:
  - name: my-instance
    arguments:
      token_url: "https://my-org.salesforce.com/services/oauth2/token"
      auth:
        grant_type: "password"
        client_id: "MY-CLIENT-ID"
        client_secret: "MY-CLIENT-SECRET"
        username: "user@my-org"
        password: "MY-PASSWORD"
      cache_enabled: True
      redis:
        host: "cache-host"
        port: "6379"
        db_number: 0
        expire_days: 2
        ssl: False
        password: ""
      date_field: "LogDate"
      generation_interval: "Hourly"
      time_lag_minutes: 0
    labels:
      environment: staging

queries: [
  {
    query: "SELECT Id,Action,CreatedDate,DelegateUser,Display FROM SetupAuditTrail WHERE CreatedDate>={from_timestamp}",
    timestamp_attr: CreatedDate,
    api_ver: "58.0",
  }
]

newrelic:
  license_key: "MY-LICENSE-KEY"
  account_id: "1234"
  api_endpoint: "US"
  data_format: "events"
```

```yaml
#
# v3 (latest) config
#

version: "2.0"

runAsService: false

eventLog:
  instanceName: my-instance
  auth:
    tokenUrl: "https://my-org.salesforce.com"
    # WARNING: DO NOT USE THIS AUTH METHOD, CHECKOUT THE REPO README FOR MORE INFO.
    userPass:
      clientId: "MY-CLIENT-ID"
      clientSecret: "MY-CLIENT-SECRET"
      username: "user@my-org"
      password: "MY-PASSWORD"
  cache:
    redis:
      host: "cache-host"
      port: 6379
      dbNumber: 0
      password: ""
      expireDays: 2
  initialTimeInterval:
    hours: 2
    minutes: 0
  customQueries:
    - soql:
        select: [Id, Action, CreatedDate, DelegateUser, Display]
        from: "SetupAuditTrail"
        timestamp: CreatedDate
        apiVer: "58.0"

licenseKey: "MY-LICENSE-KEY"
accountId: "1234"
region: "US"
format: "events"
```

## Instances

The biggest difference is the concept of instances present in v2. There is no
such concept in v3, the integration runs for only one SFDC instance, there is
no way to collect data from multiple instances within one config file. To
collect multiple instances, we have to create multiple config files and run the
integration for each config file. So if your v2 config file looks like this:

```yaml
# ...
instances:
  - name: my-instance-1
    # ...
  - name: my-instance-2
    # ...
  - name: my-instance-3
    # ...
```

You will have to create three different config files: for my-instance-1,
my-instance-2, and my-instance-3.

Having separate integrations running for each instance has multiple advantages
like namespacing, more configuration flexibility, and resource scaling.

## General structure

A valid v3 config file requires the following fields:

```yaml
version: "2.0"

eventLog:
    # ...

licenseKey: "<LICENSE KEY HERE>"
accountId: "<ACCOUNT ID HERE>"
region: "<REGION HERE>" # either "EU" or "US"
format: "<FORMAT HERE>" # either "events" or "logs"

runAsService: false # true or false

# Other config options...
```

Check out the [official documentation](https://github.com/newrelic/newrelic-salesforce-exporter/tree/main/cmd/nr-salesforce-eventlog#setup) for more info.

## Field translation table

| v2 field | v3 field | Comments |
| --- | --- | --- |
| `integration_name` | N/A | Now the integration name is hardcoded. |
| `api_ver` | `apiVer` | Same meaning, applicable to the whole integration, specific queries and org limits. [More info](https://github.com/newrelic/newrelic-salesforce-exporter/tree/main/cmd/nr-salesforce-eventlog#setup).|
| `run_as_service` | `runAsService` | Same meaning. |
| `cron_interval_minutes` | `eventLog -> initialTimeInterval` | Check [`initialTimeInterval` doc](https://github.com/newrelic/newrelic-salesforce-exporter/tree/main/cmd/nr-salesforce-eventlog#--initialtimeinterval) for more info. |
| `service_schedule` | `eventLog -> initialTimeInterval` | Check [`initialTimeInterval` doc](https://github.com/newrelic/newrelic-salesforce-exporter/tree/main/cmd/nr-salesforce-eventlog#--initialtimeinterval) for more info. |
| `request_timeout` | `eventLog -> requestTimeout` | Same meaning. |
| `instances -> name` | `eventLog -> instanceName` | Same meaning. |
| `instances -> arguments -> token_url` | `eventLog -> auth -> tokenUrl` | Now it's only the base URL, without the path. |
| `instances -> arguments -> auth` | `eventLog -> auth` | Same semantics, only the field names change. [More info](https://github.com/newrelic/newrelic-salesforce-exporter/tree/main/cmd/nr-salesforce-eventlog#--auth). |
| `instances -> arguments -> cache_enabled` | N/A | Now there is no explicit flag to enable the cache. The presence of a cache config is enough. |
| `instances -> arguments -> redis` | `eventLog -> cache -> redis` | Same semantics, only the field names change. [More info](https://github.com/newrelic/newrelic-salesforce-exporter/tree/main/cmd/nr-salesforce-eventlog#--cache). |
| `instances -> arguments -> date_field` | N/A | Now always CreatedDate. |
| `instances -> arguments -> generation_interval` | N/A | Now always Hourly. |
| `instances -> arguments -> time_lag_minutes` | N/A | Deprecated. |
| `instances -> arguments -> auth_env_prefix` | N/A | Deprecated. |
| `instances -> arguments -> logs_enabled` | N/A | Deprecated. The integration no longer performs autologging. |
| `instances -> labels` | N/A | Deprecated. |
| `instances -> arguments -> queries` | `eventLog -> customQueries` | The query format changed. [More info](https://github.com/newrelic/newrelic-salesforce-exporter/tree/main/cmd/nr-salesforce-eventlog#--customqueries). |
| `queries` | `eventLog -> customQueries` | The query format changed. [More info](https://github.com/newrelic/newrelic-salesforce-exporter/tree/main/cmd/nr-salesforce-eventlog#--customqueries). |
| `instances -> arguments -> limits` | `eventLog -> limits` | Same meaning. [More info](https://github.com/newrelic/newrelic-salesforce-exporter/tree/main/cmd/nr-salesforce-eventlog#--limits) |
| `newrelic` | `licenseKey`, `accountId`, `region`, `format` | Same meaning, only the field names change. [More info](https://github.com/newrelic/newrelic-salesforce-exporter/tree/main/cmd/nr-salesforce-eventlog#new-relic-credentials). |

## `EventLogFile` custom queries

The new integration does not use custom queries for the `EventLogFile` object.
Instead, it provides a mechanism to select event types, the `eventLog -> eventTypes`
[field](https://github.com/newrelic/newrelic-salesforce-exporter/tree/main/cmd/nr-salesforce-eventlog#--eventtypes).

## Event types fields

The old integration uses the `event_type_fields.yml` file for field mapping.
The new integration provides a more integrated mechanism: the `fieldMapping`
config [key](https://github.com/newrelic/newrelic-salesforce-exporter/tree/main/cmd/nr-salesforce-eventlog#--fieldmapping),
and the `fieldMappingFile` config [key](https://github.com/newrelic/newrelic-salesforce-exporter/tree/main/cmd/nr-salesforce-eventlog#--fieldmappingfile).