package config

import (
	"errors"
	"net/url"

	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/log"
)

func CheckUrl(urlStr string) bool {
	if _, err := url.ParseRequestURI(urlStr) ; err != nil {
   		return false
	}
	return true
}

func CheckAuth(auth *AuthConfig) error {
	if auth.TokenUrl == "" {
		return errors.New("Empty 'auth.tokenUrl'")
	}
	if !CheckUrl(auth.TokenUrl) {
   		return errors.New("Invalid URL 'auth.tokenUrl'")
	}
	definedAuthMethods := 0
	if auth.Jwt != nil {
		definedAuthMethods += 1
	}
	if auth.ClientCred != nil {
		definedAuthMethods += 1
	}
	if auth.UserPass != nil {
		definedAuthMethods += 1
	}
	if definedAuthMethods != 1 {
		return errors.New("Exactly one auth method must be defined")
	}
	if auth.Jwt != nil {
		err := checkJwtCredentials(auth.Jwt)
		if err != nil {
			return err
		}
	}
	if auth.ClientCred != nil {
		err := checkClientCredCredentials(auth.ClientCred)
		if err != nil {
			return err
		}
	}	
	if auth.UserPass != nil {
		err := checkUserPassCredentials(auth.UserPass)
		if err != nil {
			return err
		}
	}
	return nil
}

func checkUserPassCredentials(userPassAuth *UserPassAuth) error {
	if userPassAuth == nil {
		return errors.New("Undefined userPass credentials")
	}
	if userPassAuth.ClientId == "" {
		return errors.New("Empty 'userPass.clientId'")
	}
	if userPassAuth.ClientSecret == "" {
		return errors.New("Empty 'userPass.clientSecret'")
	}
	if userPassAuth.Username == "" {
		return errors.New("Empty 'userPass.username'")
	}
	if userPassAuth.Password == "" {
		return errors.New("Empty 'userPass.password'")
	}
	return nil
}

func checkJwtCredentials(jwtAuth *JwtAuth) error {
	if jwtAuth == nil {
		return errors.New("Undefined jwt credentials")
	}
	if jwtAuth.ClientId == "" {
		return errors.New("Empty 'jwt.clientId'")
	}
	if jwtAuth.PrivateKey == "" {
		return errors.New("Empty 'jwt.privateKey'")
	}
	if jwtAuth.Username == "" {
		return errors.New("Empty 'jwt.username'")
	}
	return nil
}

func checkClientCredCredentials(clientCredAuth *ClientCredAuth) error {
	if clientCredAuth == nil {
		return errors.New("Undefined clientCred credentials")
	}
	if clientCredAuth.ClientId == "" {
		return errors.New("Empty 'clientCred.clientId'")
	}
	if clientCredAuth.ClientSecret == "" {
		return errors.New("Empty 'clientCred.clientSecret'")
	}
	return nil
}

func CheckCache(cache *CacheConfig) error {
	if cache == nil {
		log.Warnf("Cache not defined, events won't be de-duplicated.")
	} else {
		if cache.Redis == nil {
			log.Warnf("Redis DB not defined, events won't be de-duplicated.")
		} else {
			if cache.Redis.Host == "" {
				return errors.New("Empty 'cache.redis.host'")
			}
		}
	}
	return nil
}