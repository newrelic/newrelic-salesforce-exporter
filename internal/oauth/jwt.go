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
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/log"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
)

func AuthWithJwt(tokenUrl string, auth *config.JwtAuth) (*AuthResponse, error) {
	privateKeyPath := auth.PrivateKey
	clientID := auth.ClientId
	username := auth.Username

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
		"aud": tokenUrl,
		"exp": time.Now().Add(time.Minute * 5).Unix(),
	})
	signedToken, err := token.SignedString(privateKey)
	if err != nil {
		return nil, fmt.Errorf("Error signing token: %s", err)
	}

	body := url.Values{}

	body.Set("grant_type", "urn:ietf:params:oauth:grant-type:jwt-bearer")
	body.Set("assertion", signedToken)

	ctx, cancelFn := context.WithTimeout(context.Background(), oAuthDialTimeout)
	defer cancelFn()

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, tokenUrl+loginEndpoint, strings.NewReader(body.Encode()))
	if err != nil {
		return nil, fmt.Errorf("Error creating JWT auth request: %s", err)
	}

	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")

	httpResp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("Error doing JWT auth request: %s", err)
	}

	defer httpResp.Body.Close()

	if httpResp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("%s", authError(httpResp.Body, httpResp.StatusCode))
	}

	var authResponse AuthResponse
	err = json.NewDecoder(httpResp.Body).Decode(&authResponse)
	if err != nil {
		return nil, fmt.Errorf("Error decoding response: %s", err)
	}

	log.Debugf("Auth with JWT, OK")

	return &authResponse, nil
}