package eventlog

import (
	"context"

	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/log"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/model"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/pipeline"
)

type SalesforceEventsReceiver struct {
	i *integration.LabsIntegration
}

func (s *SalesforceEventsReceiver) GetId() string {
	return "salesforce-events-receiver"
}

func (s *SalesforceEventsReceiver) PollEvents(context context.Context, writer chan <- model.Event) error {
	//TODO: send events
	log.Debugf("-----> PollEvents")
	return nil	
}

func NewSalesforceEventsReceiver(i *integration.LabsIntegration) (pipeline.EventsReceiver, error) {
	return &SalesforceEventsReceiver{
		i: i,
	}, nil
}