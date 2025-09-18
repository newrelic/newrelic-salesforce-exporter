package config

import (
	"testing"
)

func rightConfig() Config {
	return Config{
		Version: "2.0",
		IsTemplate: false,
		Format: "events",
	}
}

func TestIntegrityCheck(t *testing.T) {
	config := Config{}
	err := integrityCheck(&config)
	if err == nil {
		t.Errorf("Integrity check didn't catch an empty cache")
	}

	config = rightConfig()
	
	err = integrityCheck(&config)
	if err != nil {
		t.Errorf("Integrity check failed with a correct config")
	}

	config.Format = "logs"
	err = integrityCheck(&config)
	if err != nil {
		t.Errorf("Integrity check failed with a correct config (format = logs)")
	}

	config.Version = "3.0.0"
	err = integrityCheck(&config)
	if err == nil {
		t.Errorf("Integrity check didn't catch a wrong version format (3.0.0)")
	}

	config.Version = "hello"
	err = integrityCheck(&config)
	if err == nil {
		t.Errorf("Integrity check didn't catch a wrong version format (hello)")
	}

	config.Version = "3.0"
	err = integrityCheck(&config)
	if err == nil {
		t.Errorf("Integrity check didn't catch a wrong version value (3.0)")
	}
	
	config = rightConfig()

	config.Format = "hello"
	err = integrityCheck(&config)
	if err == nil {
		t.Errorf("Integrity check didn't catch a wrong data format")
	}

	config = rightConfig()

	config.IsTemplate = true
	err = integrityCheck(&config)
	if err == nil {
		t.Errorf("Integrity check didn't catch the template flag")
	}
}
