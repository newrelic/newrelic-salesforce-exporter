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
