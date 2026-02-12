# New Relic Salesforce Event Stream Integration

  1. [Introduction](#introduction)
  1. [Build](#build)
  1. [Run](#run)
  1. [Setup](#setup)
  1. [Data](#data)
  1. [Docker](#docker)
  1. [Debugging](#debugging)
  1. [Testing](#testing)

## Introduction

The Event Stream integration reads a stream of events from Salesforce and injects
them into New Relic.
It uses the [Pub/Sub API](https://developer.salesforce.com/docs/platform/pub-sub-api/overview)
to subscribe to [topics](https://developer.salesforce.com/docs/platform/pub-sub-api/references/methods/gettopic-rpc.html)
(event types) and listen to the stream of data comming from a gRPC connection.

> NOTE: If for some reason you can't use the newer Pub/Sub API, and instead you
have to use the [Streaming API](https://developer.salesforce.com/docs/atlas.en-us.api_streaming.meta/api_streaming/intro_stream.htm),
consider using the [legacy event streaming integration](https://github.com/newrelic/nr-salesforce-event-streaming),
which is outdated and unmaintained, but should work.

## Build

Install [Go](https://go.dev/doc/install) first. The minimum required version is
`1.25.3`.

From the folder `cmd/nr-salesforce-stream/`, run:

```bash
go build nr-salesforce-stream.go
```

It will generate a binary `nr-salesforce-stream` in the same folder.

## Run

Once the config file is set, we can run the integration:

```bash
./nr-salesforce-stream --config_path path/to/config.yml
```

Check the [setup](#setup) section for more information on how to set up the
config file or check the [sample file](../../config_sample_eventstream.yml)
provided in this repo.

Run the integration with `--help` for a complete list of arguments:

```bash
./nr-salesforce-stream --help
```

## Setup

The event stream integration obtains the configuration from a YAML file. There is
a [sample config file](../../config_sample_eventstream.yml) you can use as a
template to create your own.

The following is a list of the required keys and a description for each.

### Version

The version key is mandatory and must contain the value `2.0`:

```yaml
version: "2.0"
```

### Event Stream

The `eventStream` key contains the following structure:

```yaml
eventStream:
  integrationName: "MY INTEGRATION NAME"
  appetite: 10
  auth:
    # Auth section, described later
  cache:
    # Cache section, described later
  topics:
    # Topics section, described later
```

The `integrationName` must contain a descriptive name for the integration,
something like `com.newrelic.labs.sfdc.eventstream` is recommended.

The `appetite` must contain an integer with the maximum number of events to read
per call. If unspecified, the default value is `10`.

Any value within the `eventStream` section can be specified with an environment
variable. To do that, just set `$ENV_VAR_NAME` as the value. Example:

```yaml
eventStream:
  integrationName: $INTEGRATION
```

It will get the value of `integragtionName` from the environment variable named
`INTEGRATION`.

Each one of the config keys within `eventStream` are described in the following
sections.

#### Auth

| Valid Values | Required | Default |
| --- | --- | --- |
| Auth structure | Yes | N/A |

It describes the credentials to connect to the Salesforce API. Currently we only
support the **Username-Password** auth flow:

**Username-Password**:

It has the following structure:

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

#### Cache

| Valid Values | Required | Default |
| --- | --- | --- |
| Cache structure | No | Empty |

Setting up the cache is optional but **strongly recommended**. The cache is used
to keep track of the latest event ID received. In case there is an interruption
in the integration, when it comes back online again it will start requesting events
from the ID stored in the cache. If the cache is not set, all the events generated
during the offline period will be lost.

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

#### Topics

| Valid Values | Required | Default |
| --- | --- | --- |
| List of strings | Yes | N/A |

A list of the event types we want to capture. Example:

```yaml
  topics:
    - "/event/LoginEventStream"
    - "/event/LogoutEventStream"
    - "/event/ReportEventStream"
    - "/event/ApiEventStream"
    - "/event/FileEvent"
    - "/event/UriEventStream"
    - "/event/LightningUriEventStream"
```

### New Relic credentials

Credentials to inject data to New Relic.

```yaml
licenseKey: "<LICENSE KEY HERE>"
accountId: "<ACCOUNT ID HERE>"
region: "<REGION HERE>"
format: "<FORMAT HERE>"
```

- `licenseKey`: A New Relic license key with permissions to inject data. It can
also be specified using the `NR_LICENSE_KEY` environment variable.
- `accountId`: The account ID where the license key was created. It can also be
specified using the `NR_ACCOUNT_ID` environment variable.
- `region`: The region of your account ID: Either `US` or `EU`.
- `format`: The data format we want to inject to New Relic: Either `events` or
`logs`.

## Data

This integration can generate New Relic `events` or `logs`, depending on the value
of the key `format` in the config file.

### Events

The integration will generate a new `eventType` for each topic, with the format
`SFDC{topic name}`. For example, the topic `/event/LoginEventStream` will generate
`SFDCLoginEventStream` events.

To view the data, you can run the following NRQL:

```sql
FROM SFDCLoginEventStream SELECT *
```

### Logs

The integration will generate a new log with the `message` in the format `SFDC{topic name}`.
 For example, the topic `/event/LoginEventStream` will generate
`SFDCLoginEventStream` log message.

To view the data, you can run the following NRQL:

```sql
FROM Log SELECT * WHERE message = 'SFDCLoginEventStream'
```

## Docker

> Set up correct configuration for `config.yml` before proceeding.

This repo includes a [Dockerfile](../../Dockerfile.eventstream) for the eventlog
integration.

To create the image, go to the root of the repo folder, and run:

```bash
docker build -f Dockerfile.eventstream --tag newrelic/sfdc-eventstream:VERSION .
```

Set `VERSION` accordingly.

And run it:

```bash
docker run newrelic/sfdc-eventstream:VERSION
```

Add `-d` after `docker run` to run in detached mode.

## Debugging

To capture the complete sequence of console logs, add the following to your config
file:

```yaml
log:
  level: trace
```

## Testing

From the project's root folder run:

```bash
go test ./...
```

Or, for a more detailed output:

```bash
go test -v ./...
```