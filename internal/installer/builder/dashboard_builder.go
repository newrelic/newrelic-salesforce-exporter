package builder

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
)

func BuildDashboards(userSelection *UserSelection, dashboardsPath string) error {
	for _, eventGroup := range userSelection.Groups {
		var dashboardFile string
		switch eventGroup {
		case UserAccess:
			dashboardFile = "sfdc_user_access.json"
		case ApexUsage:
			dashboardFile = "sfdc_apex_usage.json"
		case LightningUsage:
			dashboardFile = "sfdc_lightning_usage.json"
		case ApiAccess:
			dashboardFile = "sfdc_api_access.json"
		case ReportAccess:
			dashboardFile = "sfdc_report_access.json"
		case DocContentDbAccess:
			dashboardFile = "sfdc_docdb_access.json"
		case WaveUsage:
			dashboardFile = "sfdc_wave_usage.json"
		case ErrPermViol:
			dashboardFile = "sfdc_err_perm_viol.json"
		case AlertSecurity:
			dashboardFile = "sfdc_sec_alerts.json"
		default:
			return fmt.Errorf("Unknown event group")
		}

		err := processDashboard(dashboardFile, userSelection.NewRelic.AccountId, dashboardsPath)
		if err != nil {
			return err
		}
	}

	// Org Limits dashboard
	err := processDashboard("sfdc_org_limits.json", userSelection.NewRelic.AccountId, dashboardsPath)
	if err != nil {
		return err
	}

	return nil
}

func processDashboard(filename string, accountId string, dashboardsPath string) error {
	accountIdInt, err := strconv.Atoi(accountId)
	if err != nil {
		return err
	}

	path := filepath.Join(dashboardsPath, filename)
	dat, err := os.ReadFile(path)
	if err != nil {
		return err
	}

	var jsonMap map[string]any
	err = json.Unmarshal(dat, &jsonMap)
	if err != nil {
		return err
	}

	jsonMap = setAccountIds(jsonMap, accountIdInt)

	result, err := json.MarshalIndent(jsonMap, "", "    ")
	if err != nil {
		return err
	}

	// Write dashboard

	f, err := os.OpenFile(
		BuildInstallerPath(filename),
		os.O_RDWR|os.O_CREATE|os.O_TRUNC,
		0644,
	)
	if err != nil {
		return err
	}
	_, err = f.WriteString(string(result))
	if err != nil {
		return err
	}
	err = f.Close()
	if err != nil {
		return err
	}

	return nil
}

// Look for "accountIds" keys
func setAccountIds(jsonMap map[string]any, accountId int) map[string]any {
	for key := range jsonMap {
		if key == "accountIds" {
			jsonMap[key] = []int{accountId}
		} else {
			switch v := jsonMap[key].(type) {
			case map[string]any:
				setAccountIds(v, accountId)
			case []any:
				for i := range v {
					nextMap, ok := (v[i]).(map[string]any)
					if ok {
						setAccountIds(nextMap, accountId)
					}
				}
			}
		}
	}
	return jsonMap
}
