package config

import (
	"errors"
	"net/url"
)

func CheckUrl(urlStr string) bool {
	if _, err := url.ParseRequestURI(urlStr) ; err != nil {
   		return false
	}
	return true
}

func CheckAuth(auth AuthConfig) error {
	if auth.TokenUrl == "" {
		return errors.New("Empty 'auth.token_url'")
	}
	if !CheckUrl(auth.TokenUrl) {
   		return errors.New("Invalid URL 'auth.token_url'")
	}
	return nil
}

func CheckUserPassCredentials(userPassAuth *UserPassAuth) error {
	if userPassAuth == nil {
		return errors.New("Undefined user_pass credentials")
	}
	if userPassAuth.ClientId == "" {
		return errors.New("Empty 'user_pass.client_id'")
	}
	if userPassAuth.ClientSecret == "" {
		return errors.New("Empty 'user_pass.client_secret'")
	}
	if userPassAuth.Username == "" {
		return errors.New("Empty 'user_pass.username'")
	}
	if userPassAuth.Password == "" {
		return errors.New("Empty 'user_pass.password'")
	}
	return nil
}
