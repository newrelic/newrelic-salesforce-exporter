package query

import "testing"

func TestSoqlQuery(t *testing.T) {
	soql := MakeSoqlQuery("MyTable", "one")
	soqlStr := soql.Build()
	expected := "SELECT+one+FROM+MyTable"
		if soqlStr != expected {
		t.Errorf("First SOQL is not the expected: %s", soqlStr)
	}

	soql = MakeSoqlQuery("MyTable", "one", "two", "three")
	soql.AndWhere("one = Hello")
	soql.OrWhere("two = Bye")
	soql.AndOrWhere("three = 0", "three = 1")
	soqlStr = soql.Build()
	expected = "SELECT+one,two,three+FROM+MyTable+WHERE+one+=+Hello+OR+two+=+Bye+AND+(+three+=+0+OR+three+=+1+)"
	if soqlStr != expected {
		t.Errorf("Second SOQL is not the expected: %s", soqlStr)
	}
}