# Cross-repo ablation matrix

- started: 2026-11-03T04:46:33+00:00
- models: fable, sonnet
- arms: no-skill, build, build-test, build-test-review, chain
- tasks: build-scenarios, leju-robot-ota, leju-let-platform
- runs per cell: 1
- runner failures: 0

| arm | scenario | runs | task pass | hidden | files | tools | seconds | out tokens | skill calls | errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| matrix-fable-build | LET1-dept-isolation-consistency | 1 | 1 | 1/1 | 2.0 | 34.0 | 482.6 | 36729 | 1 | 0 |
| matrix-fable-build | OTA2-audit-client-ip-filter | 1 | 0 | 1/1 | 6.0 | 30.0 | 226.2 | 13572 | 1 | 0 |
| matrix-fable-build | S11-saas-billing-backend | 1 | 1 | 1/1 | 4.0 | 20.0 | 288.4 | 38404 | 1 | 0 |
| matrix-fable-build | S9-fullstack-backend-filter | 1 | 1 | 1/1 | 2.0 | 9.0 | 80.9 | 5384 | 1 | 0 |
| matrix-fable-build-test | LET1-dept-isolation-consistency | 1 | 1 | 1/1 | 2.0 | 27.0 | 388.5 | 23950 | 2 | 0 |
| matrix-fable-build-test | OTA2-audit-client-ip-filter | 1 | 0 | 1/1 | 7.0 | 42.0 | 361.1 | 22471 | 2 | 0 |
| matrix-fable-build-test | S11-saas-billing-backend | 1 | 1 | 1/1 | 4.0 | 20.0 | 223.9 | 21988 | 2 | 0 |
| matrix-fable-build-test | S9-fullstack-backend-filter | 1 | 1 | 1/1 | 2.0 | 15.0 | 133.3 | 8489 | 2 | 0 |
| matrix-fable-build-test-review | LET1-dept-isolation-consistency | 1 | 1 | 1/1 | 2.0 | 35.0 | 463.7 | 40499 | 3 | 0 |
| matrix-fable-build-test-review | OTA2-audit-client-ip-filter | 1 | 0 | 0/1 | 5.0 | 42.0 | 348.1 | 28588 | 1 | 0 |
| matrix-fable-build-test-review | S11-saas-billing-backend | 1 | 1 | 1/1 | 4.0 | 14.0 | 185.5 | 23577 | 3 | 0 |
| matrix-fable-build-test-review | S9-fullstack-backend-filter | 1 | 1 | 1/1 | 2.0 | 13.0 | 127.6 | 9283 | 3 | 0 |
| matrix-fable-chain | LET1-dept-isolation-consistency | 1 | 1 | 1/1 | 2.0 | 23.0 | 360.4 | 26951 | 1 | 0 |
| matrix-fable-chain | OTA2-audit-client-ip-filter | 1 | 0 | 1/1 | 6.0 | 45.0 | 361.2 | 26112 | 1 | 0 |
| matrix-fable-chain | S11-saas-billing-backend | 1 | 1 | 1/1 | 6.0 | 52.0 | 304.8 | 53490 | 6 | 0 |
| matrix-fable-chain | S9-fullstack-backend-filter | 1 | 1 | 1/1 | 2.0 | 17.0 | 76.9 | 9863 | 5 | 0 |
| matrix-fable-no-skill | LET1-dept-isolation-consistency | 1 | 1 | 1/1 | 2.0 | 25.0 | 502.0 | 25886 | 0 | 0 |
| matrix-fable-no-skill | OTA2-audit-client-ip-filter | 1 | 0 | 1/1 | 6.0 | 29.0 | 197.2 | 17185 | 0 | 0 |
| matrix-fable-no-skill | S11-saas-billing-backend | 1 | 1 | 1/1 | 5.0 | 14.0 | 146.2 | 17632 | 0 | 0 |
| matrix-fable-no-skill | S9-fullstack-backend-filter | 1 | 1 | 1/1 | 2.0 | 6.0 | 51.4 | 4403 | 0 | 0 |
| matrix-sonnet-build | LET1-dept-isolation-consistency | 1 | 1 | 1/1 | 2.0 | 59.0 | 571.0 | 35902 | 1 | 0 |
| matrix-sonnet-build | OTA2-audit-client-ip-filter | 1 | 0 | 1/1 | 6.0 | 49.0 | 128.4 | 13949 | 1 | 0 |
| matrix-sonnet-build | S11-saas-billing-backend | 1 | 1 | 1/1 | 5.0 | 41.0 | 209.3 | 30061 | 1 | 0 |
| matrix-sonnet-build | S9-fullstack-backend-filter | 1 | 1 | 1/1 | 2.0 | 22.0 | 48.8 | 5243 | 1 | 0 |
| matrix-sonnet-build-test | LET1-dept-isolation-consistency | 1 | 1 | 1/1 | 2.0 | 73.0 | 339.0 | 25851 | 2 | 0 |
| matrix-sonnet-build-test | OTA2-audit-client-ip-filter | 1 | 0 | 1/1 | 7.0 | 81.0 | 368.1 | 33502 | 2 | 0 |
| matrix-sonnet-build-test | S11-saas-billing-backend | 1 | 1 | 1/1 | 4.0 | 30.0 | 127.0 | 16773 | 2 | 0 |
| matrix-sonnet-build-test | S9-fullstack-backend-filter | 1 | 1 | 1/1 | 2.0 | 33.0 | 84.9 | 8499 | 2 | 0 |
| matrix-sonnet-build-test-review | LET1-dept-isolation-consistency | 1 | 1 | 1/1 | 2.0 | 104.0 | 746.9 | 66886 | 3 | 0 |
| matrix-sonnet-build-test-review | OTA2-audit-client-ip-filter | 1 | 0 | 1/1 | 10.0 | 84.0 | 285.6 | 22116 | 3 | 0 |
| matrix-sonnet-build-test-review | S11-saas-billing-backend | 1 | 1 | 1/1 | 4.0 | 35.0 | 153.1 | 23605 | 3 | 0 |
| matrix-sonnet-build-test-review | S9-fullstack-backend-filter | 1 | 1 | 1/1 | 2.0 | 19.0 | 108.8 | 11376 | 3 | 0 |
| matrix-sonnet-chain | LET1-dept-isolation-consistency | 1 | 0 | 0/0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 1 |
| matrix-sonnet-chain | OTA2-audit-client-ip-filter | 1 | 0 | 1/1 | 10.0 | 113.0 | 535.3 | 55226 | 1 | 0 |
| matrix-sonnet-chain | S11-saas-billing-backend | 1 | 0 | 0/0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 1 |
| matrix-sonnet-chain | S9-fullstack-backend-filter | 1 | 1 | 1/1 | 2.0 | 61.0 | 201.4 | 20616 | 5 | 0 |
| matrix-sonnet-no-skill | LET1-dept-isolation-consistency | 1 | 1 | 1/1 | 2.0 | 45.0 | 203.1 | 18489 | 0 | 0 |
| matrix-sonnet-no-skill | OTA2-audit-client-ip-filter | 1 | 0 | 1/1 | 7.0 | 40.0 | 99.4 | 9093 | 0 | 0 |
| matrix-sonnet-no-skill | S11-saas-billing-backend | 1 | 1 | 1/1 | 4.0 | 48.0 | 119.4 | 16257 | 0 | 0 |
| matrix-sonnet-no-skill | S9-fullstack-backend-filter | 1 | 1 | 1/1 | 3.0 | 19.0 | 62.4 | 7350 | 0 | 0 |
