package audit

import (
	"encoding/json"
	"strings"
	"testing"
)

func TestHiddenRedactsCredentialStrings(t *testing.T) {
	cases := []struct {
		input   string
		secret  string
		unchanged bool
	}{
		{"Authorization: Basic dXNlcjpwYXNz", "dXNlcjpwYXNz", false},
		{"authorization: Digest s3cr3t-digest", "s3cr3t-digest", false},
		{"Cookie: ota_session=cookie-secret", "cookie-secret", false},
		{"Set-Cookie: ota_session=set-cookie-secret; HttpOnly", "set-cookie-secret", false},
		{"https://user:url-secret@bucket.example/software/a", "url-secret", false},
		{"https://bucket.example/software/a?token=token-secret", "token-secret", false},
		{"https://bucket.example/software/a?password=password-secret", "password-secret", false},
		{"normal note", "", true},
		{"https://bucket.example/software/a", "", true},
	}
	for _, tc := range cases {
		detail, err := SanitizeDetail(map[string]any{"value": tc.input})
		if err != nil {
			t.Fatalf("%q: %v", tc.input, err)
		}
		got, _ := detail["value"].(string)
		if tc.unchanged {
			if got != tc.input {
				t.Errorf("SanitizeDetail(%q) = %q, want unchanged", tc.input, got)
			}
			continue
		}
		if !strings.Contains(got, "[redacted]") {
			t.Errorf("SanitizeDetail(%q) = %q, missing [redacted]", tc.input, got)
		}
		if strings.Contains(got, tc.secret) {
			t.Errorf("SanitizeDetail(%q) = %q, leaks %q", tc.input, got, tc.secret)
		}
	}
}

func TestHiddenRedactsInsideArraysAndKeepsOrdinaryText(t *testing.T) {
	detail, err := SanitizeDetail(map[string]any{
		"items": []any{
			map[string]any{"header": "Authorization: Basic array-secret"},
			"Cookie: session=array-cookie-secret",
			"release note",
		},
	})
	if err != nil {
		t.Fatal(err)
	}
	items, ok := detail["items"].([]any)
	if !ok || len(items) != 3 {
		t.Fatalf("items: %#v", detail["items"])
	}
	header, _ := items[0].(map[string]any)["header"].(string)
	if !strings.Contains(header, "[redacted]") || strings.Contains(header, "array-secret") {
		t.Fatalf("nested header survived: %#v", items[0])
	}
	cookie, _ := items[1].(string)
	if !strings.Contains(cookie, "[redacted]") || strings.Contains(cookie, "array-cookie-secret") {
		t.Fatalf("array cookie survived: %#v", items[1])
	}
	if items[2] != "release note" {
		t.Fatalf("ordinary array value changed: %#v", items[2])
	}
}

func TestHiddenCookieValuesDoNotLeak(t *testing.T) {
	detail, err := SanitizeDetail(map[string]any{
		"cookie":     "session=cookie-key-secret",
		"set-cookie": "session=set-cookie-key-secret",
		"note":       "kept",
	})
	if err != nil {
		t.Fatal(err)
	}
	raw, err := json.Marshal(detail)
	if err != nil {
		t.Fatal(err)
	}
	for _, secret := range []string{"cookie-key-secret", "set-cookie-key-secret"} {
		if strings.Contains(string(raw), secret) {
			t.Fatalf("cookie secret leaked: %s", raw)
		}
	}
	if detail["note"] != "kept" {
		t.Fatalf("ordinary key dropped: %#v", detail)
	}
}
