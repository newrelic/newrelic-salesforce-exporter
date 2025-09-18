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
	return nil
}

func CheckUserPassCredentials(userPassAuth *UserPassAuth) error {
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