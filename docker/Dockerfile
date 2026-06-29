FROM dhi.io/golang:1.26.4-alpine3.24-dev AS build-stage

WORKDIR /build

COPY go.mod go.sum ./

RUN go mod download

COPY cmd ./cmd
COPY internal ./internal

RUN CGO_ENABLED=0 go build ./cmd/nr-salesforce-eventlog/nr-salesforce-eventlog.go
RUN CGO_ENABLED=0 go build ./cmd/nr-salesforce-stream/nr-salesforce-stream.go

FROM dhi.io/golang:1.26.4-alpine3.24 AS release-stage

WORKDIR /app

COPY --from=build-stage /build/nr-salesforce-eventlog ./
COPY --from=build-stage /build/nr-salesforce-stream ./
