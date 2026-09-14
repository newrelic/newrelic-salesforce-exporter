module github.com/newrelic/newrelic-salesforce-exporter

go 1.25.3

require (
	github.com/charmbracelet/lipgloss v1.1.0
	github.com/go-viper/mapstructure/v2 v2.5.0
	github.com/linkedin/goavro/v2 v2.15.0
	github.com/redis/go-redis/v9 v9.21.0
	github.com/spf13/viper v1.21.0
	google.golang.org/grpc v1.83.1
	google.golang.org/protobuf v1.36.11
	gopkg.in/yaml.v3 v3.0.1
)

require (
	github.com/atotto/clipboard v0.1.4 // indirect
	github.com/aymanbagabas/go-osc52/v2 v2.0.1 // indirect
	github.com/cespare/xxhash/v2 v2.3.0 // indirect
	github.com/charmbracelet/colorprofile v0.4.3 // indirect
	github.com/charmbracelet/x/ansi v0.11.7 // indirect
	github.com/charmbracelet/x/cellbuf v0.0.15 // indirect
	github.com/charmbracelet/x/term v0.2.2 // indirect
	github.com/clipperhouse/displaywidth v0.11.0 // indirect
	github.com/clipperhouse/uax29/v2 v2.7.0 // indirect
	github.com/davecgh/go-spew v1.1.2-0.20180830191138-d8f796af33cc // indirect
	github.com/erikgeiser/coninput v0.0.0-20211004153227-1c3628e74d0f // indirect
	github.com/fsnotify/fsnotify v1.10.1 // indirect
	github.com/go-co-op/gocron/v2 v2.21.2 // indirect
	github.com/google/go-querystring v1.2.0 // indirect
	github.com/google/uuid v1.6.0 // indirect
	github.com/hashicorp/go-cleanhttp v0.5.2 // indirect
	github.com/hashicorp/go-retryablehttp v0.7.8 // indirect
	github.com/imdario/mergo v0.3.16 // indirect
	github.com/jonboulle/clockwork v0.5.0 // indirect
	github.com/lucasb-eyer/go-colorful v1.4.0 // indirect
	github.com/mattn/go-isatty v0.0.22 // indirect
	github.com/mattn/go-localereader v0.0.1 // indirect
	github.com/mattn/go-runewidth v0.0.24 // indirect
	github.com/muesli/ansi v0.0.0-20230316100256-276c6243b2f6 // indirect
	github.com/muesli/cancelreader v0.2.2 // indirect
	github.com/muesli/termenv v0.16.0 // indirect
	github.com/newrelic/go-agent/v3 v3.44.1 // indirect
	github.com/newrelic/go-agent/v3/integrations/logcontext-v2/nrlogrus v1.1.4 // indirect
	github.com/newrelic/infra-integrations-sdk/v4 v4.2.1 // indirect
	github.com/newrelic/infrastructure-agent v1.67.3 // indirect
	github.com/newrelic/newrelic-client-go/v2 v2.93.2 // indirect
	github.com/pelletier/go-toml/v2 v2.4.2 // indirect
	github.com/pmezard/go-difflib v1.0.1-0.20181226105442-5d4384ee4fb2 // indirect
	github.com/rivo/uniseg v0.4.7 // indirect
	github.com/robertkrimen/otto v0.5.1 // indirect
	github.com/robfig/cron/v3 v3.0.1 // indirect
	github.com/sagikazarmark/locafero v0.12.0 // indirect
	github.com/sirupsen/logrus v1.9.4 // indirect
	github.com/spf13/afero v1.15.0 // indirect
	github.com/spf13/cast v1.10.0 // indirect
	github.com/spf13/pflag v1.0.10 // indirect
	github.com/stretchr/testify v1.11.1 // indirect
	github.com/subosito/gotenv v1.6.0 // indirect
	github.com/tomnomnom/linkheader v0.0.0-20250811210735-e5fe3b51442e // indirect
	github.com/valyala/fastjson v1.6.10 // indirect
	github.com/xo/terminfo v0.0.0-20220910002029-abceb7e1c41e // indirect
	go.uber.org/atomic v1.11.0 // indirect
	go.yaml.in/yaml/v3 v3.0.4 // indirect
	gopkg.in/sourcemap.v1 v1.0.5 // indirect
)

require (
	github.com/charmbracelet/bubbles v1.0.0
	github.com/charmbracelet/bubbletea v1.3.10
	github.com/golang-jwt/jwt/v5 v5.3.1
	github.com/golang/snappy v1.0.0 // indirect
	github.com/newrelic/newrelic-labs-sdk/v2 v2.4.0
	golang.org/x/net v0.56.0 // indirect
	golang.org/x/sys v0.46.0 // indirect
	golang.org/x/text v0.38.0 // indirect
	google.golang.org/genproto/googleapis/rpc v0.0.0-20260622175928-b703f567277d // indirect
)

// Dev env newrelic-labs-sdk
//replace github.com/newrelic/newrelic-labs-sdk/v2 => ../newrelic-labs-sdk
