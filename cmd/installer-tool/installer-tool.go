package main

import (
	"fmt"

	"github.com/newrelic/newrelic-salesforce-exporter/cmd/installer-tool/components"
)

func main() {
	choices := []string{
		"User Acccess",
		"Apex usage and performance",
		"Lightning usage and performance",
		"API access",
		"Report access",
		"Document, Content and Database access",
		"CRM Analytics (Wave) usage and performance",
		"Errors, Permissions and Violations",
		"Real-time Alerts and Security Warnings (*)",
	}
	title := "Select event groups to collect"
	footer := []string{
		"(*) This group requires rolling out a separate data collector and access to the Salesforce Event Stream.",
	}

	checked := components.CheckerList(choices, title, footer)
	fmt.Printf("\nSelected:\n")
	for i := range checked {
		fmt.Printf("- %s\n", choices[checked[i]])
	}
}