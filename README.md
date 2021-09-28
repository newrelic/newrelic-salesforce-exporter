  
    
[![New Relic Experimental header](https://github.com/newrelic/opensource-website/raw/master/src/images/categories/Experimental.png)](https://opensource.newrelic.com/oss-category/#new-relic-experimental)    
    
![GitHub forks](https://img.shields.io/github/forks/newrelic-experimental/newrelic-logs-salesforce-eventlogfile?style=social)    
![GitHub stars](https://img.shields.io/github/stars/newrelic-experimental/newrelic-logs-salesforce-eventlogfile?style=social)    
![GitHub watchers](https://img.shields.io/github/watchers/newrelic-experimental/newrelic-logs-salesforce-eventlogfile?style=social)    
    
![GitHub all releases](https://img.shields.io/github/downloads/newrelic-experimental/newrelic-logs-salesforce-eventlogfile/total)    
![GitHub release (latest by date)](https://img.shields.io/github/v/release/newrelic-experimental/newrelic-logs-salesforce-eventlogfile)    
![GitHub last commit](https://img.shields.io/github/last-commit/newrelic-experimental/newrelic-logs-salesforce-eventlogfile)    
![GitHub Release Date](https://img.shields.io/github/release-date/newrelic-experimental/newrelic-logs-salesforce-eventlogfile)    
    
    
![GitHub issues](https://img.shields.io/github/issues/newrelic-experimental/newrelic-logs-salesforce-eventlogfile)    
![GitHub issues closed](https://img.shields.io/github/issues-closed/newrelic-experimental/newrelic-logs-salesforce-eventlogfile)    
![GitHub pull requests](https://img.shields.io/github/issues-pr/newrelic-experimental/newrelic-logs-salesforce-eventlogfile)    
![GitHub pull requests closed](https://img.shields.io/github/issues-pr-closed/newrelic-experimental/newrelic-logs-salesforce-eventlogfile)    
    
# Salesforce Event Logs integration for NewRelic Logs    
 *Salesforce Event Logs integration for NewRelic Logs* offers an integration to process and foward Salesforce event log files to [NewRelic Logs](https://docs.newrelic.com/docs/introduction-new-relic-logs)    
    
## Installation    
    
    
    
 ## Configuration    
 To collect Salesforce event log data, you have to have read access to the Salesforce event log and enable the Salesforce event log file API.    
Create a Salesforce 'Connected App' to use OAuth authentication.    
    
Then fill in the relevant information in the **config.yml** file in the root folder     
  
 1. Update the service parameters 
	 - **run_as_service**:  True or False. True will run this application as a service with an interval cron service on a schedule specified in *service_schedule* parameter. False is useful to setup this application up to be invoked by crontab. The crontab frequency should then be specified using the *cron_interval_minutes* parameter.
	 - **cron_interval_minutes**:  Required only if *run_as_service* is False. 
	 - **service_schedule**: Required only if *run_as_service* is True. The *hour* attribute specifies all the hours (0 - 23, comma separated) to invoke the application to fetch logs. Use * as wildcard to invoke the application every hour. The *minute* attribute specifies all the minutes (0 - 59, comma separated) at which invoke the application to fetch logs. For example { "hour" = "*", "minute" = "0, 15, 30, 45"}  will fetch logs every hour on the hour as well as the 15 minute, 30 minute and 45th minute past every hour. 
	
 2. Update the **instances** section with the *name*, connection  
   *arguments* and *labels* for each salesforce instance from which to fetch event logs files.  
     
	- **token_url**: The salesforce url to authenticate and obtain an *oauth access_token* and *sfdc_instance_url* for further queries  
	- **auth**: Provide the oauth application credentials to use for authentication  
	- **cache_enabled**: True or False. If True, you must provide a redis server to cache all log file ids and message ids processed by this application. This allows the application to perform log message deduplication so that previously processed logs are skipped  
	- **redis**: (optional). Required only when cache_enabled is True  
	- **date_field**: The date to use in salesforce query for fetching event log files. It can be *LogDate* or *CreatedDate*. See note below regarding best practice on setting this field  
	- **generation_interval**: The frequency at which salesforce is configured to generate log files. It can be "Hourly" or "Daily"  
	- **time_lag_minutes**: A time lag to use when this application queries salesforce for event log files. See note below regarding best practice on setting this field  

	**Note about cache_enabled, date_field and time_lag_minutes arguments** If a *redis cache* is not enabled and thereby disabling log message deduplication, we want to download and process every log file only *once* but with a lag to ensure we are picking most message for occured in that time period. So in this case, it is best to use *LogDate* as the date_field to use in queries and setup a lag of 3 - 5 hours (180 - 300 minutes) as that is the time it could take (when the production servers are under load) for most of the generated log messages to be archived by salesforce log service and become available for download through salesforce queries . When a lag is specified, the application requests log activity for an interval in the past rather than current time.   
On the other hand, if a *redis cache* is enabled, then use *CreatedDate* for use in salesforce log queries and set the lag to 0. In this case, we are going to query for all log files updated with additional log messages since this application last ran (or the cron tab interval) and process them.   
So the two recommeded combinations for this set of arguments are  
  
   - **cache_enabled**=false, **date_field**=LogDate and **time_lag_minutes**=180  
   - **cache_enabled**=true, **redis**={...}, **date_field**=CreatedDate and **time_lag_minutes**=0  
          
 3. Update the **newrelic** section with the newrelic log API *http_endpoint* and *license_key*    
    
 ## Usage    
 1. Run  `python -m pip install -r requirements.txt` to install dependencies    
3. Run  `python src/__main__.py` to run the integration    
    
## Support    
 New Relic has open-sourced this project. This project is provided AS-IS WITHOUT WARRANTY OR DEDICATED SUPPORT. Issues and contributions should be reported to the project here on GitHub.    
    
We encourage you to bring your experiences and questions to the [Explorers Hub](https://discuss.newrelic.com) where our community members collaborate on solutions and new ideas.    
    
    
## Contributing    
 We encourage your contributions to improve [Project Name]! Keep in mind when you submit your pull request, you'll need to sign the CLA via the click-through using CLA-Assistant. You only have to sign the CLA one time per project. If you have any questions, or to execute our corporate CLA, required if your contribution is on behalf of a company, please drop us an email at opensource@newrelic.com.    
    
**A note about vulnerabilities**    
 As noted in our [security policy](../../security/policy), New Relic is committed to the privacy and security of our customers and their data. We believe that providing coordinated disclosure by security researchers and engaging with the security community are important means to achieve our security goals.    
    
If you believe you have found a security vulnerability in this project or any of New Relic's products or websites, we welcome and greatly appreciate you reporting it to New Relic through [HackerOne](https://hackerone.com/newrelic).    
    
    
## License    
 *Salesforce Event Logs integration for NewRelic Logs* is licensed under the [Apache 2.0](http://apache.org/licenses/LICENSE-2.0.txt) License.    
    
*Salesforce Event Logs integration for NewRelic Logs* also uses source code from third-party libraries. You can find full details on which libraries are used and the terms under which they are licensed in the third-party notices document.