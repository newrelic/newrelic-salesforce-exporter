[![New Relic Community header](https://opensource.newrelic.com/static/Community_Project-0c3079a4e4dbe2cbd05edc4f8e169d7b.png)](https://opensource.newrelic.com/oss-category/#new-relic-community)

![GitHub forks](https://img.shields.io/github/forks/newrelic/newrelic-salesforce-exporter?style=social)
![GitHub stars](https://img.shields.io/github/stars/newrelic/newrelic-salesforce-exporter?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/newrelic/newrelic-salesforce-exporter?style=social)

![GitHub all releases](https://img.shields.io/github/downloads/newrelic/newrelic-salesforce-exporter/total)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/newrelic/newrelic-salesforce-exporter)
![GitHub last commit](https://img.shields.io/github/last-commit/newrelic/newrelic-salesforce-exporter)
![GitHub Release Date](https://img.shields.io/github/release-date/newrelic/newrelic-salesforce-exporter)

![GitHub issues](https://img.shields.io/github/issues/newrelic/newrelic-salesforce-exporter)
![GitHub issues closed](https://img.shields.io/github/issues-closed/newrelic/newrelic-salesforce-exporter)
![GitHub pull requests](https://img.shields.io/github/issues-pr/newrelic/newrelic-salesforce-exporter)
![GitHub pull requests closed](https://img.shields.io/github/issues-pr-closed/newrelic/newrelic-salesforce-exporter)

# Salesforce Exporter for New Relic

The Salesforce Exporter offers an integration to process and forward Salesforce
data to New Relic as either logs or events. The exporter currently supports
sending the results of an SOQL query (with special handling for event log file
queries) and sending information on Salesforce Org Limits.

## System Requirements

The New Relic Salesforce Exporter can be run on any host environment with
Python 3.9+ installed.

It can also be run inside a Docker container by leveraging
[the published Docker image](https://hub.docker.com/r/newrelic/newrelic-salesforce-exporter)
[directly](#run-directly-from-dockerhub), as a base image for
[building a custom image](#extend-the-base-image), or using
[the provided `Dockerfile`](./Dockerfile) to [build a custom image](#build-a-custom-image).

In addition, the Salesforce Exporter requires the use of a Salesforce
[connected app](https://help.salesforce.com/s/articleView?id=sf.connected_app_overview.htm&type=5)
in order to extract data via the Salesforce APIs. The connected app _must_ be
[configured](https://help.salesforce.com/s/articleView?id=sf.connected_app_create_api_integration.htm&type=5)
to allow OAuth authentication and authorization for API integration. See the
[Authentication section](#authentication) for more information.

## Usage

### On-host

To use the Salesforce Exporter on a host, perform the following steps.

1. Clone this repository
1. Run `pip install -r requirements.txt` to install dependencies

Once installed, the Salesforce Exporter can be run from the repository root
using the command `python src/__main__.py`. See the section
[Command Line Options](#command-line-options) and [Configuration](#configuration)
for more details on using the exporter.

### Docker

A Docker image for the Salesforce Exporter is available at
[https://hub.docker.com/r/newrelic/newrelic-salesforce-exporter](https://hub.docker.com/r/newrelic/newrelic-salesforce-exporter). This image can be used in one of two ways.

#### Run directly from [DockerHub](https://hub.docker.com/)

The Salesforce Exporter [Docker image](https://hub.docker.com/r/newrelic/newrelic-salesforce-exporter)
can be run directly from [DockerHub](https://hub.docker.com/). To do this, the
[`config.yml`](#configyml) must be mapped into the running container. It can
be mapped using the default filename or using a custom filename. In the case of
the latter, the `-f` [command line option](#command-line-options) must be
specified with the custom filename. One of the same methods can be used to map
an [event type fields mapping file](#event-type-fields-mapping-file) and/or a
[numeric fields mapping file](#numeric-fields-mapping-file) into the running
container. In addition, environment variables can be passed to the container
using `docker run` with [the `-e`, `--env`, or `--env-file` options](https://docs.docker.com/reference/cli/docker/container/run/#env)
for [configuration parameters](#configuration) that can be specified via
environment variables. See below for examples.

**Example 1: Using the default configuration filename**

In the following example, the file `config.yml` in the current directory on the
host system is mapped with the default configuration filename in the container
(`config.yml`). In addition, the [`license_key`](#license_key) value is
specified using the `NR_LICENSE_KEY` environment variable and the
[application name](https://docs.newrelic.com/docs/apm/agents/python-agent/configuration/python-agent-configuration/#app_name)
and [license key](https://docs.newrelic.com/docs/apm/agents/python-agent/configuration/python-agent-configuration/#license_key)
agent parameters for the built-in [New Relic Python agent](#new-relic-python-agent)
are specified using the `NEW_RELIC_APP_NAME` AND `NEW_RELIC_LICENSE_KEY`
environment variables, respectively. No command line argument are passed to the
exporter.

```bash
docker run -t --rm --name salesforce-exporter \
   -v "$PWD/config.yml":/usr/src/app/config.yml \
   -e NR_LICENSE_KEY=$NR_LICENSE_KEY \
   -e NEW_RELIC_APP_NAME="New Relic Salesforce Exporter" \
   -e NEW_RELIC_LICENSE_KEY=$NEW_RELIC_LICENSE_KEY \
   newrelic/newrelic-salesforce-exporter
```

**Example 2: Using a custom configuration filename**

In the following example, the file `config.yml` in the current directory on the
host system is mapped with a custom configuration filename in the container
(`my_custom_config.yml`) and the `-f` [command line option](#command-line-options)
is used to specify the custom filename. The full path is not needed as
`/usr/src/app` is the working directory when the exporter runs in the container.
The environment variables are the same as in Example 1.

```bash
docker run -t --rm --name salesforce-exporter \
   -v "$PWD/config.yml":/usr/src/app/my_custom_config.yml \
   -e NR_LICENSE_KEY=$NR_LICENSE_KEY \
   -e NEW_RELIC_APP_NAME="New Relic Salesforce Exporter" \
   -e NEW_RELIC_LICENSE_KEY=$NEW_RELIC_LICENSE_KEY \
   newrelic/newrelic-salesforce-exporter \
   -f my_custom_config.yml
```

**Example 3: Using an [event type fields mapping file](#event-type-fields-mapping-file)**

The following example is the same as Example 1 except that an
[event type fields mapping file](#event-type-fields-mapping-file) is mapped into
the container with a custom filename in the container
(`my_event_type_fields.yml`) and the `-e` [command line option](#command-line-options)
is used to specify the custom filename. Again, the full path is not needed as
`/usr/src/app` is the working directory when the exporter runs in the container.

```bash
docker run -t --rm --name salesforce-exporter \
   -v "$PWD/config.yml":/usr/src/app/config.yml \
   -v "$PWD/my_event_type_fields.yml":/usr/src/app/my_event_type_fields.yml \
   -e NR_LICENSE_KEY=$NR_LICENSE_KEY \
   -e NEW_RELIC_APP_NAME="New Relic Salesforce Exporter" \
   -e NEW_RELIC_LICENSE_KEY=$NEW_RELIC_LICENSE_KEY \
   newrelic/newrelic-salesforce-exporter \
   -e my_event_type_fields.yml
```

**Example 4: Using additional environment variables**

In the following example, additional environment variables are passed to the
container to configure the exporter. In this case, caching is enabled via the
[`CACHE_ENABLED`](#cache_enabled) environment variable (in order to address
[data de-duplication](#data-de-duplication)) and the Redis connection parameters
are set using the `REDIS_*` environment variables.

```bash
docker run -t --rm --name salesforce-exporter \
   -v "$PWD/config.yml":/usr/src/app/config.yml \
   -e CACHE_ENABLED="yes" \
   -e REDIS_HOST="my.redis.test" \
   -e REDIS_PORT="15432" \
   -e REDIS_DB_NUMBER="2" \
   -e REDIS_SSL="on" \
   -e REDIS_PASSWORD="R3d1s1sGr3@t" \
   -e NR_LICENSE_KEY=$NR_LICENSE_KEY \
   -e NEW_RELIC_APP_NAME="New Relic Salesforce Exporter" \
   -e NEW_RELIC_LICENSE_KEY=$NEW_RELIC_LICENSE_KEY \
   newrelic/newrelic-salesforce-exporter
```

**NOTE:** In this scenario, the container will need to have access to the Redis
instance.

#### Extend the base image

The Salesforce Exporter [Docker image](https://hub.docker.com/r/newrelic/newrelic-salesforce-exporter)
can be used as the base image for building custom images. This scenario can be
easier as the [`config.yml`](#configyml) can be packaged into the custom image
and does not need to be mounted in. However, it does require access to
[a Docker registry](https://docs.docker.com/guides/docker-concepts/the-basics/what-is-a-registry/)
where the custom image can be pushed (e.g. [ECR](https://aws.amazon.com/ecr/)
and that is accessible to the technology used to manage the container
(e.g. [ECS](https://aws.amazon.com/ecs/)). In addition, this scenario requires
maintenance of a custom `Dockerfile` and the processes to build and publish the
image to a registry.

The minimal example of a `Dockerfile` for building a custom image simply extends
the base image (`newrelic/newrelic-salesforce-exporter`) and copies a
configuration file to the default location (`/usr/src/app/config.yml`).

```dockerfile
FROM newrelic/newrelic-salesforce-exporter

#
# Copy your config file into the default location.
# Adjust the local path as necessary.
#
COPY ./config.yml .
```

Note that the directory path in the container does not need to be specified.
This is because the base image sets the [`WORKDIR`](https://docs.docker.com/reference/dockerfile/#workdir)
to `/usr/src/app`. In fact, custom `Dockerfile`s should _not_ change the
`WORKDIR`.

The following commands can be used to build a custom image using a custom
`Dockerfile` that extends the base image.

```bash
docker build -t newrelic-salesforce-exporter-custom -f Dockerfile-custom .
docker tag newrelic-salesforce-exporter-custom someregistry/username/newrelic-salesforce-exporter-custom
docker push someregistry/username/newrelic-salesforce-exporter-custom
```

Subsequently, the exporter can be run using the custom image as in the previous
examples but without the need to mount the configuration file. Similarly, if
an [event type fields mapping file](#event-type-fields-mapping-file) and/or
a [numeric fields mapping file](#numeric-fields-mapping-file) are required,
these can be copied into the default locations using the custom `Dockerfile` as
well, eliminating the need for these files to be mounted into the container.

#### Build a custom image

The Salesforce Exporter [Docker image](https://hub.docker.com/r/newrelic/newrelic-salesforce-exporter)
can also be built locally using the provided [`Dockerfile`](./Dockerfile)
"as-is" or as the basis for building a custom `Dockerfile`. As is the case when
extending the base image, this scenario does require access to
[a Docker registry](https://docs.docker.com/guides/docker-concepts/the-basics/what-is-a-registry/)
where the custom image can be pushed (e.g. [ECR](https://aws.amazon.com/ecr/)
and that is accessible to the technology used to manage the container
(e.g. [ECS](https://aws.amazon.com/ecs/)). Similarly, it requires maintenance of
a custom `Dockerfile` and the processes to build and publish the image to a
registry.

The general set of steps for building a custom image using the provided
`Dockerfile` "as-is" are as follows.

1. Clone this repository
1. Navigate to the repository root
1. Run the following commands

```bash
docker build -t newrelic-salesforce-exporter .
docker tag newrelic-salesforce-exporter someregistry/username/newrelic-salesforce-exporter
docker push someregistry/username/newrelic-salesforce-exporter
```

To use a custom `Dockerfile`, backup the provided `Dockerfile`, make necessary
changes to the original, and follow the steps above.

As is the case when extending the base image, the exporter can be run using the
custom image as in the previous examples but without the need to mount any files
into the container.

### Features

The Salesforce Exporter supports the following capabilities.

* [Export event log files](#event-log-files)

  The default behavior of the exporter, in the absence of configuration for
  additional capabilities, is to collect Salesforce event log files. Log
  messages can be sent to New Relic as logs or events.

* [Export query results](#custom-queries)

  The exporter can execute arbitrary SOQL queries and send the query results to
  New Relic as logs or events.

* [Export org limits](#org-limits)

  The exporter can collect Salesforce Org Limits and send either all limits or
  only select limits to New Relic as logs or events.

### Command Line Options

| Option | Alias | Description | Default |
| --- | --- | --- | --- |
| -f | --config_file | name of [configuration file](#configyml) | `config.yml` |
| -c | --config_dir | path to the directory containing the [configuration file](#configyml) | `.` |
| -e | --event_type_fields_mapping | path to the [event type fields mapping file](#event-type-fields-mapping-file) | `event_type_fields.yml` |
| -n | --num_fields_mapping | path to the [numeric fields mapping file](#numeric-fields-mapping-file) | `numeric_fields.yml` |

For historical purposes, you can also use the `CONFIG_DIR` environment variable
to specify the directory containing the [configuration file](#configyml).

### Configuration

Several configuration files are used to control the behavior of the exporter.

#### `config.yml`

The main configuration for the exporter is the `config.yml` file. In fact, it
does not need to be named `config.yml` although that is the default name if a
name is not specified on the command line. The supported configuration
parameters are listed below.

See [`config_sample.yml`](./config_sample.yml) for a full configuration example.

##### Service configuration parameters

###### `integration_name`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| ID used in logs generated by the exporter | string | N | `com.newrelic.labs.sfdc.eventlogfiles` |

The integration name is used in the exporter logs for troubleshooting purposes.

###### `run_as_service`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| Flag to enable the built-in scheduler | `True` / `False` | N | `False` |

The exporter can run either as a service that uses a built-in scheduler to
run the export process on a set schedule or as a simple command line utility
which runs once and exits when it is complete. The latter is intended for use
with an external scheduling mechanism like [cron](https://man7.org/linux/man-pages/man8/cron.8.html).

When set to `True`, the exporter will run on a schedule specified in the
[`service_schedule`](#service_schedule) parameter. When set to `False` or
when not specified, the exporter will run once and exit. In this case, the
[`cron_interval_minutes`](#cron-interval-minutes) parameter should be used to
indicate the interval configured in the external scheduler. For example, if
using cron, this would be the frequency (in minutes) between runs setup in the
`crontab`.

###### `service_schedule`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| Schedule configuration used by the built-in scheduler | YAML Mapping | conditional | N/a |

This parameter is required if the [`run_as_service`](#run_as_service) parameter
is set to `True`. The value of this parameter is a YAML mapping with two
attributes: `hour` and `minute`.

The `hour` attribute specifies all the hours (0 - 23, comma separated) to invoke
the exporter. Use `*` as awildcard to invoke the application every hour. The
`minute` attribute specifies all the minutes (0 - 59, comma separated) at which
to invoke the exporter. For example, the following configuration will run the
exporter every hour on the hour as well as at the 15th minute, 30th minute
and 45th minute past every hour.

```yaml
service_schedule:
    hour: *
    minute: "0, 15, 30, 45"
```

###### `cron_interval_minutes`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| The execution interval (in minutes) used by the external scheduler | integer | N | 60 |

This parameter is used when the [`run_as_service`](#run_as_service) parameter
is set to `False` or is not set at all. This parameter is intended for use when
an external scheduling mechanism is being used to execute the exporter. The
value of this parameter is a number representing the interval (in minutes) at
which the external scheduler executes the exporter. For example, if using
CRON, this would be the frequency at which CRON invokes the process as
represented by the CRON expression in the `crontab`.

See the section [de-duplication without a cache](#de-duplication-without-a-cache)
for more details on the interaction between the [`cache_enabled`](#cache_enabled)
attribute, the [`date_field`](#date_field) attribute, the
[`time_lag_minutes`](#time_lag_minutes) attribute, the
[`generation_interval`](#generation_interval) attribute, and the
[`cron_interval_minutes`](#cron_interval_minutes) attribute.

**NOTE:** If [`run_as_service`](#run_as_service) is set to `False` and you set
this parameter to `0`, the time range that will be used for `EventLogFile`
queries generated by the exporter will be "since now", "until now" which will
result in no query results being returned.

###### `instances`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| An array of [instance configurations](#instance-configuration-parameters) | YAML Sequence | Y | N/a |

The exporter can run one or more exports each time it is invoked. Each export is
an "instance" defined using an [instance configuration](#instance-configuration-parameters).
This parameter is an array where each element is an [instance configuration](#instance-configuration-parameters).
This parameter must contain at least one [instance configuration](#instance-configuration-parameters).

##### `queries` (global)

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| An array of [custom query](#custom-queries) configurations | YAML mapping | N | `{}` |

The exporter is capable of running [custom SOQL queries](#custom-queries)
_instead of_ the default generated log file queries. This parameter can be used
to specify queries that should be run for all instances.

See the [custom queries section](#custom-queries) for more details.

##### `newrelic`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| New Relic configuration | YAML Mapping | Y | N/a |

This parameter contains the information necessary to send logs or events to your
New Relic account.

**NOTE:** The exporter uses the [New Relic Python APM agent](https://docs.newrelic.com/docs/apm/agents/python-agent/getting-started/introduction-new-relic-python/)
to report telemetry about itself to your account. The `license_key` attribute
defined in this configuration is _not_ used by the Python agent. See more
details about configuring the included Python agent in
[the New Relic Python Agent](#new-relic-python-agent) section.

###### `data_format`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| New Relic telemetry type | `logs` / `events` | N | `logs` |

This attribute specifies the type of telemetry to generate for exported data.
When set to `logs`, data exported from Salesforce will be transformed into
New Relic logs and sent via the New Relic Logs API. When set to `events`, data
exported from Salesforce will be transformed into New Relic events and sent via
the New Relic Events API.

###### `api_endpoint`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| New Relic region identifier | `US` / `EU` | Y | N/a |

This attribute specifies which New Relic region should be used to send
generated telemetry.

###### `account_id`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| New Relic account ID | integer | conditional | N/a |

This attribute specifies which New Relic account generated events should be sent
to. This attribute is required if the [`data_format`](#data_format) attribute is
set to `events`. It is ignored if the [`data_format`](#data_format) is `logs`.

The account ID can also be specified using the `NR_ACCOUNT_ID` environment
variable.

###### `license_key`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| New Relic license key | string | Y | N/a |

This attribute specifies the New Relic License Key (INGEST) that should be used
to send generated logs and events.

The license key can also be specified using the `NR_LICENSE_KEY` environment
variable.

##### Instance configuration parameters

An "instance" is defined using an instance configuration. An instance
configuration is a YAML mapping containing 3 attributes: `name`, `arguments`,
and `labels`.

###### `name`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| A symbolic name for the instance | string | Y | N/a |

The instance name is used in the exporter logs for troubleshooting purposes.

###### `arguments`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| The main configuration for the instance | YAML Mapping | Y | N/a |

The majority of the instance configuration is specified in the `arguments`
attribute. The attribute value is a YAML mapping. The supported arguments are
documented in [the instance arguments section](#instance_arguments).

###### `labels`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| A set of labels to include on all logs and events | YAML mapping | N | `{}` |

The `labels` parameter is a set of key/value pairs. The value of this parameter
is a YAML mapping. Each key/value pair is added to all logs and events generated
by the exporter.

##### Instance arguments

The main configuration of an instance is specified in the `arguments` attribute
of the [instance configuration](#instance-configuration-parameters). The value
of this attribute is a YAML mapping that supports the following values.

###### `api_ver`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| The version of the Salesforce API to use | any valid Salesforce API version number | N | `55.0` |

The `api_ver` attribute can be used to customize the version of the Salesforce
API that the exporter should use when making API calls. The exporter was tested
against API version `60.0`.

**NOTE:** The API version can also be configured at
[the query level](#api_ver-custom-queries) for custom queries and at
[the limit level](#api_ver-limits) for limits.

###### `token_url`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| The Salesforce URL to use for token-based authentication | URL | Y | N/a |

The exporter authenticates to Salesforce using token-based authentication. The
value of this attribute is used as the token URL. For more details, see the
[Authentication section](#authentication) below.

###### `auth`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| The authentication configuration | YAML Mapping | N | `{}` |

The configuration used to authenticate to Salesforce can be specified either in
the [`config.yml` ](#configyml) or the environment. If the `auth` attribute is
present, the exporter will attempt to load the configuration _entirely_ from the
[`config.yml` ](#configyml). The attribute value is a YAML mapping.

See the [Authentication section](#authentication) for more details.

###### `auth_env_prefix`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| A prefix to use when looking up environment variables | string | N | `''` |

Many, but not all, configuration values can be provided as environment
variables. When the exporter looks up an environment variable, it can
automatically prepend the environment variable name with a prefix. This prefix
is specified in the [instance arguments](#instance-arguments) using the
`auth_env_prefix` attribute. This enables different [instances](#instance-configuration-parameters)]
to use different environment variables in a single run of the exporter.

**NOTE:** This variable is named `auth_env_prefix` for historical reasons.
In previous releases, it only applied to authentication environment variables.
However, it currently applies to many other configuration environment variables.

###### `cache_enabled`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| Flag to control usage of a Redis cache for storing query record IDs and log entry IDs | `True` / `False` | N | `False` |

When this flag is set to `True`, the exporter will use a cache to store the IDs
of query records and log messages that have already been processed to prevent
duplication of data in New Relic. With this flag set to `False` or if the flag
is not specified, multiple occurrences of the same log message or query record
will result in duplicate log entries or events in New Relic.

See the section [de-duplication with a cache](#de-duplication-with-a-cache) for
more details on the use of caching to help prevent duplicaton of data.

###### `redis`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| The Redis configuration | YAML Mapping | conditional | `{}` |

The configuration used to authenticate to Redis. This attribute is required if
the [`cache_enabled`](#cache_enabled) attribute is set to `True`. The attribute
value is a YAML mapping.

See the section [de-duplication with a cache](#de-duplication-with-a-cache) for
more details.

###### `date_field`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| The name of the date field on the [`EventLogFile`](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile.htm) object to use when building log file queries  | `LogDate` / `CreatedDate` | N | conditional |

The [`EventLogFile`](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile.htm)
object has two date fields, `LogDate` and `CreatedDate`. Briefly, the `LogDate`
field represents the start of the collection interval for logs contained in the
given log file. The `CreatedDate` represents the date the given log file was
created. The decision to use one versus the other is primarily relevant with
regards to [caching](#de-duplication-with-a-cache).

The default value of this attribute is conditional on the value of
[`cache_enabled`](#cache_enabled) attribute. When the [`cache_enabled`](#cache_enabled)
attribute is set to `True`, the default value of this attribute is
`CreatedDate`. When the [`cache_enabled`](#cache_enabled) attribute is set to
`False`, the default value of this attribute is `LogDate`.

**NOTE:** This attribute is only used for `EventLogFile` queries generated by
the exporter. It is not used for [custom](#custom-queries) `EventLogFile`
queries.

See the section [de-duplication without a cache](#de-duplication-without-a-cache)
for more details on the interaction between the [`cache_enabled`](#cache_enabled)
attribute, the [`date_field`](#date_field) attribute, the
[`time_lag_minutes`](#time_lag_minutes) attribute, the
[`generation_interval`](#generation_interval) attribute, and the
[`cron_interval_minutes`](#cron_interval_minutes) attribute.

###### `generation_interval`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| The value of the `Interval` field on the [`EventLogFile`](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile.htm) object to use when building log file queries | `Daily` / `Hourly` | N | `Daily` |

There are two types of event log files created by Salesforce: daily (or
"24-hour") event log files and hourly event log files. Daily log files include
_all_ log files _for the previous day_ and are generated at approximately 3am
(server local time) each day. With respect to the exporter, the important
difference between the two has to do with how _deltas_ to these logs are
published.

The value of this attribute is automatically used for `EventLogFile` queries
generated by the exporter and is made available to [custom queries](#custom-queries)
as the query substitution variable `log_interval_type`.

See the section [de-duplication without a cache](#de-duplication-without-a-cache)
for more details on the interaction between the [`cache_enabled`](#cache_enabled)
attribute, the [`date_field`](#date_field) attribute, the
[`time_lag_minutes`](#time_lag_minutes) attribute, the
[`generation_interval`](#generation_interval) attribute, and the
[`cron_interval_minutes`](#cron_interval_minutes) attribute.

###### `time_lag_minutes`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| An offset duration (in _minutes_) to use when building log file queries | integer | N | conditional |

The value of this attribute affects the calculation of the start and end values
for the time range used in `EventLogFile` queries generated by the exporter and
the `to_timestamp` and `from_timestamp` values made available to
[custom queries](#custom-queries). Specifically, on each execution of the
exporter, the starting value of the time range will be set to the end value of
the time range on the previous execution (or the current time minus the
[`cron_interval_minutes`](#cron_interval_minutes) when
[`run_as_service`](#run_as_service) is `False`) minus the `time_lag_minutes` and
the ending value of the time range will be set to the current time minus the
value of `time_lag_minutes`.

The default value of this attribute is conditional on the value of
[`cache_enabled`](#cache_enabled) attribute. When the [`cache_enabled`](#cache_enabled)
attribute is set to `True`, the default value of this attribute is
`0`. When the [`cache_enabled`](#cache_enabled) attribute is set to
`False`, the default value of this attribute is `300`.

See the section [de-duplication without a cache](#de-duplication-without-a-cache)
for more details on the interaction between the [`cache_enabled`](#cache_enabled)
attribute, the [`date_field`](#date_field) attribute, the
[`time_lag_minutes`](#time_lag_minutes) attribute, the
[`generation_interval`](#generation_interval) attribute, and the
[`cron_interval_minutes`](#cron_interval_minutes) attribute.

###### `queries` (instance)

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| An array of instance-scoped [custom queries](#custom-queries) | YAML Sequence | N | `[]` |

The exporter is capable of running [custom SOQL queries](#custom-queries)
_instead of_ the default generated log file queries. This attribute can be used
to specify queries that should _only_ be run for the instance. These are
_separate_ from, but additive to, the queries defined in the top-level
[`queries`](#queries-global) configuration parameter.

See the [custom queries section](#custom-queries) for more details.

###### `limits`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| Limits collection configuration | YAML Mapping | N | `{}` |

In addition to exporting [`EventLogFile`](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile.htm)
logs and the results of SOQL queries, the exporter can also collect data about
[Salesforce Organization Limits](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_limits.htm).

See the [Org limits section](#org-limits) for more details.

###### `logs_enabled`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| Flag to explicitly enable or disable the default generated log file query | `True` / `False` | N | `True` |

By default, for each instance, the exporter will execute the default generated
log file query, unless [custom queries](#custom-queries) are defined at the
[global](#queries-global) or [instance](#queries-instance) level.

This attribute can be used to prevent the default behavior. For example, to
configure an instance to _only_ collect Salesforce org [limits](#limits), set
this attribute to `False` in conjunction with specifying the [`limits`](#limits)
configuration.

**NOTE:** When [custom queries](#custom-queries) are enabled (either at the
[global](#queries-global) or [instance](#queries-instance) level) the default
generated log file query will be disabled _automatically_ and the value of this
attribute will be ignored.

#### Event Type Fields Mapping File

[`EventLogFile`](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile.htm)
data can contain many attributes and the set of attributes
returned can differ depending on the event type. By default, the exporter will
include all attributes returned in the generated New Relic Logs or Events. This
behavior can be customized using an event type fields mapping file.  This file
contains a list of fields to record for each event type as shown in the
following example.

```yaml
mapping:
  Login: [ 'FIELD_A', 'FIELD_B' ]
  API: [ 'FIELD_A' ]
  OTHER_EVENT: [ 'OTHER_FIELDS' ]
```

See the file [event_type_fields.yml](./event_type_fields.yml) at the root of the
repository for an example.

**NOTE:** This mapping only applies to data in downloaded log message CSVs when
querying `EventLogFile` data. It does not apply to any other type of SOQL query
results.

#### Numeric Fields Mapping File

The data contained in downloaded log message CSVs when querying
[`EventLogFile`](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile.htm)
data are all represented using strings even if some of them are actually numeric
values. However, it may be beneficial to have numeric values converted to
numbers in the generated New Relic _Events_. To address this, a numeric fields
mapping file can be specified. This file defines the set of fields that should
be converted to numeric values by event type. The format of this file is the
same as the [event type fields mapping](#event-type-fields-mapping-file) file.

See the file [numeric_fields.yml](./numeric_fields.yml) at the root of the
repository for an example.

**NOTE:** The numeric fields mapping applies _only_ when generating New Relic
events. It is ignored when generating New Relic Logs.

**NOTE:** Unlike the event type fields mappings which only apply to
`EventLogFile` data, the numeric fields mappings apply to fields returned in
SOQL result sets as well.

### Authentication

The exporter supports the [OAuth 2.0 Username-Password flow](https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_username_password_flow.htm&type=5)
and the
[OAuth 2.0 JWT Bearer flow](https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_jwt_flow.htm&type=5)
for gaining access to the ReST API via a
[Connected App](https://help.salesforce.com/s/articleView?id=sf.connected_app_overview.htm&type=5).
The JWT Bearer flow is strongly recommended as it does not expose any passwords.

As mentioned above, authentication information can either be specified in the
[`auth`](#auth) attribute of the [`arguments`](#instance-arguments) parameter
of the [instance configuration](#instance-configuration-parameters) or in the
runtime system environment via environment variables.

#### OAuth 2.0 access token

Both OAuth 2.0 authorization flows require an [access token](https://help.salesforce.com/s/articleView?id=sf.remoteaccess_access_tokens.htm&type=5).
The access token is obtained using the Salesforce instance’s
[OAuth 2.0 token endpoint](https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_endpoints.htm&type=5),
e.g. `https://hostname/services/oauth2/token`.

The OAuth 2.0 token endpoint URL can be specified either as a
[configuration parameter](#token_url) or using the
`{auth_env_prefix}SF_TOKEN_URL` environment variable.

#### OAuth 2.0 Username-Password Flow

For the [OAuth 2.0 Username-Password Flow](https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_username_password_flow.htm&type=5),
the following parameters are required.

##### `grant_type`

The `grant_type` for the OAuth 2.0 Username-Password Flow _must_ be set to
`password` (case-sensitive).

The grant type can also be specified using the `{auth_env_prefix}SF_GRANT_TYPE`
environment variable.

##### `client_id`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| Consumer key of the connected app | string | Y | N/a |

This parameter specifies the **consumer key** of the connected app. To access
this value, navigate to "Manage Consumer Details" when viewing the Connected App
details.

The client ID can also be specified using the `{auth_env_prefix}SF_CLIENT_ID`
environment variable.

##### `client_secret`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| Consumer secret of the connected app | string | Y | N/a |

This parameter specifies the **consumer secret** of the connected app. To access
this value, navigate to "Manage Consumer Details" when viewing the Connected App
details.

The client secret can also be specified using the
`{auth_env_prefix}SF_CLIENT_SECRET` environment variable.

##### `username`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| Username the connected app is impersonating | string | Y | N/a |

This parameter specifies the **username** that the connected app will
impersonate/imitate for authentication and authorization purposes.

The username can also be specified using the `{auth_env_prefix}SF_USERNAME`
environment variable.

##### `password`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| Password of the user the connected app is impersonating | string | Y | N/a |

This parameter specifies the **password** of the user that the connected app
will impersonate/imitate for authentication and authorization purposes.

The password can also be specified using the `{auth_env_prefix}SF_PASSWORD`
environment variable.

**NOTE:** As noted in [the OAuth 2.0 Username-Password flow documentation](https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_username_password_flow.htm&type=5),
the password requires a security token to be concatenated with it when
authenticating from an untrusted network.

##### Example

Below is an example OAuth 2.0 Username-Password Flow configuration in the
[`auth`](#auth) attribute of the [instance arguments](#instance-arguments)
attribute of the [instance configuration parameter](#instance-configuration-parameters).

```yaml
token_url: https://my.salesforce.test/services/oauth2/token
# ... other instance arguments ...
auth:
  grant_type: password
  client_id: "ABCDEFG1234567"
  client_secret: "1123581321abc=="
  username: pat
  password: My5fPa55w0rd
```

Below is an example OAuth 2.0 Username-Password Flow configuration using
environment variables with _no prefix_ from a `bash` shell.

```bash
export SF_TOKEN_URL="https://my.salesforce.test/services/oauth2/token"
export SF_GRANT_TYPE="password"
export SF_CLIENT_ID="ABCDEFG1234567"
export SF_CLIENT_SECRET="1123581321abc=="
export SF_USERNAME="pat"
export SF_PASSWORD="My5fPa55w0rd"
```

#### OAuth 2.0 JWT Bearer Flow

For the [OAuth 2.0 JWT Bearer Flow](https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_jwt_flow.htm&type=5),
the following parameters are required.

##### `grant_type`

The `grant_type` for the OAuth 2.0 JWT Bearer Flow _must_ be set to
`urn:ietf:params:oauth:grant-type:jwt-bearer` (case-sensitive).

The grant type can also be specified using the `{auth_env_prefix}SF_GRANT_TYPE`
environment variable.

##### `client_id`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| `client_id` of the connected app | string | Y | N/a |

This parameter specifies the **client_id** generated and assigned to the
connected app when it is saved after
[registering the X509 certificate](https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_jwt_flow.htm&type=5)

The client ID can also be specified using the `{auth_env_prefix}SF_CLIENT_ID`
environment variable.

##### `private_key`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| Path to the file containing the private key of the connected app | file path | Y | N/a |

This parameter specifies the file system path to the file containing the private
key that is associated with the X509 certificate that is
[registered]((https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_jwt_flow.htm&type=5))
with the connected app. The private key is used to sign the JWT.

The private key file path can also be specified using the
`{auth_env_prefix}SF_PRIVATE_KEY` environment variable.

##### `subject`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| Value for the `sub` claim | string | Y | N/a |

This parameter specifies the value used for the `sub` claim in the JSON Claims
Set for the JWT. Per [the documentation](https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_jwt_flow.htm&type=5),
this should be set to the user's username when accessing an Experience Cloud
site.

The subject can also be specified using the `{auth_env_prefix}SF_SUBJECT`
environment variable.

##### `audience`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| Value for the `aud` claim | string | Y | N/a |

This parameter specifies the value used for the `aud` claim in the JSON Claims
Set for the JWT. Per [the documentation](https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_jwt_flow.htm&type=5),
this should be set to the authorization server's URL.

The audience can also be specified using the `{auth_env_prefix}SF_AUDIENCE`
environment variable.

##### `expiration_offset`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| An offset duration (in _minutes_) to use when calculating the JWT `exp` claim | integer | N | 5 |

This value of this parameter is added to the current time and the result is used
as the value of the `exp` claim in the JSON Claims Set for the JWT. The value
_must_ be a positive integer.

The expiration offset can also be specified using the
`{auth_env_prefix}SF_EXPIRATION_OFFSET` environment variable.

##### Example

Below is an example OAuth 2.0 JWT Bearer Flow configuration in the
[`auth`](#auth) attribute of the [instance arguments](#instance-arguments)
attribute of the [instance configuration parameter](#instance-configuration-parameters).

```yaml
auth:
  grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer"
  client_id: "GFEDCBA7654321"
  private_key: "path/to/private_key_file"
  subject: pat
  audience: "https://login.salesforce.com"
```

Below is an example OAuth 2.0 JWT Bearer Flow configuration using environment
variables with _no prefix_ from a `bash` shell.

```bash
export SF_TOKEN_URL="https://my.salesforce.test/services/oauth2/token"
export SF_GRANT_TYPE="urn:ietf:params:oauth:grant-type:jwt-bearer"
export SF_CLIENT_ID="GFEDCBA7654321"
export SF_PRIVATE_KEY="path/to/private_key_file"
export SF_SUBJECT="pat"
export SF_AUDIENCE="https://login.salesforce.com"
```

### Event Log Files

The default behavior of the exporter, in the absence of
configuration of additional capabilities, is to collect event logs using the
log related attributes in [the instance arguments](#instance-arguments) of
[each instance configuration](#instance-configuration-parameters), for
example, [`date_field`](#date_field),
[`generation_interval`](#generation_interval), etc.

Event log messages are collected by executing an
[SOQL](https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql.htm)
query for [`EventLogFile`](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile.htm)
objects, iterating through each result object, and processing the log messages
in the log file referenced by the `LogFile` attribute.

Subsequently, the event log messages in the log files are transformed into the
[New Relic Logs API](https://docs.newrelic.com/docs/logs/log-api/introduction-log-api/)
[payload format](https://docs.newrelic.com/docs/logs/log-api/introduction-log-api/#json-content)
or the [New Relic Events API](https://docs.newrelic.com/docs/data-apis/ingest-apis/event-api/introduction-event-api/)
[payload format](https://docs.newrelic.com/docs/data-apis/ingest-apis/event-api/introduction-event-api/#instrument)
and sent to New Relic.

**NOTE:** The event log file functionality is really just specialized logic
for handling query results of `EventLogFile` queries. Under the hood, the logic
to run [custom queries](#custom-queries) and the logic to query for
`EventLogFile` records run through the same code path. The paths diverge only
when the exporter detects that the query results contain `EventLogFile` records.
In this case, the exporter proceeds to process the log messages in the
referenced event log file. In fact, the exporter will even detect `EventLogFile`
records returned from [custom queries](#custom-queries). This is why the
[default event log file queries](#default-event-log-file-queries) are disabled
when [custom queries](#custom-queries) are specified. In this case, it is
assumed that customized `EventLogFile` queries will be provided (although this
is not required).

#### Default event log file queries

By default, the exporter will execute one of the following queries.

* When [`date_field`](#date_field) is set to `LogDate`:

  ```sql
  SELECT Id,EventType,CreatedDate,LogDate,Interval,LogFile,Sequence
  FROM EventLogFile
  WHERE LogDate>={from_timestamp} AND LogDate<{to_timestamp} AND Interval='{log_interval_type}'
  ```

* When [`date_field`](#date_field) is set to `CreateDate`:

  ```sql
  SELECT Id,EventType,CreatedDate,LogDate,Interval,LogFile,Sequence
  FROM EventLogFile
  WHERE CreatedDate>={from_timestamp} AND CreatedDate<{to_timestamp} AND Interval='{log_interval_type}'
  ```

If [custom queries](#custom-queries) are specified either at the global or
instance scope, or the [logs_enabled](#logs_enabled) flag is set to `False`,
the default queries are _disabled_. However, event log files can still be
collected by adding a [custom query](#custom-queries) against the `EventLogFile`
object. The exporter will automatically detect `EventLogFile` results and
process the log messages in each event log file identified by the `LogFile`
attribute in each result.

**NOTE:** For more details on `{from_timestamp}`, `{to_timestamp}` and
`log_interval_type`, see the [query substitution variables](#query-substitution-variables)
section.

#### Event log file data mapping

Salesforce event log file data is mapped to New Relic data as follows.

1. Before processing event log file messages, the "event type" is set to either
   the [`event_type`](#event_type-custom-queries) value or the `EventType`
   attribute of the `EventLogFile` record.
1. Next, a connection is opened to stream the log file specified by the
   `LogFile` attribute of the `EventLogFile` into the CSV parser.
1. For each line of the CSV file, the line is converted to a Python `dict`
   object and processed into a single [New Relic log entry](https://docs.newrelic.com/docs/logs/log-api/introduction-log-api/#json-logs)
   as follows.
    1. The `attributes` for the New Relic log entry are built first as follows.
        1. If an [event type fields mapping file](#event-type-fields-mapping-file)
           exists and the calculated event type from step 1 exists in the
           mapping, copy the fields listed in the mapping from the log message
           to the `attributes`.
        1. Otherwise, copy all the fields.
        1. A timestamp to use in subsequent steps is calculated as follows.
            1. If a `TIMESTAMP` field exists on the log message, convert it to
               the number of seconds since the epoch and remove `TIMESTAMP` from
               the `attributes`.
            1. Otherwise, use the _current_ number of seconds since the epoch
               for the timestamp.
        1. Set the `LogFileId` attribute in `attributes` to the `Id` field of
           the `EventLogFile` record (not the log message).
        1. Set the `EVENT_TYPE` attribute in `attributes` to either the
           [`event_type`](#event_type-custom-queries) value or the `EVENT_TYPE`
           field from the log message. If neither exists, it is set to
           `SFEvent`.
        1. The calculated timestamp value is set with the attribute name
           specified in [`rename_timestamp`](#rename_timestamp) or the name
           `timestamp`.
    1. The `message` for the New Relic log entry is set to
       `LogFile RECORD_ID row LINE_NO` where `RECORD_ID` is the `Id` attribute
       of the `EventLogFile` record and `LINE_NO` is the number of the row of
       the CSV file currently being processed.
    1. If, and only if, the calculated name of the `timestamp` field is
       `timestamp`, the `timestamp` for the New Relic log entry is set to the
       calculated timestamp value. Otherwise, the time of ingestion will be used
       as the timestamp of the log entry.
1. If the target New Relic data type is an event, the calculated log entry is
   converted to an event as follows.
    1. Each attribute from the `attributes` value of the log entry is copied to
       the event.
    1. Any attribute with a name in the set of combined field names of all event
       types from the [numeric fields mapping file](#numeric-fields-mapping-file),
       is converted to a numeric value. If the conversion fails, the value
       remains as a string.
    1. The `eventType` of the event is set to the `EVENT_TYPE` attribute.

Below is an example of an `EventLogFile` record, a single log message, and the
New Relic log entry or New Relic event that would result from the above
transformation.

**Example `EventLogFile` Record:**

```json
{
    "attributes": {
      "type": "EventLogFile",
      "url": "/services/data/v52.0/sobjects/EventLogFile/00001111AAAABBBB"
    },
    "Id": "00001111AAAABBBB",
    "EventType": "ApexCallout",
    "CreatedDate": "2024-03-11T15:00:00.000+0000",
    "LogDate": "2024-03-11T02:00:00.000+0000",
    "Interval": "Hourly",
    "LogFile": "/services/data/v52.0/sobjects/EventLogFile/00001111AAAABBBB/LogFile",
    "Sequence": 1
}
```

**Example `EventLogFile` Log Message (shown abridged and with header row):**

"EVENT_TYPE","TIMESTAMP","REQUEST_ID","ORGANIZATION_ID","USER_ID","RUN_TIME","CPU_TIME",...
"ApexCallout","20240311160000.000","YYZ:abcdef123456","001122334455667","000000001111111","2112","10",...

**Example New Relic log entry:**

```json
{
    "message": "LogFile 00001111AAAABBBB row 0",
    "attributes": {
        "EVENT_TYPE": "ApexCallout",
        "REQUEST_ID": "YYZ:abcdef123456",
        "ORGANIZATION_ID": "001122334455667",
        "USER_ID": "000000001111111",
        "RUN_TIME": "2112",
        "CPU_TIME": "10",
        "LogFileId": "00001111AAAABBBB",
        "timestamp": 1710172800.0
    },
    "timestamp": 1710172800.0
}
```

**Example New Relic event:**

```json
{
    "EVENT_TYPE": "ApexCallout",
    "REQUEST_ID": "YYZ:abcdef123456",
    "ORGANIZATION_ID": "001122334455667",
    "USER_ID": "000000001111111",
    "RUN_TIME": "2112",
    "CPU_TIME": "10",
    "LogFileId": "00001111AAAABBBB",
    "timestamp": 1710172800.0,
    "eventType": "ApexCallout"
}
```

### Custom queries

The exporter can be configured to execute one or more arbitrary
[SOQL](https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql.htm)
queries and transform the query results into New Relic logs or events. Queries
can be specified at the [global level](#queries-global) or at the
[instance](#queries-instance) level. Global queries are executed once for each
instance while instance queries are executed just for that instance.

#### Custom `EventLogFile` queries

When custom queries are specified at any level,
[the default event log file queries](#default-event-log-file-queries) will be
disabled. However, the exporter will still detect `EventLogFile` records
returned from custom queries and automatically process the log messages in each
event log file identified by the `LogFile` attribute in each `EventLogFile`
result. This behavior can be leveraged to write custom `EventLogFile` queries
when more (or less) functionality is needed than is provided by the default
queries.

Custom `EventLogFile` queries _must_ include the following fields.

- `Id`
- `Interval`
- `LogFile`
- `EventType`
- `CreatedDate`
- `LogDate`

Failure to include these fields will cause the exporter to terminate with an
exit code.

**NOTE:** It is _very_ important when writing custom `EventLogFile` queries to
have an understanding of the issues discussed in the
[Data De-duplication section](#data-de-duplication) and the use of the
[query substitution variables](#query-substitution-variables) in order to craft
queries that do not select duplicate data. For instance, the following is an
example of a query that would result in duplicate data.

```sql
SELECT Id,EventType,CreatedDate,LogDate,LogFile,Interval FROM EventLogFile WHERE LogDate<={to_timestamp} AND Interval='Daily'
```

The problem with this query is that query time range is unbounded in the past.
Each time it is run, it would match all daily log files records since the
current time and it would process all log messages for all the records. If the
exporter was run, for example, every 15 minutes _without_ using a cache, this
query would post every log message from the past on every execution, resulting
in a potentially massive amount of data duplication. See
[the default event log file queries](#default-event-log-file-queries) for
examples of using the [query substitution variables](#query-substitution-variables)
in a way that will minimize data duplication.

#### Query configuration example

Custom queries are defined by specifying one or more
[query configurations](#query-configuration). An example
[query configuration](#query-configuration) is shown below.

```yaml
queries:
- query: "SELECT Id,EventType,CreatedDate,LogDate,LogFile,Interval FROM EventLogFile WHERE CreatedDate>={from_timestamp} AND EventType='API' AND Interval='Hourly'"
- query: "SELECT Id,Action,CreatedDate,DelegateUser,Display FROM SetupAuditTrail WHERE CreatedDate>={from_timestamp}"
  event_type: MySetupAuditTrailEvent
  timestamp_attr: CreatedDate
  rename_timestamp: actualTimestamp
- query: "SELECT EventName, EventType, UsageType, Client, Value, StartDate, EndDate FROM PlatformEventUsageMetric WHERE TimeSegment='FifteenMinutes' AND StartDate >= {start_date} AND EndDate <= {end_date}"
  api_ver: "58.0"
  id:
  - Value
  - EventType
  timestamp_attr: StartDate
  env:
    end_date: "now()"
    start_date: "now(timedelta(minutes=-60))"
```

#### Query configuration

Each query is defined with a set of configuration parameters. The supported
configuration parameters are listed below.

##### `query`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| The SOQL query to execute | string | Y | N/a |

The `query` parameter is used to specify the
[SOQL](https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql.htm)
query to execute.

##### `api_ver` (custom queries)

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| The version of the Salesforce API to use | string | N | `55.0` |

The `api_ver` attribute can be used to customize the version of the Salesforce
API that the exporter should use when executing query API calls.

##### `id`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| An array of field names to use when generating record IDs | YAML Sequence | N | `[]` |

The value of the `id` parameter is an array of strings. Each string specifies
the name of a field on the query records in the query results. The values of
these fields are used to generate a unique id for query records that do not have
an `Id` field. The unique id is generated by combining the values of each field
and generating a SHA-3 256-bit hash.

This parameter is used _only_ when transforming query records from custom
queries. It is not used when processing [event log files](#event-log-files).

##### `event_type` (custom queries)

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| The name of an event type to use when transforming log messages and query results to New Relic logs or events | string | N | conditional |

The value of the `event_type` parameter is used during the transformation of
event log file messages and query results from custom queries.

For more details on the usage of this parameter when querying the `EventLogFile`
object, see the [event log file data mapping](#event-log-file-data-mapping). For
more details on the usage of this parameter when querying other objects, see the
[query record data mapping](#query-record-data-mapping).

##### `timestamp_attr`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| The name of the query record field containing the value to use for the timestamp | string | N | `CreatedDate` |

The value of the `timestamp_attr` parameter specifies the name of the field on
query records in the query results that contains the value to use as the
timestamp when transforming query records to log entries or events. This
parameter is not used when transforming [event log files](#event-log-files).

##### `rename_timestamp`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| The name to use for the attribute on the log or event under which the timestamp will be stored | string | N | `timestamp` |

By default, the timestamp value taken from the query record will be stored
with the attribute name `timestamp`. The `rename_timestamp` parameter can be
used to specify an alternate name for this attribute. When present, the
generated log or event will not have a `timestamp` attribute. As a result,
a `timestamp` attribute will be added when the log or event is ingested and it
will be set to the time of ingestion.

This parameter is used both when transforming query records and when
transforming [event log files](#event-log-files).

##### `env`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| A set of [query substitution variables](#query-substitution-variables) | YAML Mapping | N | `{}` |

This parameter is used to define a set of custom
[query substitution variables](#query-substitution-variables) that can be used
to build more dynamic queries. The value of each query is one of the supported
Python expressions. For more details see the
[query substitution variables](#query-substitution-variables) section.

#### Query substitution variables

The [`query`](#query) parameter can contain substitution variables in the form
`{VARIABLE_NAME}`. The supported variables, listed below, are primarily
provided for the purposes of constructing custom `EventLogFile` queries, since
[the default event log file queries](#default-event-log-file-queries) will not
be run when custom queries are present.

For example usages of these variables, see the
[query configuration example](#query-configuration-example).

**NOTE:** As mentioned in [custom `EventLogFile` queries](#custom-eventlogfile-queries),
it is _very_ important when writing custom `EventLogFile` queries to
have an understanding of the issues discussed in the
[Data De-duplication section](#data-de-duplication) and the use of the
substitution variables below in order to craft queries that do not select
duplicate data.

##### `from_timestamp`

The `from_timestamp` substitution variable represents the start of the current
query time range. It is provided in ISO-8601 format as this is what is used by
the `LogDate` and `CreatedDate` fields on the `EventLogFile` record. When
[`run_as_service`](#run_as_service) is set to `False`, this value will be the
current time minus the [`time_lag_minutes`](#time_lag_minutes) minus the
[`cron_interval_minutes`](#cron_interval_minutes). When
[`run_as_service`](#run_as_service) is set to `True`, this will be the current
time minus the [`time_lag_minutes`](#time_lag_minutes) on the initial run and
the end time of the previous run on subsequent runs.

##### `to_timestamp`

The `to_timestamp` substitution variable represents the end of the current query
time range. It is provided in ISO-8601 format as this is what is used by the
`LogDate` and `CreatedDate` fields on the `EventLogFile` record. This value will
always be set to the current time minus the [`time_lag_minutes`](#time_lag_minutes).

##### `log_interval_type`

The `log_interval_type` substitution variable will always be set to the value of
the [`generation_interval`](#generation_interval) set in the
[`config.yml`](#configyml).

#### Custom substitution variables

In addition to the supported substitution variables, it is possible to define
additional substitution variables for each query using the `env` configuration
parameter. These variables contain supported Python expressions that are
evaluated to generate the data to be susbtituted in the query. The supported
expressions are listed below.

For example usages of these variables, see the
[query configuration example](#query-configuration-example).

**NOTE:** **WARNING**! This feature is currently implemented by using the
built-in Python [eval()](https://docs.python.org/3.9/library/functions.html?highlight=eval#eval)
function to evaluate the Python expressions specified in the configuration file.
While the expressions are evaluated in a sandbox, it is still possible to break
out of the sandbox and execute potentially malicious code. This functionality
will likely be replaced in the future with a more secure mechanism for building
dynamic queries.

##### `now()`

The `now()` expression will return the current time in ISO-8601 date-time
format. The expression can optionally take a timedelta argument and add it to
the current time, e.g. `now(timedelta(minutes=-60))`.

##### `sf_time()`

The `sf_time()` expression takes a Python
[`datetime`](https://docs.python.org/3.9/library/datetime.html?highlight=datetime#datetime-objects)
object and converts it to an ISO-8601 formatted date-time string.

##### `datetime`

The `datetime` expression returns a Python
[`datetime`](https://docs.python.org/3.9/library/datetime.html?highlight=datetime#datetime-objects)
object. Parameters may be passed just as they may to the
[`datetime` constructor](https://docs.python.org/3.9/library/datetime.html?highlight=datetime#datetime.datetime).

##### `timedelta`

The `timedelta` expression returns a Python
[`timedelta`](https://docs.python.org/3.9/library/datetime.html?highlight=datetime#timedelta-objects)
object. Parameters may be passed just as they may to the
[`timedelta` constructor](https://docs.python.org/3.9/library/datetime.html?highlight=datetime#datetime.timedelta).

#### External query configuration files

The _global_ `queries` parameter may "include" queries from other YAML files by
mixing file path strings into the `queries` array as in the following example.

```yaml
queries:
- "my_queries_file_1.yml"
- "my_queries_file_2.yml"
- query: "..."
```

The external query configuration files must contain a `queries` key with exactly
the same format as the [query configuration](#query-configuration), with the
limitation that the "included" files can not "include" other files.

#### Query record data mapping

Query records are mapped to New Relic data as follows.

1. For each query record returned in the query results, the record is converted
   into a Python `dict` object and processed into a single
   [New Relic log entry](https://docs.newrelic.com/docs/logs/log-api/introduction-log-api/#json-logs)
   as follows.
    1. The `attributes` for the New Relic log entry are built first as follows.
        1. Each field of the query record is copied into the `attributes` with
           the following considerations.

           - Query records typically contain their own `attributes` field that
             contain metadata about the record/object. This field is ignored.
           - The field names for nested fields are flattened by joining together
             the names at each level with the `.` character (i.e. the same way
             as they are selected in the SOQL statement).
           - Nested field "leaf" values that are not primitives are ignored.
           - Any `attributes` fields found in nested fields are ignored.

        1. If an `Id` field exists it is copied to `attributes`. Otherwise,
           a unique ID is generated using [the `id` configuration parameter](#id)
           and it is copied to `attributes`. If there is no
           [`id` configuration parameter](#id) or if the concatenated values
           yield an empty string, no `Id` field will be added.
        1. If the `attributes` field in the query record metadata is present and
           if it contains a `type` attribute, set the `EVENT_TYPE` attribute in
           `attributes` to either the [`event_type`](#event_type-custom-queries)
           value or the the value of the `type` attribute.
        1. A timestamp to use in subsequent steps is calculated as follows.
            1. If a value is specifed for [the `timestamp_attr` configuration parameter](#timestamp_attr)
               _and_ a field exists on the record with that name, convert the
               field value to the number of milliseconds since the epoch and use
               it for the timestamp. The field value (not the converted value)
               will also be used in the log entry `message` (see below).
            1. Otherwise, if the `CreatedDate` field exists on the record, treat
               the value in the same as in the previous step.
            1. Otherwise, use the _current_ number of milliseconds since the
               epoch for the timestamp.
        1. The timestamp value is set with the attribute name specified in
           [`rename_timestamp`](#rename_timestamp) or the name `timestamp`.
    1. The `message` for the New Relic log entry is set to
       `EVENT_TYPE CREATED_DATE` where `EVENT_TYPE` is either the
       [`event_type`](#event_type-custom-queries) value, the `type` attribute in
       the query record `attributes` metadata if it exists, or the value
       `SFEvent`, and the `CREATED_DATE` is the value of the field specified by
       [the `timestamp_attr` configuration parameter](#timestamp_attr), the
       value of the `CreatedDate` field, or the empty string.
    1. If, and only if, the calculated name of the `timestamp` field is
       `timestamp`, the `timestamp` for the New Relic log entry is set to the
       calculated timestamp value. Otherwise, the time of ingestion will be used
       as the timestamp of the log entry.

Below is an example of an SOQL query, a query result record, and the New Relic
log entry or New Relic event that would result from the above transformation.

**Example SOQL Query:**

```sql
SELECT Id, Name, BillingCity, CreatedDate, CreatedBy.Name, CreatedBy.Profile.Name, CreatedBy.UserType FROM Account
```

**Example `Account` Record:**

```json
  {
    "attributes": {
      "type": "Account",
      "url": "/services/data/v58.0/sobjects/Account/12345"
    },
    "Id": "000012345",
    "Name": "My Account",
    "BillingCity": null,
    "CreatedDate": "2024-03-11T00:00:00.000+0000",
    "CreatedBy": {
      "attributes": {
          "type": "User",
          "url": "/services/data/v55.0/sobjects/User/12345"
      },
      "Name": "Foo Bar",
      "Profile": {
          "attributes": {
              "type": "Profile",
              "url": "/services/data/v55.0/sobjects/Profile/12345"
          },
          "Name": "Beep Boop"
      },
      "UserType": "Bip Bop"
    }
  }
```

**Example New Relic log entry:**

```json
{
    "message": "Account 2024-03-11T00:00:00.000+0000",
    "attributes": {
        "EVENT_TYPE": "Account",
        "Id": "000012345",
        "Name": "My Account",
        "BillingCity": null,
        "CreatedDate": "2024-03-11T00:00:00.000+0000",
        "CreatedBy.Name": "Foo Bar",
        "CreatedBy.Profile.Name": "Beep Boop",
        "CreatedBy.UserType": "Bip Bop",
        "timestamp": 1710115200000,
    },
    "timestamp": 1710115200000
}
```

**Example New Relic event:**

```json
{
    "EVENT_TYPE": "Account",
    "Id": "000012345",
    "Name": "My Account",
    "BillingCity": null,
    "CreatedDate": "2024-03-11T00:00:00.000+0000",
    "CreatedBy.Name": "Foo Bar",
    "CreatedBy.Profile.Name": "Beep Boop",
    "CreatedBy.UserType": "Bip Bop",
    "timestamp": 1710115200000,
    "eventType": "Account"
}
```

### Org Limits

In addition to exporting `EventLogFile` logs and the results of custom SOQL
queries, the exporter can also collect data about
[Salesforce Org Limits](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_limits.htm).
Limits collection is configured at the instance level. It can _not_ be
configured at the global level like [custom queries](#custom-queries) can.

#### Limits configuration example

Limits collection is configured using the [limits configuration](#limits-configuration)
specified in the [`limits`](#limits) attribute of the [instance arguments](#instance-arguments)
attribute of the [instance configuration parameter](#instance-configuration-parameters).
An example [limits configuration](#limits-configuration) is shown below.

```yaml
limits:
  api_ver: "58.0"
  names:
  - ActiveScratchOrgs
  - DailyApiRequests
```

#### Limits configuration

The [`limits`](#limits) configuration supports the following configuration
parameters.

##### `api_ver` (limits)

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| The version of the Salesforce API to use | string | N | `55.0` |

The `api_ver` attribute can be used to customize the version of the Salesforce
API that the exporter should use when executing limits API calls.

##### `names`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| An array of limit names to collect | YAML Sequence | N | N/a |

By default, the exporter will collect information on all limits returned from
the [limits API](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_limits.htm).
The `names` configuration parameter can be used to limit the limits collected by
specifying a list of limit labels.

##### `event_type` (limits)

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| The name of an event type to use when transforming limits to New Relic logs or events | string | N | `SalesforceOrgLimit` |

The value of the `event_type` parameter is used during the transformation of
limits.

#### Limits data mapping

Limits data is mapped to New Relic data as follows.

1. The set of limit names is calculated as follows.

    1. If the [`names`](#names) parameter exists, each limit label listed in
       the array will be used. **NOTE**: If an empty array is specified using
       the inline flow sequence `[]`, _no_ limits will be collected.
    1. Otherwise, each limit label returned from the
       [limits API](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_limits.htm).
       will be used.

1. For each limit name in the calculated set of limits, data is converted as
   follows.
    1. If the limit name is not in the retrieved set of limits, processing
       continues with the next limit name.
    1. Otherwise, the limit is converted into a Python `dict` object and
       processed into a single [New Relic log entry](https://docs.newrelic.com/docs/logs/log-api/introduction-log-api/#json-logs)
       as follows.
    1. The `attributes` for the New Relic log entry are built first as follows.
        1. Set the `name` attribute to the limit name.
        1. If a `Max` attribute exists on the limit, convert the value to an
           integer and set the `Max` attribute to the converted value.
        1. If a `Remaining` attribute exists on the limit, convert the value to
           an integer and set the `Remaining` attribute to the converted value.
        1. If both the `Max` and `Remaining` attributes exist, calculate
           `Max - Remaining` and the the `Used` attribute to the result.
        1. Set the `EVENT_TYPE` attribute to either the
           [`event_type`](#event_type-limits) value or `SalesforceOrgLimit`.
    1. The `message` for the New Relic log entry is set to
       `Salesforce Org Limit: LIMIT_NAME` where `LIMIT_NAME` is the name of the
       limit being processed.
    1. The `timestamp` for the New Relic log entry is set to the current time in
       milliseconds since the epoch.

Below is an example of an abridged result returned from the
the [limits API](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_limits.htm).
and the New Relic log entry or New Relic event that would result from the above
transformation for the _first_ limit in the result.

**Example Limits API Result (show abridged):**

```json
{
    "ActiveScratchOrgs": {
        "Max": 3,
        "Remaining": 3
    },
    "AnalyticsExternalDataSizeMB": {
        "Max": 40960,
        "Remaining": 40960
    },
    "ConcurrentAsyncGetReportInstances": {
        "Max": 200,
        "Remaining": 200
    },
    "ConcurrentEinsteinDataInsightsStoryCreation": {
        "Max": 5,
        "Remaining": 5
    },
    "ConcurrentEinsteinDiscoveryStoryCreation": {
        "Max": 2,
        "Remaining": 2
    }
}
```

**Example New Relic log entry for the `ActiveScratchOrgs` limit:**

```json
{
    "message": "Salesforce Org Limit: ActiveScratchOrgs",
    "attributes": {
        "EVENT_TYPE": "SalesforceOrgLimit",
        "name": "ActiveScratchOrgs",
        "Max": 3,
        "Remaining": 3,
        "Used": 0
    },
    "timestamp": 1709876543210
}
```

**Example New Relic event for the `ActiveScratchOrgs` limit:**

```json
{
    "EVENT_TYPE": "SalesforceOrgLimit",
    "name": "ActiveScratchOrgs",
    "Max": 3,
    "Remaining": 3,
    "Used": 0,
    "eventType": "SalesforceOrgLimit"
}
```

### Data De-duplication

In certain scenarios, it is possible to encounter the same query results on
separate executions of the exporter. Without some mechanism to handle these
scenarios, this would result in duplication of data in New Relic. This can
not only lead to inaccurate query results in New Relic but also to unintended
ingest. In the case of
[`EventLogFile`](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile.htm)
data, the magnitude of data could be significant.

#### De-duplication with a cache

To help prevent duplication of data, the exporter can use a cache to store the
IDs of query records and log messages that have been previously processed.
Caching is enabled at the [instance](#instances) level using the
[`cache_enabled`](#cache_enabled) flag in the [instance arguments](#instance-arguments).
With this flag set to `True`, the exporter will attempt to connect to a Redis
cache using _a combination_ of the configuration set in the [`redis`](#redis)
section of the [instance arguments](#instance-arguments) and/or environment
variables.

The following configuration parameters are supported.

##### `host`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| Redis server hostname or IP address | string | N | `localhost` |

This parameter specifies the hostname or IP address of the Redis server.

The host can also be specified using the `{auth_env_prefix}REDIS_HOST`
environment variable.

##### `port`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| Redis server port | number / numeric string | N | `6379` |

This parameter specifies the port to connect to on the Redis server.

The port can also be specified using the `{auth_env_prefix}REDIS_PORT`
environment variable.

##### `db_number`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| Redis database number | number / numeric string | N | `0` |

This parameter specifies the database number to connect to on the Redis server.

The database number can also be specified using the
`{auth_env_prefix}REDIS_DB_NUMBER` environment variable.

##### `ssl`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| SSL flag | `True` / `False` | N | `False` |

This parameter specifies whether or not to use an SSL connection to connect to
the Redis server.

The SSL flag can also be specified using the `{auth_env_prefix}REDIS_SSL`
environment variable.

##### `password`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| Redis password | string | Y | N/a |

This parameter specifies the password to use to connect to the Redis server.

The password can also be specified using the `{auth_env_prefix}REDIS_PASSWORD`
environment variable.

##### `expire_days`

| Description | Valid Values | Required | Default |
| --- | --- | --- | --- |
| Cache entry expiry, in days | number / numeric string | N | `2` |

This parameter specifies the expiration time to use when putting any entry into
the cache. The time is specified in days.

The expiry can also be specified using the `{auth_env_prefix}REDIS_EXPIRE_DAYS`
environment variable.

##### Example

Below is an example Redis configuration in the [`redis`](#redis) attribute of
the [instance arguments](#instance-arguments) attribute of the
[instance configuration parameter](#instance-configuration-parameters).

```yaml
redis:
  host: my.redis.test
  port: 7721
  db_number: 2
  ssl: True
  password: "R3d1s1sGr3@t"
  expire_days: 1
```

Below is an example Redis configuration using environment variables with
_no prefix_ from a `bash` shell.

```bash
export REDIS_HOST="my.redis.test"
export REDIS_PORT="7721"
export REDIS_DB_NUMBER="2"
export REDIS_SSL="True"
export REDIS_PASSWORD="R3d1s1sGr3@t"
export REDIS_EXPIRE_DAYS="1"
```

#### De-duplication without a cache

If caching is not possible, several parameters are provided that can be used to
_reduce_ the chances of _log message duplication_, namely, `date_field`,
`generation_interval`, and `time_lag_minutes`. Use of these parameters may not
_eliminate_ duplication but will _reduce_ the chances of duplication.

In order to understand how these parameters interact, it can be helpful to have
an understanding of
[the basics of using event monitoring with event log files](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/using_resources_event_log_files.htm),
[the differences between `Hourly` and `Daily` event log files](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/event_log_file_hourly_diff.htm),
[considerations when querying `Hourly` event log files](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/event_log_file_hourly_overview.htm#hourly_considerations),
[the difference between `LogDate` and `CreatedDate`, and how and when Salesforce generates event log files.](https://www.salesforcehacker.com/2015/10/logdate-vs-createddate-when-to-use-one.html#:~:text=LogDate%20tracks%20usage%20activity%20of,the%20log%20file%20was%20generated.)

**NOTE:** The use of the parameters in this section _only_ apply to the
`EventLogFile` queries generated by the exporter and to the `to_timestamp`,
`from_timestamp`, and `log_interval_type` arguments that can be used by
[custom queries](#custom-queries).

##### Using `Hourly` logs

The best way to avoid duplication of log messages without a cache is to use
`Hourly` event log files. As mentioned in
[the ReST API Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/event_log_file_hourly_diff.htm),
`Hourly` log files are incremental, meaning that as new log messages arrive for
a given hour, new log files are generated with just the new log messages.

To use `Hourly` logs, set the [`generation_interval`](#generation_interval) to
`Hourly`.

When using an external scheduler ([`run_as_service](#run_as_service) is `False`),
it is also necessary to ensure that the external scheduler fires on a regular
interval (e.g. every 15 minutes or every day at 05:00) and that the
[`cron_interval_minutes`](#cron_interval_minutes) matches the regular interval.

When using the built-in scheduler ([run_as_service](#run_as_service) is `True`),
no additional configuration is necessary as the time of the last run is
persisted in memory.

With these settings, their _should_ be no duplication of log messages.

##### Using `Daily` logs

The best way to avoid duplication when querying `Daily` event log files without
using a cache is to set the [`date_field`](#date_field) to `LogDate` (the
default when [`cache_enabled`](#cache_enabled) is `False`) and to set
[`time_lag_minutes`](#time_lag_minutes) to between 180 (3 hours) and 300
(5 hours).

As with `Hourly` logs, when using an external scheduler ([`run_as_service](#run_as_service)
is `False`), it is also necessary to ensure that the external scheduler fires on
a regular interval (e.g. every 15 minutes or every day at 05:00) and that the
[`cron_interval_minutes`](#cron_interval_minutes) matches the regular interval.

When using the built-in scheduler ([run_as_service](#run_as_service) is `True`),
no additional configuration is necessary as the time of the last run is
persisted in memory.

With these settings, the `Daily` event log file should be picked up _once_,
anywhere between 3 and 5 hours _after_ the event log file `LogDate` (which will
always be midnight of each new day). The lag time accounts for the fact that
`Daily` event log files are generated each day around 0300 server local time
even though the reported `LogDate` will be 0000. Higher lag times can also
account for delays in log file generation due to heavy load on the log file
processing servers (Gridforce/Hadoop).

#### Recommended configurations

Following are the recommended configurations for avoiding duplication in each
of the above scenarios. In general, using `Hourly` for the
[`generation_interval`](#generation_interval) and `CreatedDate` for the
[`date_field`](#date_field) is the recommended configuration with or
without a cache.

| Scenario | Parameter | Recommended Value |
| --- | --- | --- |
| With a cache | | |
| | [`cache_enabled`](#cache_enabled) | `True` |
| | [`date_field`](#date_field) | `CreatedDate` |
| | [`generation_interval`](#generation_interval) | `Hourly` |
| | [`time_lag_minutes`](#time_lag_minutes) | `0` |
| | [`cron_interval_minutes`](#cron_interval_minutes) (if [`run_as_service`](#run_as_service) is `False`) | match external schedule |
| | [`service_schedule`](#service_schedule) (if [`run_as_service`](#run_as_service) is `True`) | any |
| Without a cache (Hourly) | | |
| | [`cache_enabled`](#cache_enabled) | `False` |
| | [`date_field`](#date_field) | `CreatedDate` |
| | [`generation_interval`](#generation_interval) | `Hourly` |
| | [`time_lag_minutes`](#time_lag_minutes) | `0` |
| | [`cron_interval_minutes`](#cron_interval_minutes) (if [`run_as_service`](#run_as_service) is `False`) | match external schedule |
| | [`service_schedule`](#service_schedule) (if [`run_as_service`](#run_as_service) is `True`) | any |
| Without a cache (Daily) | | |
| | [`cache_enabled`](#cache_enabled) | `False` |
| | [`date_field`](#date_field) | `LogDate` |
| | [`generation_interval`](#generation_interval) | `Daily` |
| | [`time_lag_minutes`](#time_lag_minutes) | `180` - `300` |
| | [`cron_interval_minutes`](#cron_interval_minutes) (if [`run_as_service`](#run_as_service) is `False`) | match external schedule |
| | [`service_schedule`](#service_schedule) (if [`run_as_service`](#run_as_service) is `True`) | any |

### Telemetry

#### New Relic Python Agent

The exporter uses the [New Relic Python APM agent](https://docs.newrelic.com/docs/apm/agents/python-agent/getting-started/introduction-new-relic-python/)
to report telemetry about itself to the New Relic account associated with the
specified [New Relic license key](#new-relic-license-key).

##### New Relic license key

As with any [New Relic APM agent](https://docs.newrelic.com/docs/apm/new-relic-apm/getting-started/introduction-apm/),
a license key is required to report agent telemetry. The license key used by the
Python agent must be defined either
[in the agent configuration file](https://docs.newrelic.com/install/python/?python-non-web=non-web-yes#config-file-option)
located at [`newrelic.ini`](./newrelic.ini) or
[using environment variables](https://docs.newrelic.com/install/python/#env-variables).

##### Application name

By default, the name of the application which the Python agent reports telemetry
to is `New Relic Salesforce Exporter`. This name can be changed either
[in the agent configuration file](https://docs.newrelic.com/install/python/?python-non-web=non-web-yes#config-file-option)
located at [`newrelic.ini`](./newrelic.ini) or
[using environment variables](https://docs.newrelic.com/install/python/#env-variables).

##### Other agent configuration

Additional agent configuration settings can be defined as outlined in the
[Python agent configuration documentation](https://docs.newrelic.com/docs/apm/agents/python-agent/configuration/python-agent-configuration/).

#### Application logs

The exporter automatically generates logs to trace its health state and correct
functioning. Logs are generated in the standard output as JSON objects, each
line being an object. This will help other integrations and tools to collect
these logs and handle them properly. The JSON object contains the following
keys:

- `message`: String. The log message.
- `timestamp`: Integer. Unix timestamp in milliseconds.
- `level`: String. `info`, `error` or `warn`.

## Support

New Relic has open-sourced this project. This project is provided AS-IS WITHOUT
WARRANTY OR DEDICATED SUPPORT. Issues and contributions should be reported to
the project here on GitHub.

We encourage you to bring your experiences and questions to the
[Explorers Hub](https://discuss.newrelic.com/) where our community members
collaborate on solutions and new ideas.

### Privacy

At New Relic we take your privacy and the security of your information
seriously, and are committed to protecting your information. We must emphasize
the importance of not sharing personal data in public forums, and ask all users
to scrub logs and diagnostic information for sensitive information, whether
personal, proprietary, or otherwise.

We define “Personal Data” as any information relating to an identified or
identifiable individual, including, for example, your name, phone number, post
code or zip code, Device ID, IP address, and email address.

For more information, review [New Relic’s General Data Privacy Notice](https://newrelic.com/termsandconditions/privacy).

### Contribute

We encourage your contributions to improve this project! Keep in mind that
when you submit your pull request, you'll need to sign the CLA via the
click-through using CLA-Assistant. You only have to sign the CLA one time per
project.

If you have any questions, or to execute our corporate CLA (which is required
if your contribution is on behalf of a company), drop us an email at
opensource@newrelic.com.

**A note about vulnerabilities**

As noted in our [security policy](../../security/policy), New Relic is committed
to the privacy and security of our customers and their data. We believe that
providing coordinated disclosure by security researchers and engaging with the
security community are important means to achieve our security goals.

If you believe you have found a security vulnerability in this project or any of
New Relic's products or websites, we welcome and greatly appreciate you
reporting it to New Relic through [HackerOne](https://hackerone.com/newrelic).

If you would like to contribute to this project, review [these guidelines](./CONTRIBUTING.md).

To all contributors, we thank you!  Without your contribution, this project
would not be what it is today.

### License

The [New Relic Salesforce Exporter] project is licensed under the
[Apache 2.0](http://apache.org/licenses/LICENSE-2.0.txt) License.
