package main

import (
	"fmt"
	"os"

	"github.com/newrelic/newrelic-salesforce-exporter/cmd/installer-tool/builder"
	"github.com/newrelic/newrelic-salesforce-exporter/cmd/installer-tool/tui"
	"github.com/newrelic/newrelic-salesforce-exporter/cmd/installer-tool/tui/components"
)

func main() {
	userSelection, err := tui.Questionnaire()
	if err != nil {
		fmt.Printf("Error in questionnaire: %s", err)
		os.Exit(1)
	}

	err = builder.BuildConfig(userSelection)
	if err != nil {
		fmt.Printf("Error building config: %s", err)
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