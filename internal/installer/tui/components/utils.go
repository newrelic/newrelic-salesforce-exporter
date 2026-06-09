package components

import (
	"fmt"
	"os"
)

func EndProgram() {
	fmt.Printf("\n\n%s\n", ErrorStyle.Render("Program interrupted. Goodbye."))
	os.Exit(1)
}
