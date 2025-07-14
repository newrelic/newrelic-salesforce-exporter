package oauth

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"strings"
	"time"

	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
)

const (
	oAuthDialTimeout = 5 * time.Second
	loginEndpoint    = "/services/oauth2/token"
	userInfoEndpoint = "/services/oauth2/userinfo"
)

var (
	// OAuth credentials
	grantType     string
	clientId      string
	clientSecret  string
	username      string
	password      string
	tokenEndpoint string
)

type LoginResponse struct {
	AccessToken string `json:"access_token"`
	InstanceURL string `json:"instance_url"`
	ID          string `json:"id"`
	TokenType   string `json:"token_type"`
	IssuedAt    string `json:"issued_at"`
	Signature   string `json:"signature"`
}

type UserInfoResponse struct {
	UserID         string `json:"user_id"`
	OrganizationID string `json:"organization_id"`
}

//TODO: fill JWT credentials
func SetCredentials(auth config.AuthConfig) {
	grantType = "password"
	clientId = auth.UserPass.ClientId
	clientSecret = auth.UserPass.ClientSecret
	username = auth.UserPass.Username
	password = auth.UserPass.Password
	tokenEndpoint = auth.TokenUrl
}

func Login() (*LoginResponse, error) {
	body := url.Values{}
	body.Set("grant_type", grantType)
	body.Set("client_id", clientId)
	body.Set("client_secret", clientSecret)
	body.Set("username", username)
	body.Set("password", password)

	ctx, cancelFn := context.WithTimeout(context.Background(), oAuthDialTimeout)
	defer cancelFn()

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, tokenEndpoint+loginEndpoint, strings.NewReader(body.Encode()))
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

func UserInfo(accessToken string) (*UserInfoResponse, error) {
	ctx, cancelFn := context.WithTimeout(context.Background(), oAuthDialTimeout)
	defer cancelFn()

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, tokenEndpoint+userInfoEndpoint, nil)
	if err != nil {
		return nil, err
	}

	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", accessToken))

	httpResp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, err
	}

	defer httpResp.Body.Close()

	if httpResp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("non-200 status code returned on OAuth user info call: %v", httpResp.StatusCode)
	}

	var userInfoResponse UserInfoResponse
	err = json.NewDecoder(httpResp.Body).Decode(&userInfoResponse)
	if err != nil {
		return nil, err
	}

	return &userInfoResponse, nil
}
