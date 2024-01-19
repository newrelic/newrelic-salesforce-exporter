[![New Relic Community header](https://opensource.newrelic.com/static/Community_Project-0c3079a4e4dbe2cbd05edc4f8e169d7b.png)](https://opensource.newrelic.com/oss-category/#new-relic-community)

![GitHub forks](https://img.shields.io/github/forks/newrelic/newrelic-logs-salesforce-eventlogfile?style=social)
![GitHub stars](https://img.shields.io/github/stars/newrelic/newrelic-logs-salesforce-eventlogfile?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/newrelic/newrelic-logs-salesforce-eventlogfile?style=social)

![GitHub all releases](https://img.shields.io/github/downloads/newrelic/newrelic-logs-salesforce-eventlogfile/total)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/newrelic/newrelic-logs-salesforce-eventlogfile)
![GitHub last commit](https://img.shields.io/github/last-commit/newrelic/newrelic-logs-salesforce-eventlogfile)
![GitHub Release Date](https://img.shields.io/github/release-date/newrelic/newrelic-logs-salesforce-eventlogfile)

![GitHub issues](https://img.shields.io/github/issues/newrelic/newrelic-logs-salesforce-eventlogfile)
![GitHub issues closed](https://img.shields.io/github/issues-closed/newrelic/newrelic-logs-salesforce-eventlogfile)
![GitHub pull requests](https://img.shields.io/github/issues-pr/newrelic/newrelic-logs-salesforce-eventlogfile)
![GitHub pull requests closed](https://img.shields.io/github/issues-pr-closed/newrelic/newrelic-logs-salesforce-eventlogfile)

# Salesforce Event Logs integration for NewRelic

*Salesforce Event Logs integration for NewRelic* offers an integration to process and foward Salesforce event log files and events to NewRelic Logs and New Relic Events.
    
## Configuration    

To collect Salesforce event log data, you have to have read access to the Salesforce event log and enable the Salesforce event log file API.    
Create a Salesforce 'Connected App' to use OAuth authentication.

Then fill in the relevant information in the **config.yml** file in the root folder     
  
 1. Update the service parameters 
	 - **run_as_service**:  True or False. True will run this application as a service with an interval cron service on a schedule specified in *service_schedule* parameter. False is useful to setup this application up to be invoked by crontab. The crontab frequency should then be specified using the *cron_interval_minutes* parameter.
	 - **cron_interval_minutes**:  Required only if *run_as_service* is False. If not defined, it will try to read the `CRON_INTERVAL_MINUTES` environment variable.
	 - **service_schedule**: Required only if *run_as_service* is True. The *hour* attribute specifies all the hours (0 - 23, comma separated) to invoke the application to fetch logs. Use * as wildcard to invoke the application every hour. The *minute* attribute specifies all the minutes (0 - 59, comma separated) at which invoke the application to fetch logs. For example { "hour" = "*", "minute" = "0, 15, 30, 45"}  will fetch logs every hour on the hour as well as the 15 minute, 30 minute and 45th minute past every hour. 
	
 2. Update the **instances** section with the *name*, connection  
   *arguments* and *labels* for each salesforce instance from which to fetch event logs files.  
     
	- **token_url**: The salesforce url to authenticate and obtain an *oauth access_token* and *sfdc_instance_url* for further queries  
	- **auth**: (optional) Provide the oauth application credentials to use for authentication. See [Authentication](#authentication) section below.
	- **auth_env_prefix**: (optional) Adds a prefix to the environment variables used to obtain [authentication](#authentication) credentials.
	- **cache_enabled**: True or False. If True, you must provide a redis server to cache all log file ids and message ids processed by this application. This allows the application to perform log message deduplication so that previously processed logs are skipped.
	- **redis**: (optional). Required only when cache_enabled is True. See [Redis](#redis) section below.
	- **date_field**: The date to use in salesforce query for fetching event log files. It can be *LogDate* or *CreatedDate*. See note below regarding best practice on setting this field.
	- **generation_interval**: The frequency at which salesforce is configured to generate log files. It can be "Hourly" or "Daily".
	- **time_lag_minutes**: A time lag to use when this application queries salesforce for event log files. See note below regarding best practice on setting this field.

	**Note about cache_enabled, date_field and time_lag_minutes arguments**
	
	If a *redis cache* is not enabled and thereby disabling log message deduplication, we want to download and process every log file only *once* but with a lag to ensure we are picking most message for occured in that time period. So in this case, it is best to use *LogDate* as the date_field to use in queries and setup a lag of 3 - 5 hours (180 - 300 minutes) as that is the time it could take (when the production servers are under load) for most of the generated log messages to be archived by salesforce log service and become available for download through salesforce queries . When a lag is specified, the application requests log activity for an interval in the past rather than current time. On the other hand, if a *redis cache* is enabled, then use *CreatedDate* for use in salesforce log queries and set the lag to 0. In this case, we are going to query for all log files updated with additional log messages since this application last ran (or the cron tab interval) and process them. So the two recommended combinations for this set of arguments are:
  
   - **cache_enabled**=false, **date_field**=LogDate and **time_lag_minutes**=180  
   - **cache_enabled**=true, **redis**={...}, **date_field**=CreatedDate and **time_lag_minutes**=0  
          
 3. Update the **newrelic** section with
    - **data_format**: `logs` or `events`. Correspondingly Salesforce event log data is formatted and posted to New Relic Logs API or Events API endpoints
    - **api_endpoint**: `US` or `EU` or the full api endpoint URL for the chosen data_format collector endpoint
    - **account_id**: (optional, see [Authentication](#authentication)) Required only when `data_format` is `events`
    - **license_key**: (optional, see [Authentication](#authentication)) New Relic account license key

Check `config.yml.sample` for a configuration example.

## Authentication

This integration supports the OAuth 2.0 Username Password and OAuth 2.0 JWT Bearer Token methods of authentication. The JWT Bearer flow is strongly recommended as it does not expose any passwords.

For OAuth 2.0 Username Password Flow, the auth section template is:

```yaml
auth: {
    "grant_type": "password",
    "client_id": "...",
    "client_secret": "...",
    "username": "...",
    "password": "..."
}
```

For OAuth 2.0 JWT Bearer Flow, the auth section template is:

```yaml
auth: {
    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
    "client_id": "...",
    "private_key": "path/to/private_key_file",
    "subject": "...",
    "audience": "..."
}
```

Alternatively, authentication credentials can be set as environment variables.

The following variable names are used for OAuth 2.0 Username Password Flow:

```
SF_GRANT_TYPE
SF_CLIENT_ID
SF_CLIENT_SECRET
SF_USERNAME
SF_PASSWORD
```

For OAuth 2.0 JWT Bearer Flow:

```
SF_GRANT_TYPE
SF_CLIENT_ID
SF_PRIVATE_KEY
SF_SUBJECT
SF_AUDIENCE
```

If `auth_env_prefix` is defined in the `config.yml` file, it will be added as a prefix to all the environment variables listed above. This mechanism allows different instances to use different environment variables just by defining a different prefix.

New Relic credentials can also be passed as environment variables. The following variable names are used:

```
NR_LICENSE_KEY
NR_ACCOUNT_ID
```

No prefix is used for these variables, as only one New Relic account is supported.

## Redis

When `cache_enabled` is `True`, we have to set a `redis` section in our `config.yml` file, for each Salesforce instance. This sections looks like:

```yaml
redis: {
    "host": "localhost",
    "port": "6379",
    "db_number": 0,
    "ssl": True,
    "password": "...",
    "expire_days": 2
}
```

- `host`: redis server address.
- `port`: redis server port.
- `db_number`: database number to be used.
- `ssl`: SSL is enabled or not.
- `password`: password to access the redis server.
- `expire_days`: expiration time in days for the keys created in redis.

The following keys are mandatory: `host`, `port`, and `db_number`. The rest are optional, and the default values are:

- `ssl` = `False`
- `password` = `None`
- `expire_days` = `7`

## Custom queries

This integration provides default queries to obtain logs from Salesforce, but it's also possible to define custom queries using [SOQL](https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql.htm). We do it by defining an array of `queries` in the root of `config.yml`. In the following example we define three custom queries:

```yaml
queries: [
    {
        query: "SELECT Id,EventType,CreatedDate,LogDate,LogFile FROM EventLogFile WHERE CreatedDate>={from_timestamp} AND EventType='API' AND Interval='{log_interval_type}'",
    },
    {
        query: "SELECT Id,Action,CreatedDate,DelegateUser,Display FROM SetupAuditTrail WHERE CreatedDate>={from_timestamp}",
        timestamp_attr: CreatedData,
        api_ver: "58.0"
    },
]
```

Each custom query is encapsulated in an object with a set of optional config keys:

- `api_ver`: Salesforce API version to use. Default `52.0`.
- `event_type`: New Relic event type to record. Default, the event type reported in the response.
- `timestamp_attr`: Attribute top use as timestamp from the SF response. Default `CreatedDate`. Ignored for `EventLogFile` queries.
- `rename_timestamp`: If present, the New Relic timestamp attribute will be renamed, from `timestamp` to the provided name. The default timestamp will be left empty and will become the time of ingestion.

The `query` field can contain substitution variables, in the form `{VARIABLE_NAME}`:

- `from_timestamp`: initial time in the time range.
- `to_timestamp`: final time in the time range.
- `log_interval_type`: either 'Hourly' or 'Daily', from `generation_interval` in the `config.yml` file.

Queries for `EventLogFile` requiere the following fields to be present:

- `Id`
- `EventType`
- `CreatedDate`
- `LogDate`
- `LogFile`

For queries of other event types there is no minimum set of attributes requiered, but a unique identifier is requiered to be able to store the events on Redis (when `cache_enabled` is `True`). If the `Id` field is present, it will be used. Otherwise it will check for the id key in the query environment config:

```yaml
queries: [
    {
        query: "SELECT EventName, EventType, UsageType, Client, Value, StartDate, EndDate FROM PlatformEventUsageMetric ...",
        id: ["Client", "Value", "StartDate", "EndDate"]
    }
]
```

In this case, the integration will combine the fields `Client`, `Value`, `StartDate`, and `EndDate` to form a unique identifier for each event of the type `PlatformEventUsageMetric`.

### Query env

It's possible to define a set of environment variables for a specific query, we do it by setting the key `env`:

```yaml
queries: [
    {
        query: "SELECT EventName, EventType, UsageType, Client, Value, StartDate, EndDate FROM PlatformEventUsageMetric WHERE TimeSegment='FifteenMinutes' AND StartDate >= {start_date} AND EndDate <= {end_date}",
        env: {
            end_date: "now()",
            start_date: "now(timedelta(minutes=-60))"
        },
    }
]
```

In this example above we defined two variables: `end_date` and `start_date`. These variables contain python expressions that are evaluated to generate the data that is going to be susbtituted in the query. The following elements are supported:

- `now()`: Get current time and generate an ISO formatted date-time. It can optionally take a timedelta as argument and add it to the current time.
- `timedelta`: Generate a Python timedelta object.
- `datetime`: Generate a Python datetime object.
- `sf_time()`: Generate an ISO formatted date-time. Takes a Python datetime object as argument.

## Usage

### Locally

1. Run `pip install -r requirements.txt` to install dependencies
2. Run `python src/__main__.py` to run the integration

### Docker

1. Run `docker build -t nr-sf-eventlogs .` to build the docker image.
2. Run `docker run nr-sf-eventlogs` to run the integration.

## Contributing

We encourage your contributions to improve NR-SF-EventLogs! Keep in mind when you submit your pull request, you'll need to sign the CLA via the click-through using CLA-Assistant. You only have to sign the CLA one time per project. If you have any questions, or to execute our corporate CLA, required if your contribution is on behalf of a company, please drop us an email at opensource@newrelic.com.    
    
**A note about vulnerabilities**

As noted in our [security policy](../../security/policy), New Relic is committed to the privacy and security of our customers and their data. We believe that providing coordinated disclosure by security researchers and engaging with the security community are important means to achieve our security goals.    
    
If you believe you have found a security vulnerability in this project or any of New Relic's products or websites, we welcome and greatly appreciate you reporting it to New Relic through [HackerOne](https://hackerone.com/newrelic).    

## License

*Salesforce Event Logs integration for NewRelic Logs* is licensed under the [Apache 2.0](http://apache.org/licenses/LICENSE-2.0.txt) License.    
    
*Salesforce Event Logs integration for NewRelic Logs* also uses source code from third-party libraries. You can find full details on which libraries are used and the terms under which they are licensed in the third-party notices document.
