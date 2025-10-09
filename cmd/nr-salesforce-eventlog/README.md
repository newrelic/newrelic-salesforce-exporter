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

TODO