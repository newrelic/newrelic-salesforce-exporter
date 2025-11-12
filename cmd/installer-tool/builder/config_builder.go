package builder

import (
	"os"
	"path/filepath"

	"gopkg.in/yaml.v3"
)

func BuildConfig(userSelection UserSelection) error {
	err := setupOutputFolder()
	if err != nil {
		return err
	}

	err = buildEventLogConfig(&userSelection)
	if err != nil {
		return err
	}

	// TODO: build config file for Event Stream integration

	return nil
}

func buildEventLogConfig(userSelection *UserSelection) error {
	eventLogConf := EventLogConfigFileModel{
		Version: "2.0",
		EventLog: EventLog{
			IntegrationName: "com.newrelic.labs.sfdc.eventlog",
			Instances: []Instance{
				{
					Name: "sfdc-instance-1",
					Auth: Auth{
						TokenUrl: userSelection.Salesforce.TokenUrl,
						UserPass: UserPass{
							ClientId: userSelection.Salesforce.ClientId,
							ClientSecret: userSelection.Salesforce.ClientSecret,
							Username: userSelection.Salesforce.Username,
							Password: userSelection.Salesforce.Password,
						},
					},
					EventTypes: buildEventTypes(userSelection.Groups),
				},
			},
		},
		RunAsService: userSelection.RunMode == ServiceMode,
		LicenseKey: userSelection.NewRelic.ApiKey,
		AccountId: userSelection.NewRelic.AccountId,
		Region: userSelection.NewRelic.Region,
		Format: "events",
	}

	if userSelection.Redis != nil {
		eventLogConf.EventLog.Instances[0].Cache = &Cache{
			Redis: &RedisCache{
				Host: userSelection.Redis.Host,
				Port: userSelection.Redis.Port,
				DbNumber: userSelection.Redis.DbNum,
				Password: userSelection.Redis.Password,
				ExpireDays: 1,
			},
		}
	}

	eventLogConfYaml, err := yaml.Marshal(&eventLogConf)
	if err != nil {
		return err
	}

	//fmt.Printf("Resulting conf:\n%s", string(eventLogConfYaml))

	eventLogConfFile, err := os.OpenFile(
		"./installer_output/config_eventlog.yml",
		os.O_RDWR|os.O_CREATE|os.O_TRUNC,
		0755,
	)
    if err != nil {
        return err
    }
	_, err = eventLogConfFile.WriteString(string(eventLogConfYaml))
	if err != nil {
        return err
    }
	err = eventLogConfFile.Close()
	if err != nil {
        return err
    }

	return nil
}

func buildEventTypes(eventGroups []EventGroup) []string {
	eventTypes := []string{}
	for _, eventId := range eventGroups {
		switch eventId {
		case UserAccess:
			eventTypes = append(eventTypes,
				"Login",
				"LoginAs",
				"Logout",
			)
		case ApexUsage:
			eventTypes = append(eventTypes,
				"ApexCallout",
				"ApexExecution",
				"ApexRestApi",
				"ApexSoap",
				"ApexTrigger",
				"ApexUnexpectedException",
				"AuraRequest",
				"ConcurrentLongRunningApexLimit",
				"ExternalCustomApexCallout",
				"NamedCredential",
			)
		// TODO: implement all groups
		default:
			panic("Event group not implemented yet")
		}
	}
	return eventTypes
}

func setupOutputFolder() error {
	newpath := filepath.Join(".", "installer_output")
	os.MkdirAll(newpath, os.ModePerm)
	f, err := os.OpenFile("./installer_output/.gitignore", os.O_RDWR|os.O_CREATE|os.O_TRUNC, 0755)
    if err != nil {
        return err
    }
	f.WriteString("*")
	f.Close()
	return nil
}