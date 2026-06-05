# Installer Tool

The Installer Tool is a small utility to streamline the installation and setup
process for the Salesforce New Relic Integrations.

Starting with a quick questionnaire that users must answer, it generates config
files to run the integration, Docker files to deploy it, and NROne dashboards
to visualize the data generated. It's designed as a quickstart mechanism,
especially for users unfamiliar with the platform who can struggle setting this
up manually.

<p align="center">
  <img src="./tui-capture.gif">
</p>

## Data groups

The Installer Tool shows data in groups, each one of these groups contain
multiple event types which are read from Salesforce. Each group is associated
with a dashboard, so the tool will generate as many dashboard files as groups
selected. The groups are:

### User access

- [Login](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_login.htm)
- [LoginAs](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_loginas.htm)
- [Logout](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_logout.htm)

### Apex usage and performance

- [ApexCallout](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_apexcallout.htm)
- [ApexExecution](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_apexexecution.htm)
- [ApexRestApi](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_apexrestapi.htm)
- [ApexSoap](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_apexsoap.htm)
- [ApexTrigger](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_apextrigger.htm)
- [ApexUnexpectedException](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_apexunexpectedexception.htm)
- [AuraRequest](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_lightning_component.htm)
- [ConcurrentLongRunningApexLimit](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_concurrentlongrunningapexlimit.htm)
- [ExternalCustomApexCallout](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_externalcustomapexcallout.htm)
- [NamedCredential](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_namedcredential.htm)

### Lightning usage and performance

- [LightningError](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_lightningerror.htm)
- [LightningInteraction](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_lightninginteraction.htm)
- [LightningLogger](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_lightninglogger.htm)
- [LightningPageView](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_lightningpageview.htm)
- [LightningPerformance](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_lightningperformance.htm)
- [VisualforceRequest](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_visualforce.htm)

### API access

- [ApiTotalUsage](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_apitotalusage.htm)
- [BulkApi](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_bulkapi.htm)
- [BulkApiRequest](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_bulkapi_request.htm)
- [BulkApi2](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_bulkapi2.htm)
- [CompositeApi](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_composite_api.htm)
- [CompositeApiSubrequest](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_composite_api_subrequest.htm)
- [MetadataApiOperation](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_metadataapi.htm)
- [RestApi](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_restapi.htm)
- [API](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_api.htm)

### Report access

- [AsynchronousReportRun](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_asyncreportrun.htm)
- [Dashboard](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_dashboard.htm)
- [MultiblockReport](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_multiblock.htm)
- [Report](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_report.htm)
- [ReportExport](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_reportexport.htm)

### Document, Content and Database access

- [DatabaseSave](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_databasesaveevent.htm)
- [UniqueQuery](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_unique_query_event_elf.htm)
- [DocumentAttachmentDownoads](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_documentattach.htm)
- [ContentDocumentLink](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_contentdocument.htm)
- [ContentTransfer](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_contenttransfer.htm)
- [ContentDistribution](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_contentdistribution.htm)

### CRM Analytics (Wave) usage and performance

- [WaveChange](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_wavechange.htm)
- [WaveDownload](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_wavedownload.htm)
- [WaveInteraction](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_waveinteraction.htm)
- [WavePerformance](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_waveperformance.htm)

### Errors, Permissions and Violations

- [CorsViolation](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_cors_violation.htm)
- [CspViolation](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_cspviolation.htm)
- [InsufficientAccess](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_insufficientaccess.htm)
- [PermissionUpdate](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_permissionupdate.htm)
- [InsecureExternalAssets](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_insecureexternalassets.htm)
- [TransactionSecurity](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_transaction.htm)
- [BlockedRedirect](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_blockedredirect.htm)
- [HostnameRedirects](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_hostnameredirects.htm)
- [GroupMembership](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile_groupmembership.htm)

### Org limits

This group is not actually selected during the questionnaire process, it's
captured OOTB. It contains all [resource limits](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_limits.htm).

### Real-time Alerts and Security Warnings

Unlike the other data groups, which are collected by the Event Log
integration, this one is collected by the Event Stream integration.

- [/event/LoginAnomalyEvent](https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/sforce_api_objects_loginanomalyevent.htm)
- [/event/SessionHijackingEvent](https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/sforce_api_objects_sessionhijackingevent.htm)
- [/event/CredentialStuffingEvent](https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/sforce_api_objects_credentialstuffingevent.htm)

## Run

From the repo root folder, run:

```bash
go run cmd/installer-tool/installer-tool.go 
```

Follow the installer instruction.

Once finished, the output fill be under the `installer_output` folder, in the
repo root. It contains the config files for the integrations, the dockerfiles
to build the docker images, and the dashboards in JSON format, ready to be
imported from NROne.

## Docker

To build the docker image for the EventLog integration:

```bash
docker build -t newrelic/sfdc-eventlog:v1 -f installer_output/Dockerfile.eventlog .
```

To build the docker image for the EventStream integration:

```bash
docker build -t newrelic/sfdc-eventstream:v1 -f installer_output/Dockerfile.eventstream .
```
