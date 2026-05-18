package oauth

import (
	"encoding/json"
	"fmt"
	"io"
	"time"

	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
)

const (
	oAuthDialTimeout = 5 * time.Second
	loginEndpoint    = "/services/oauth2/token"
)

type AuthResponse struct {
	AccessToken string `json:"access_token"`
	InstanceURL string `json:"instance_url"`
	ID          string `json:"id"`
	TokenType   string `json:"token_type"`
	// Other fields are flow-dependant
}

func Login(auth config.AuthConfig) (*AuthResponse, error) {
	if auth.Jwt != nil {
		return AuthWithJwt(auth.TokenUrl, auth.Jwt)
	} else if auth.ClientCred != nil {
		return AuthWithClientCred(auth.TokenUrl, auth.ClientCred)
	} else if auth.UserPass != nil {
		return AuthWithUserPass(auth.TokenUrl, auth.UserPass)
	} else {
		return nil, fmt.Errorf("Auth config missing")
	}
}

type authErrorResponse struct {
	Error            string `json:"error"`
	ErrorDescription string `json:"error_description"`
}

func authError(body io.ReadCloser, statusCode int) string {
	var authErr authErrorResponse
	err := json.NewDecoder(body).Decode(&authErr)
	var reason string
	if err == nil {
		reason = fmt.Sprintf("'%s' : '%s'", authErr.Error, authErr.ErrorDescription)
	} else {
		reason = "unknown"
	}
	return fmt.Sprintf("OAuth error (status code %d): %s", statusCode, reason)
}
