package main

import (
	"fmt"
	"os"
	"strconv"

	"github.com/newrelic/newrelic-salesforce-exporter/cmd/installer-tool/builder"
	"github.com/newrelic/newrelic-salesforce-exporter/cmd/installer-tool/components"
	"github.com/newrelic/newrelic-salesforce-exporter/cmd/installer-tool/components/checkerlist"
	"github.com/newrelic/newrelic-salesforce-exporter/cmd/installer-tool/components/selectoption"
	"github.com/newrelic/newrelic-salesforce-exporter/cmd/installer-tool/components/textinput"
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

func choiceMap() map[builder.EventGroup]string {
	return map[builder.EventGroup]string{
		builder.UserAccess: UserAccessDesc,
		builder.ApexUsage: ApexUsageDesc,
		builder.LightningUsage: LightningUsageDesc,
		builder.ApiAccess: ApiAccessDesc,
		builder.ReportAccess: ReportAccessDesc,
		builder.DocContentDbAccess: DocContentDbAccessDesc,
		builder.WaveUsage: WaveUsageDesc,
		builder.ErrPermViol: ErrPermViolDesc,
		builder.AlertSecurity: AlertSecurityDesc,
	}
}

func selectEventGroups() ([]builder.EventGroup, error) {
	choices := choiceMap()
	title := "Select event groups to collect"
	footer := []string{
		"(*) This group requires rolling out a separate data collector, the EventStream.",
		"\nNOTE: If empty selection, the integration will collect everything from Event Logs.",
	}
	return checkerlist.CheckerList(choices, title, footer)
}

const (
	ServiceModeDesc = "Service (runs continuously)"
	CronLikeModeDesc = "Cron-like (is executed externally and runs once)"
)

func runModeMap() map[builder.RunMode]string {
	return map[builder.EventGroup]string{
		builder.ServiceMode: ServiceModeDesc,
		builder.CronLikeMode: CronLikeModeDesc,
	}
}

func selectRunMode() (builder.RunMode, error) {
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

		cacheHost, err = textinput.TextInput("Redis host", "")
		if err != nil {
			fmt.Printf("\n%s\n", err.Error())
			os.Exit(1)
		}
		for {
			port, err := textinput.TextInput("Redis port", "6379")
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
			dbNum, err := textinput.TextInput("Redis DB number", "0")
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

		cachePass, err = textinput.TextInput("Redis password", "")
		if err != nil {
			fmt.Printf("\n%s\n", err.Error())
			os.Exit(1)
		}
	}

	fmt.Printf("\n")

	fmt.Print(components.Title("Introduce New Relic API credentials", nil).String())
	nrAccountId, err := textinput.TextInput("Account ID", "")
	if err != nil {
		fmt.Printf("\n%s\n", err.Error())
        os.Exit(1)
	}
	nrApiKey, err := textinput.TextInput("API Key", "")
	if err != nil {
		fmt.Printf("\n%s\n", err.Error())
        os.Exit(1)
	}
	var nrRegion string
	for {
		nrRegion, err = textinput.TextInput("Region (US/EU)", "US")
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
	sfdcTokenUrl, err := textinput.TextInput("Token URL", "")
	if err != nil {
		fmt.Printf("\n%s\n", err.Error())
        os.Exit(1)
	}
	sfdcClientId, err := textinput.TextInput("Client ID", "")
	if err != nil {
		fmt.Printf("\n%s\n", err.Error())
        os.Exit(1)
	}
	sfdcClientSecret, err := textinput.TextInput("Client Secret", "")
	if err != nil {
		fmt.Printf("\n%s\n", err.Error())
        os.Exit(1)
	}
	sfdcUsername, err := textinput.TextInput("Username", "")
	if err != nil {
		fmt.Printf("\n%s\n", err.Error())
        os.Exit(1)
	}
	sfdcPass, err := textinput.TextInput("Password", "")
	if err != nil {
		fmt.Printf("\n%s\n", err.Error())
        os.Exit(1)
	}

	// Build config
	
	var redisConfig *builder.RedisConf

	if cacheEnabled {
		redisConfig = &builder.RedisConf{
			Host: cacheHost,
			Port: cachePort,
			DbNum: cacheDbNum,
			Password: cachePass,
		}
	}

	err = builder.BuildConfig(builder.UserSelection{
		Groups: selectedEventGroups,
		RunMode: runMode,
		NewRelic: builder.NewRelicConf{
			AccountId: nrAccountId,
			ApiKey: nrApiKey,
			Region: nrRegion,
		},
		Salesforce: builder.SalesforceConf{
			TokenUrl: sfdcTokenUrl,
			ClientId: sfdcClientId,
			ClientSecret: sfdcClientSecret,
			Username: sfdcUsername,
			Password: sfdcPass,
		},
		Redis: redisConfig,
	})

	if err != nil {
		fmt.Printf("Error: %s", err)
		os.Exit(1)
	}

	fmt.Printf("\n")
	fmt.Print(components.DoneStyle.Render("Done!"))
	fmt.Print(components.NoStyle.MarginLeft(1).Render("Output data written into"))
	fmt.Print(components.NoStyle.MarginLeft(1).Underline(true).Render("'./installer_tool'"))
	fmt.Printf("\n\n")

	//TODO: build docker images

	//TODO: build dashboards
}