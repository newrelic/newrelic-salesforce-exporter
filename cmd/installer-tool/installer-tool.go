package main

import (
	"fmt"
	"os"

	"github.com/newrelic/newrelic-salesforce-exporter/cmd/installer-tool/components"
)

type EventGroup = int

const (
    UserAccess EventGroup = iota
    ApexUsage
    LightningUsage
    ApiAccess
	ReportAccess
	DocContentDbAccess
	WaveUsage
	ErrPermViol
	AlertSecurity
)

const (
	UserAccessDesc = "User Acccess"
	ApexUsageDesc = "Apex usage and performance"
	LightningUsageDesc = "Lightning usage and performance"
	ApiAccessDesc = "API access"
	ReportAccessDesc = "Report access"
	DocContentDbAccessDesc = "Document, Content and Database access"
	WaveUsageDesc = "CRM Analytics (Wave) usage and performance"
	ErrPermViolDesc = "Errors, Permissions and Violations"
	AlertSecurityDesc = "Real-time Alerts and Security Warnings (*)"
)

func choiceMap() map[EventGroup]string {
	return map[EventGroup]string{
		UserAccess: UserAccessDesc,
		ApexUsage: ApexUsageDesc,
		LightningUsage: LightningUsageDesc,
		ApiAccess: ApiAccessDesc,
		ReportAccess: ReportAccessDesc,
		DocContentDbAccess: DocContentDbAccessDesc,
		WaveUsage: WaveUsageDesc,
		ErrPermViol: ErrPermViolDesc,
		AlertSecurity: AlertSecurityDesc,
	}
}

func selectEventGroups() ([]EventGroup, error) {
	choices := choiceMap()
	title := "Select event groups to collect"
	footer := []string{
		"(*) This group requires rolling out a separate data collector and access to the Salesforce Event Stream.",
	}
	return components.CheckerList(choices, title, footer)
}

func main() {
	fmt.Printf("\n")
	selectedEventGroups, err := selectEventGroups()
	if err != nil {
		fmt.Printf("\n%s\n", err.Error())
        os.Exit(1)
	}
	choices := choiceMap()
	fmt.Printf("\nSelected:\n")
	for _,i := range selectedEventGroups {
		fmt.Printf("- %s\n", choices[i])
	}
}