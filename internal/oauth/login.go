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
	IssuedAt    string `json:"issued_at"`
	Signature   string `json:"signature"`
}

func Login(auth config.AuthConfig) (*LoginResponse, error) {
	if auth.UserPass != nil {
		return AuthWithUserPass(auth)
	} else {
		return nil, fmt.Errorf("Auth config missing")
	}
}
