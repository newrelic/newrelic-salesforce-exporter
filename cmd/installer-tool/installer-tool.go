package main

import (
	"fmt"
	"os"

	"github.com/newrelic/newrelic-salesforce-exporter/internal/installer/builder"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/installer/tui"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/installer/tui/components"
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

	err = builder.BuildDocker()
	if err != nil {
		fmt.Printf("Error building docker files: %s", err)
		os.Exit(1)
	}

	//TODO: build dashboards

	fmt.Printf("\n")
	fmt.Print(components.DoneStyle.Render("Done!"))
	fmt.Print(components.NoStyle.MarginLeft(1).Render("Output data written into"))
	fmt.Print(components.NoStyle.MarginLeft(1).Underline(true).Render("'" + builder.InstallerPath() + "'"))
	fmt.Printf("\n\n")
}