package oauth

import (
	"fmt"
	"time"

	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
)

const (
	oAuthDialTimeout = 5 * time.Second
	loginEndpoint    = "/services/oauth2/token"
)

type LoginResponse struct {
	AccessToken string `json:"access_token"`
	InstanceURL string `json:"instance_url"`
	ID          string `json:"id"`
	TokenType   string `json:"token_type"`
	// Other fields are flow-dependant
}

func Login(auth config.AuthConfig) (*LoginResponse, error) {
	if auth.UserPass != nil {
		return AuthWithUserPass(auth)
	} else if auth.Jwt != nil {
		return AuthWithJwt(auth)
	} else {
		return nil, fmt.Errorf("Auth config missing")
	}
}
