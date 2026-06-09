package builder

import "path/filepath"

func InstallerPath() string {
	return filepath.Join(".", "installer_output")
}

func BuildInstallerPath(file string) string {
	path := filepath.Join(".", "installer_output")
	return filepath.Join(path, file)
}