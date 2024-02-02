# CHANGELOG
All notable changes to this project will be documented in this file.

## [1.0.0] - 2024/02/02
### Add
- Accept arbitrary event log queries.
- Accept queries of any type of event, not only event logs.
- Read credentials and other information from OS env vars.
- Use cache (redis) for events.
- Configurable timestamp attribute.
- Docker image.
- Reuse the token and check for auth error and refresh.
- Create specific set of substitution variables for each query.
- Generate integration telemetry.
- Configure the SF API version to use.
- Configure the NR eventType to report.
- Dynamic SOQL query generation.
- Instrumentation attributes.
### Update
- Improve NR API interaction.
- Improve cache (redis) usage.
- Improve documentation.
### Fix
- Multiple minor bugs.

## [0.1.0] - 2023/05/10
- Initial release.
