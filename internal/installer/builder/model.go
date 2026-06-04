package builder

type EventGroup = int

const (
	UserAccess EventGroup = iota
	ApexUsage
	LightningUsage
	ApiAccess
	ReportAccess
	DocContentDbAccess
	WaveUsage
	ErrPermViol
	AlertSecurity
)

type RunMode = int

const (
	ServiceMode RunMode = iota
	CronLikeMode
)

type NewRelicConf struct {
	AccountId string
	ApiKey    string
	Region    string
}

// TODO: add auth methods
type SalesforceConf struct {
	TokenUrl     string
	ClientId     string
	ClientSecret string
	Username     string
	Password     string
}

type RedisConf struct {
	Host     string
	Port     int
	DbNum    int
	Password string
}

type UserSelection struct {
	Groups     []EventGroup
	RunMode    RunMode
	NewRelic   NewRelicConf
	Salesforce SalesforceConf
	Redis      *RedisConf
}

type UserPass struct {
	ClientId     string `yaml:"clientId"`
	ClientSecret string `yaml:"clientSecret"`
	Username     string `yaml:"username"`
	Password     string `yaml:"password"`
}

type Auth struct {
	TokenUrl string `yaml:"tokenUrl"`
	//TODO: add jwt and userCred
	UserPass UserPass `yaml:"userPass"`
}

type RedisCache struct {
	Host       string `yaml:"host"`
	Port       int    `yaml:"port"`
	DbNumber   int    `yaml:"dbNumber"`
	Password   string `yaml:"password"`
	ExpireDays int    `yaml:"expireDays"`
}

type Cache struct {
	Redis *RedisCache `yaml:"redis,omitempty"`
}

type EventLog struct {
	InstanceName string   `yaml:"instanceName"`
	ApiVer       string   `yaml:"apiVer"`
	Auth         Auth     `yaml:"auth"`
	Cache        *Cache   `yaml:"cache,omitempty"`
	EventTypes   []string `yaml:"eventTypes,omitempty"`
}

type EventLogConfigFileModel struct {
	Version      string   `yaml:"version"`
	EventLog     EventLog `yaml:"eventLog"`
	RunAsService bool     `yaml:"runAsService"`
	LicenseKey   string   `yaml:"licenseKey"`
	AccountId    string   `yaml:"accountId"`
	Region       string   `yaml:"region"`
	Format       string   `yaml:"format"`
}

type EventStream struct {
	InstanceName string   `yaml:"instanceName"`
	Auth         Auth     `yaml:"auth"`
	Cache        *Cache   `yaml:"cache,omitempty"`
	Appetite     int      `yaml:"appetite"`
	Topics       []string `yaml:"topics"`
}

type EventStreamConfigFileModel struct {
	Version     string      `yaml:"version"`
	EventStream EventStream `yaml:"eventStream"`
	LicenseKey  string      `yaml:"licenseKey"`
	AccountId   string      `yaml:"accountId"`
	Region      string      `yaml:"region"`
	Format      string      `yaml:"format"`
}
