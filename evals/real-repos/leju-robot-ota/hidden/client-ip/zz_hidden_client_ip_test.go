package audit

import (
	"net/http/httptest"
	"strings"
	"testing"
)

func TestHiddenClientIPFilter(t *testing.T) {
	r := httptest.NewRequest("GET", "/audit?client_ip=203.0.113.7", nil)
	f, err := parseFilter(r, true)
	if err != nil {
		t.Fatal(err)
	}
	where, args := f.where()
	if !strings.Contains(where, "client_ip") {
		t.Fatalf("client_ip missing from where: %s", where)
	}
	found := false
	for _, arg := range args {
		if arg == "203.0.113.7" {
			found = true
		}
	}
	if !found {
		t.Fatalf("client_ip value missing from args: %#v", args)
	}

	empty := httptest.NewRequest("GET", "/audit?client_ip=", nil)
	f, err = parseFilter(empty, true)
	if err != nil {
		t.Fatal(err)
	}
	where, _ = f.where()
	if strings.Contains(where, "client_ip") {
		t.Fatalf("empty client_ip added a condition: %s", where)
	}
}

func TestHiddenClientIPFilterComposesWithOtherFilters(t *testing.T) {
	r := httptest.NewRequest(
		"GET",
		"/audit?client_ip=203.0.113.7&module=account&result=success&limit=25",
		nil,
	)
	f, err := parseFilter(r, true)
	if err != nil {
		t.Fatal(err)
	}
	where, args := f.where()
	for _, needle := range []string{"client_ip", "action = ANY", "result = $"} {
		if !strings.Contains(where, needle) {
			t.Fatalf("%s missing from where: %s", needle, where)
		}
	}
	foundIP, foundResult := false, false
	for _, arg := range args {
		foundIP = foundIP || arg == "203.0.113.7"
		foundResult = foundResult || arg == "success"
	}
	if !foundIP || !foundResult {
		t.Fatalf("filter args missing: %#v", args)
	}
	if f.Limit != 25 {
		t.Fatalf("limit: %d", f.Limit)
	}
}
