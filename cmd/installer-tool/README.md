# Installer Tool

**WORK IN PROGRESS**

- [x] UI and questionnaire.
- [x] Build dockerfiles for both integrations.
- [x] Build config files for both integrations.
- [x] Build New Relic dashboard for Apex usage.
- [x] Build New Relic dashboard for API access.
- [x] Build New Relic dashboard for Lightning usage.
- [x] Build New Relic dashboard for User access.
- [x] Build New Relic dashboard for Report access.
- [x] Build New Relic dashboard for Doc content and DB access.
- [x] Build New Relic dashboard for Wave usage.
- [x] Build New Relic dashboard for Errors, Permissions and Violations.
- [x] Build New Relic dashboard for Security and Alerts.

## Run

From the repo root folder, run:

```bash
go run cmd/installer-tool/installer-tool.go 
```

Follow the installer instruction.

Once finished, the output fill be under the `installer_output` folder, in the repo
root. It contains the config files for the integrations and the dockerfiles to
build the docker images.

## Docker

To build the docker image for the EventLog integration:

```bash
docker build -t newrelic/sfdc-eventlog:v1 -f installer_output/Dockerfile.eventlog .
```

To build the docker image for the EventStream integration:

```bash
docker build -t newrelic/sfdc-eventstream:v1 -f installer_output/Dockerfile.eventstream .
```
