package oauth

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
)

func AuthWithJwt(auth config.AuthConfig) (*LoginResponse, error) {
	privateKeyPath := auth.Jwt.PrivateKey
	clientID := auth.Jwt.ClientId
	username := auth.Jwt.Username
	loginUrl := auth.TokenUrl

	// Load private key
	privateKeyData, err := os.ReadFile(privateKeyPath)
	if err != nil {
		return nil, fmt.Errorf("Error reading private key file: %s", err)
	}
	privateKey, err := jwt.ParseRSAPrivateKeyFromPEM(privateKeyData)
	if err != nil {
		return nil, fmt.Errorf("Error parsing private key: %s", err)
	}

	// Create JWT
	token := jwt.NewWithClaims(jwt.SigningMethodRS256, jwt.MapClaims{
		"iss": clientID,
		"sub": username,
		"aud": loginUrl,
		"exp": time.Now().Add(time.Minute * 5).Unix(),
	})
	signedToken, err := token.SignedString(privateKey)
	if err != nil {
		return nil, fmt.Errorf("Error signing token: %s", err)
	}

	body := url.Values{}

	body.Set("grant_type", "urn:ietf:params:oauth:grant-type:jwt-bearer")
	body.Set("assertion", signedToken,)

	ctx, cancelFn := context.WithTimeout(context.Background(), oAuthDialTimeout)
	defer cancelFn()

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, loginUrl + loginEndpoint, strings.NewReader(body.Encode()))
	if err != nil {
		return nil, fmt.Errorf("Error creating JWT auth request: %s", err)
	}

	req.Header.Add("Content-Type", "application/x-www-form-urlencoded")

	httpResp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("Error doing JWT auth request: %s", err)
	}

	defer httpResp.Body.Close()

	if httpResp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("non-200 status code returned on OAuth authentication call: %v", httpResp.StatusCode)
	}

	var loginResponse LoginResponse
	err = json.NewDecoder(httpResp.Body).Decode(&loginResponse)
	if err != nil {
		return nil, fmt.Errorf("Error decoding response: %s", err)
	}

	return &loginResponse, nil
}