package oauth

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"strings"

	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
)

func AuthWithUserPass(auth config.AuthConfig) (*LoginResponse, error) {
	body := url.Values{}

	body.Set("grant_type", "password")
	body.Set("client_id", auth.UserPass.ClientId)
	body.Set("client_secret", auth.UserPass.ClientSecret)
	body.Set("username", auth.UserPass.Username)
	body.Set("password", auth.UserPass.Password)

	ctx, cancelFn := context.WithTimeout(context.Background(), oAuthDialTimeout)
	defer cancelFn()

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, auth.TokenUrl+loginEndpoint, strings.NewReader(body.Encode()))
	if err != nil {
		return nil, err
	}

	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")

	httpResp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, err
	}

	defer httpResp.Body.Close()

	if httpResp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("non-200 status code returned on OAuth authentication call: %v", httpResp.StatusCode)
	}

	var loginResponse LoginResponse
	err = json.NewDecoder(httpResp.Body).Decode(&loginResponse)
	if err != nil {
		return nil, err
	}

	return &loginResponse, nil
}