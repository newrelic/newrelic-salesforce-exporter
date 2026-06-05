package tui

import (
	"fmt"
	"strconv"

	"github.com/newrelic/newrelic-salesforce-exporter/internal/installer/builder"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/installer/tui/components"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/installer/tui/components/checkerlist"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/installer/tui/components/selectoption"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/installer/tui/components/textinput"
)

const (
	UserAccessDesc         = "User acccess"
	ApexUsageDesc          = "Apex usage and performance"
	LightningUsageDesc     = "Lightning usage and performance"
	ApiAccessDesc          = "API access"
	ReportAccessDesc       = "Report access"
	DocContentDbAccessDesc = "Document, Content and Database access"
	WaveUsageDesc          = "CRM Analytics (Wave) usage and performance"
	ErrPermViolDesc        = "Errors, Permissions and Violations"
	AlertSecurityDesc      = "Real-time Alerts and Security Warnings"
)

func eventLogChoiceMap() map[builder.EventGroup]string {
	return map[builder.EventGroup]string{
		builder.UserAccess:         UserAccessDesc,
		builder.ApexUsage:          ApexUsageDesc,
		builder.LightningUsage:     LightningUsageDesc,
		builder.ApiAccess:          ApiAccessDesc,
		builder.ReportAccess:       ReportAccessDesc,
		builder.DocContentDbAccess: DocContentDbAccessDesc,
		builder.WaveUsage:          WaveUsageDesc,
		builder.ErrPermViol:        ErrPermViolDesc,
	}
}

func streamMapIndex(index int) int {
	return index - builder.AlertSecurity
}

func eventStreamChoiceMap() map[builder.EventGroup]string {
	return map[builder.EventGroup]string{
		streamMapIndex(builder.AlertSecurity): AlertSecurityDesc,
	}
}

func selectEventLogGroups() ([]builder.EventGroup, error) {
	choices := eventLogChoiceMap()
	title := "Select Event Log data to collect"
	footer := []string{
		"If empty selection, the integration will collect everything.",
	}
	return checkerlist.CheckerList(choices, title, footer)
}

func selectStreamGroups() ([]builder.EventGroup, error) {
	choices := eventStreamChoiceMap()
	title := "Select Event Stream data to collect"
	return checkerlist.CheckerList(choices, title, []string{})
}

func selectEventGroups() ([]builder.EventGroup, error) {

	selectedEventLogGroups, err := selectEventLogGroups()
	if err != nil {
		return nil, err
	}

	fmt.Printf("\n")

	selectedEventStreamGroups, err := selectStreamGroups()
	if err != nil {
		return nil, err
	}

	// Trick to have eventlog and stream represented in the same array without conflicting indexes
	for index := range selectedEventStreamGroups {
		selectedEventStreamGroups[index] += builder.AlertSecurity
	}

	return append(selectedEventLogGroups, selectedEventStreamGroups...), nil
}

const (
	ServiceModeDesc  = "Service (runs continuously)"
	CronLikeModeDesc = "Cron-like (is executed externally and runs once)"
)

func runModeMap() map[builder.RunMode]string {
	return map[builder.RunMode]string{
		builder.ServiceMode:  ServiceModeDesc,
		builder.CronLikeMode: CronLikeModeDesc,
	}
}

const (
	JwtAuth        = "JWT"
	ClientCredAuth = "Client Credentials"
	UserPassAuth   = "User-Password"
)

func authMethodMap() map[builder.AuthMethod]string {
	return map[builder.AuthMethod]string{
		builder.ClientCred: ClientCredAuth,
		builder.Jwt:        JwtAuth,
		builder.UserPass:   UserPassAuth,
	}
}

func selectRunMode() (builder.RunMode, error) {
	choices := runModeMap()
	title := "Select the run mode for the integration"
	footer := []string{
		"This only affects the EventLog integration,",
		"the EventStream always runs in service mode.",
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

func selectAuthMethod() (builder.AuthMethod, error) {
	choices := authMethodMap()
	title := "Select the Salesforce auth method"
	footer := []string{
		"This will set a placeholder in the config file.",
		"Edit it to set the actual credentials.",
		"The event stream integration only supports the User-Pass auth method.",
	}
	return selectoption.SelectList(choices, title, footer)
}

func Questionnaire() (builder.UserSelection, error) {
	fmt.Printf("\n")

	selectedEventGroups, err := selectEventGroups()
	if err != nil {
		return builder.UserSelection{}, err
	}

	fmt.Printf("\n")

	runMode, err := selectRunMode()
	if err != nil {
		return builder.UserSelection{}, err
	}

	fmt.Printf("\n")

	cacheSelection, err := selectCache()
	if err != nil {
		return builder.UserSelection{}, err
	}

	var (
		cacheHost    string
		cachePort    int
		cacheDbNum   int
		cachePass    string
		cacheEnabled = (cacheSelection == 0)
	)

	if cacheEnabled {
		fmt.Printf("\n")

		cacheHost, err = textinput.TextInput("Redis host", "")
		if err != nil {
			return builder.UserSelection{}, err
		}
		for {
			port, err := textinput.TextInput("Redis port", "6379")
			if err != nil {
				return builder.UserSelection{}, err
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
				return builder.UserSelection{}, err
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
			return builder.UserSelection{}, err
		}
	}

	fmt.Printf("\n")

	fmt.Print(components.Title("Introduce New Relic API credentials", nil).String())
	nrAccountId, err := textinput.TextInput("Account ID", "")
	if err != nil {
		return builder.UserSelection{}, err
	}
	var nrRegion string
	for {
		nrRegion, err = textinput.TextInput("Region (US/EU)", "US")
		if err != nil {
			return builder.UserSelection{}, err
		}
		if nrRegion != "EU" && nrRegion != "US" {
			//error, bad values
			components.PrintError("Region must be US or EU.")
			continue
		}
		break
	}

	fmt.Printf("\n")

	fmt.Println(components.BlurredStyle.Render("This will set a placeholder for the License Key in the config file,"))
	fmt.Println(components.BlurredStyle.Render("edit it to set the actual credentials."))

	fmt.Printf("\n")

	fmt.Print(components.Title("Introduce Salesforce API credentials", nil).String())
	sfdcTokenUrl, err := textinput.TextInput("Token URL", "")
	if err != nil {
		return builder.UserSelection{}, err
	}

	fmt.Printf("\n")

	authMethod, err := selectAuthMethod()
	if err != nil {
		return builder.UserSelection{}, err
	}

	// Build user selection

	userSelection := builder.UserSelection{
		Groups:  selectedEventGroups,
		RunMode: runMode,
		NewRelic: builder.NewRelicConf{
			AccountId: nrAccountId,
			Region:    nrRegion,
		},
		Salesforce: builder.SalesforceConf{
			TokenUrl:      sfdcTokenUrl,
			AuthSelection: authMethod,
		},
	}

	if cacheEnabled {
		userSelection.Redis = &builder.RedisConf{
			Host:     cacheHost,
			Port:     cachePort,
			DbNum:    cacheDbNum,
			Password: cachePass,
		}
	}

	return userSelection, nil
}
