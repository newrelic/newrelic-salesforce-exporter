package builder

import "path/filepath"

func installerPath() string {
	return filepath.Join(".", "installer_output")
}

func buildInstallerPath(file string) string {
	path := filepath.Join(".", "installer_output")
	return filepath.Join(path, file)
}