package oauth

import (
	"context"
	"encoding/json"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/log"
)

func AuthWithJwt(loginUrl string) {
	//TODO: move this to AuthConfig
	privateKeyPath := "path/to/private.key"
	clientID := "your_client_id"
	username := "your_username"
	//loginURL := "https://login.salesforce.com"

	// Load private key
	privateKeyData, err := os.ReadFile(privateKeyPath)
	if err != nil {
		panic(err)
	}
	privateKey, err := jwt.ParseRSAPrivateKeyFromPEM(privateKeyData)
	if err != nil {
		panic(err)
	}

	// Create JWT
	token := jwt.NewWithClaims(jwt.SigningMethodRS256, jwt.MapClaims{
		"iss": clientID,
		"sub": username,
		"aud": loginUrl,
		//TODO: get expire time from AuthConfig
		"exp": time.Now().Add(time.Minute * 5).Unix(),
	})
	signedToken, err := token.SignedString(privateKey)
	if err != nil {
		panic(err)
	}

	// // Make POST request to Salesforce
	// data := map[string]string{
	// 	"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
	// 	"assertion":  signedToken,
	// }
	// jsonData, _ := json.Marshal(data)
	// resp, err := URL_Redacted(loginURL+"/services/oauth2/token", "application/json", bytes.NewBuffer(jsonData))
	// if err != nil {
	// 	panic(err)
	// }
	// defer resp.Body.Close()

	// // Read response
	// body, _ := io.ReadAll(resp.Body)
	// fmt.Println(string(body))

	body := url.Values{}

	body.Set("grant_type", "urn:ietf:params:oauth:grant-type:jwt-bearer")
	body.Set("assertion", signedToken,)

	ctx, cancelFn := context.WithTimeout(context.Background(), oAuthDialTimeout)
	defer cancelFn()

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, loginUrl + loginEndpoint, strings.NewReader(body.Encode()))
	if err != nil {
		log.Errorf("Error creating JWT auth request: %s", err)
		return
	}

	httpResp, err := http.DefaultClient.Do(req)
	if err != nil {
		log.Errorf("Error doing JWT auth request: %s", err)
		return
	}

	defer httpResp.Body.Close()

	if httpResp.StatusCode != http.StatusOK {
		log.Errorf("non-200 status code returned on OAuth authentication call: %v", httpResp.StatusCode)
		return
	}

	d := map[string]any{}
	if err := json.NewDecoder(httpResp.Body).Decode(&d) ; err != nil {
		log.Errorf("Error decoding response: %s", err)
		return
	}
	log.Debugf("JWT auth response = %v", d)
}

/*
### Additional Resources:

- [OAuth 2.0 JWT Bearer Flow for Server-to-Server Integration](https://help.salesforce.com/s/articleView?id=xcloud.remoteaccess_oauth_jwt_flow.htm&type=5&release=258.0.0)
- [Salesforce Developer Documentation](https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference_org_commands_unified.html)

This example demonstrates how to generate a JWT, send it to Salesforce, and handle the response. Make sure to replace placeholders with your actual Salesforce credentials and paths.
*/
