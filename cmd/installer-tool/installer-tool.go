package main

import (
	"fmt"

	"github.com/newrelic/newrelic-salesforce-exporter/cmd/installer-tool/components"
)

func main() {
	checked := components.CheckerList()
	fmt.Printf("\n\nSelected:\n")
	for i := range checked {
		fmt.Printf("- %s\n", checked[i])
	}
}