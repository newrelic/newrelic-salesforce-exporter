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

func AuthWithClientCred(auth config.AuthConfig) (*AuthResponse, error) {
	body := url.Values{}

	body.Set("grant_type", "client_credentials")
	body.Set("client_id", auth.ClientCred.ClientId)
	body.Set("client_secret", auth.ClientCred.ClientSecret)

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
		return nil, fmt.Errorf("%s", authError(httpResp.Body, httpResp.StatusCode))
	}

	var authResponse AuthResponse
	err = json.NewDecoder(httpResp.Body).Decode(&authResponse)
	if err != nil {
		return nil, err
	}

	return &authResponse, nil
}