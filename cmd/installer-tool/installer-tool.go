package main

import (
	"fmt"
	"os"
	"strconv"

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

func selectCache() (int, error) {
	choices := map[int]string{
		0: "Yes",
		1: "No",
	}
	title := "Do you want to set up a Redis cache (recomended)?"
	return selectoption.SelectList(choices, title, []string{})
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

	cacheSelection, err := selectCache()
	if err != nil {
		fmt.Printf("\n%s\n", err.Error())
        os.Exit(1)
	}

	var (
		cacheHost string
		cachePort int
		cacheDbNum int
		cachePass string
		cacheEnabled = (cacheSelection == 0)
	)

	if cacheEnabled {
		fmt.Printf("\n")

		cacheHost, err = textinput.TextInput("Redis host")
		if err != nil {
			fmt.Printf("\n%s\n", err.Error())
			os.Exit(1)
		}
		for {
			port, err := textinput.TextInput("Redis port")
			if err != nil {
				fmt.Printf("\n%s\n", err.Error())
				os.Exit(1)
			}
			i, err := strconv.Atoi(port)
			if err != nil {
				//error, bad format
				components.PrintError("Port must be a number.")
				continue
			}
			if i < 0 {
				//error, bad range
				components.PrintError("Port must be a positive number.")
				continue
			}
			cachePort = i
			break
		}
		for {
			dbNum, err := textinput.TextInput("Redis DB number")
			if err != nil {
				fmt.Printf("\n%s\n", err.Error())
				os.Exit(1)
			}
			i, err := strconv.Atoi(dbNum)
			if err != nil {
				//error, bad format
				components.PrintError("DB number must be a number.")
				continue
			}
			if i < 0 {
				//error, bad range
				components.PrintError("DB number must be a positive number.")
				continue
			}
			cacheDbNum = i
			break
		}

		cachePass, err = textinput.TextInput("Redis password")
		if err != nil {
			fmt.Printf("\n%s\n", err.Error())
			os.Exit(1)
		}
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
	var nrRegion string
	for {
		nrRegion, err = textinput.TextInput("Region (US/EU)")
		if err != nil {
			fmt.Printf("\n%s\n", err.Error())
			os.Exit(1)
		}
		if nrRegion != "EU" && nrRegion != "US" {
			//error, bad values
			components.PrintError("Region must be US or EU.")
			continue
		}
		break
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
	fmt.Printf("\n\n------------ RESULTS ------------\n\n")

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

	if cacheEnabled {
		fmt.Printf("Cache host: %s\n", cacheHost)
		fmt.Printf("Cache port: %s\n", cachePort)
		fmt.Printf("Cache DB number: %s\n", cacheDbNum)
		fmt.Printf("Cache password: %s\n", cachePass)
	}
}