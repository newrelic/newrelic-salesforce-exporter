package query

import "strings"

type EventLogfileResponse struct {
	TotalSize int                  `json:"totalSize"`
	Done      bool                 `json:"done"`
	Records   []EventLogfileRecord `json:"records"`
}

type EventLogfileRecord struct {
	Id        string `json:"Id"`
	LogDate   string `json:"LogDate"`
	LogFile   string `json:"LogFile"`
	EventType string `json:"EventType"`
}

type SoqlQuery struct {
	fromTable   string
	selectAttrs []string
	where       string
}

func (s *SoqlQuery) AndWhere(where string) {
	if s.where == "" {
		s.where = where
	} else {
		s.where += "+AND+" + where
	}
}

func (s *SoqlQuery) OrWhere(where string) {
	if s.where == "" {
		s.where = where
	} else {
		s.where += "+OR+" + where
	}
}

func (s *SoqlQuery) AndOrWhere(where ...string) {
	resultWhere := "(+"
	for index, w := range where {
		if index == len(where)-1 {
			resultWhere += w + "+)"
		} else {
			resultWhere += w + "+OR+"
		}
	}
	if s.where == "" {
		s.where = resultWhere
	} else {
		s.where += "+AND+" + resultWhere
	}
}

func (s *SoqlQuery) Build() string {
	soql := "SELECT+" + strings.Join(s.selectAttrs, ",") + "+FROM+" + s.fromTable
	if s.where != "" {
		s.where = strings.ReplaceAll(s.where, " ", "+")
		soql += "+WHERE+" + s.where
	}
	return soql
}

func MakeSoqlQuery(fromTable string, selectAttrs ...string) SoqlQuery {
	return SoqlQuery{
		fromTable:   fromTable,
		selectAttrs: selectAttrs,
	}
}
