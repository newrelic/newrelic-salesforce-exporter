## Run

From the repo root folder, run:

```bash
go run cmd/installer-tool/installer-tool.go 
```

Follow the installer instruction.

Once finished, the output fill be udnerf the `installer_output` folder, in the repo
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
