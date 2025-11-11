package main

import (
	"fmt"
	"os"

	"github.com/newrelic/newrelic-salesforce-exporter/cmd/installer-tool/components"
	"github.com/newrelic/newrelic-salesforce-exporter/cmd/installer-tool/components/checkerlist"
	"github.com/newrelic/newrelic-salesforce-exporter/cmd/installer-tool/components/selectoption"
	"github.com/newrelic/newrelic-salesforce-exporter/cmd/installer-tool/components/textinput"
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
		"(*) This group requires rolling out a separate data collector, the EventStream.",
	}
	return checkerlist.CheckerList(choices, title, footer)
}

type RunMode = int

const (
    ServiceMode RunMode = iota
    CronLikeMode
)

const (
	ServiceModeDesc = "Service mode"
	CronLikeModeDesc = "Cron-like mode"
)

func runModeMap() map[RunMode]string {
	return map[EventGroup]string{
		ServiceMode: ServiceModeDesc,
		CronLikeMode: CronLikeModeDesc,
	}
}

func selectRunMode() (RunMode, error) {
	choices := runModeMap()
	title := "Select the run mode for the integration"
	footer := []string{
		"NOTE: this only affects the EventLog integration, the EventStream always runs in service mode.",
	}
	return selectoption.SelectList(choices, title, footer)
}

func main() {
	fmt.Printf("\n")
	
	selectedEventGroups, err := selectEventGroups()
	if err != nil {
		fmt.Printf("\n%s\n", err.Error())
        os.Exit(1)
	}
	choices := choiceMap()

	fmt.Printf("\n")

	runMode, err := selectRunMode()
	if err != nil {
		fmt.Printf("\n%s\n", err.Error())
        os.Exit(1)
	}

	fmt.Printf("\n")

	fmt.Print(components.Title("Introduce New Relic API credentials", nil).String())
	nrAccountId, err := textinput.TextInput("Account ID")
	if err != nil {
		fmt.Printf("\n%s\n", err.Error())
        os.Exit(1)
	}
	nrApiKey, err := textinput.TextInput("API Key")
	if err != nil {
		fmt.Printf("\n%s\n", err.Error())
        os.Exit(1)
	}
	nrRegion, err := textinput.TextInput("Region (US/EU)")
	if err != nil {
		fmt.Printf("\n%s\n", err.Error())
        os.Exit(1)
	}

	fmt.Printf("\n")

	fmt.Print(components.Title("Introduce Salesforce API credentials", nil).String())
	sfdcTokenUrl, err := textinput.TextInput("Token URL")
	if err != nil {
		fmt.Printf("\n%s\n", err.Error())
        os.Exit(1)
	}
	sfdcClientId, err := textinput.TextInput("Client ID")
	if err != nil {
		fmt.Printf("\n%s\n", err.Error())
        os.Exit(1)
	}
	sfdcClientSecret, err := textinput.TextInput("Client Secret")
	if err != nil {
		fmt.Printf("\n%s\n", err.Error())
        os.Exit(1)
	}
	sfdcUsername, err := textinput.TextInput("Username")
	if err != nil {
		fmt.Printf("\n%s\n", err.Error())
        os.Exit(1)
	}
	sfdcPass, err := textinput.TextInput("Password")
	if err != nil {
		fmt.Printf("\n%s\n", err.Error())
        os.Exit(1)
	}

	// TODO: Results
	fmt.Printf("\n\n-----------------------------\n\n")

	fmt.Printf("Selected event groups:\n")
	for _,i := range selectedEventGroups {
		fmt.Printf("- %s\n", choices[i])
	}

	fmt.Printf("Selected run mode: %s\n", runModeMap()[runMode])

	fmt.Printf("AccountID: %s\n", nrAccountId)
	fmt.Printf("APIKey: %s\n", nrApiKey)
	fmt.Printf("Region: %s\n", nrRegion)

	fmt.Printf("Toke URL: %s\n", sfdcTokenUrl)
	fmt.Printf("Client ID: %s\n", sfdcClientId)
	fmt.Printf("Client Secret: %s\n", sfdcClientSecret)
	fmt.Printf("Username: %s\n", sfdcUsername)
	fmt.Printf("Password: %s\n", sfdcPass)
}