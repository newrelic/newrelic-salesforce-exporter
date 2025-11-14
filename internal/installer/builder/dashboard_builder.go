package builder

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
)

func BuildDashboards(userSelection *UserSelection) error {
	for _, eventGroup := range userSelection.Groups {
		switch eventGroup {
		case UserAccess:
			err := processDashboard("sfdc_user_access.json", userSelection.NewRelic.AccountId)
			if err != nil {
				return err
			}
		case ApexUsage:
			err := processDashboard("sfdc_apex_usage.json", userSelection.NewRelic.AccountId)
			if err != nil {
				return err
			}
		case LightningUsage:
			return fmt.Errorf("TODO: LightningUsage dashboard")
		case ApiAccess:
			return fmt.Errorf("TODO: ApiAccess dashboard")
		case ReportAccess:
			return fmt.Errorf("TODO: ReportAccess dashboard")
		case DocContentDbAccess:
			return fmt.Errorf("TODO: DocContentDbAccess dashboard")
		case WaveUsage:
			return fmt.Errorf("TODO: WaveUsage dashboard")
		case ErrPermViol:
			return fmt.Errorf("TODO: ErrPermViol dashboard")
		default:
			return fmt.Errorf("Unknown event group")
		}
	}
	
	return nil
}

func processDashboard(filename string, accountId string) error {
	accountIdInt, err := strconv.Atoi(accountId)
    if err != nil {
        return err
    }

	path := filepath.Join("dashboards", "installer", filename)
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

	//TODO: write to file
	fmt.Printf("Result json:\n%s", string(result))

	return nil
}

// Look for "accountIds" keys
func setAccountIds(jsonMap map[string]any, accountId int) map[string]any {
	for key := range jsonMap {
    	if key == "accountIds" {
			jsonMap[key] = []int { accountId }
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