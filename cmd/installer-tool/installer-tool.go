package main

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/newrelic/newrelic-salesforce-exporter/internal/installer/builder"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/installer/tui"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/installer/tui/components"
)

func main() {
	userSelection, err := tui.Questionnaire()
	if err != nil {
		fmt.Printf("\nError in questionnaire: %s\n", err)
		os.Exit(1)
	}

	fmt.Printf("\n")

	fmt.Print(components.NoStyle.MarginLeft(2).Render("Building config files ..."))
	fmt.Printf("\n")

	err = builder.BuildConfig(&userSelection)
	if err != nil {
		fmt.Printf("\nError building config: %s\n", err)
		os.Exit(1)
	}

	fmt.Print(components.NoStyle.MarginLeft(2).Render("Building docker files ..."))
	fmt.Printf("\n")

	err = builder.BuildDocker(&userSelection)
	if err != nil {
		fmt.Printf("\nError building docker files: %s\n", err)
		os.Exit(1)
	}

	dashboardsPath := filepath.Join("dashboards", "installer")
	fmt.Print(components.NoStyle.MarginLeft(2).Render("Loading dashboard files from"))
	fmt.Print(components.NoStyle.MarginLeft(1).Render("'" + dashboardsPath + "'"))
	fmt.Print(components.NoStyle.MarginLeft(1).Render("..."))
	fmt.Printf("\n")

	err = builder.BuildDashboards(&userSelection, dashboardsPath)
	if err != nil {
		fmt.Printf("\nError building dashboards: %s\n", err)
		os.Exit(1)
	}

	fmt.Printf("\n")
	fmt.Print(components.DoneStyle.Render("Done!"))
	fmt.Print(components.NoStyle.MarginLeft(1).Render("Output data written into"))
	fmt.Print(components.NoStyle.MarginLeft(1).Underline(true).Render("'" + builder.InstallerPath() + "'"))
	fmt.Printf("\n\n")
}
