# Worklog

---
Task ID: 1
Agent: main (Z.ai)
Task: Connect local workspace to GitHub repo alipedramiau-bit/Net_Scan and push main branch

Work Log:
- Checked git status: local repo on `main`, clean tree, no remote configured
- Added remote `origin` with user's credentials (remote did not exist, used `git remote add` instead of `set-url`)
- First push rejected: remote had its own commit `6f881b8 Initial commit - Net_Scan project` (2279 files: backend/, bin/, README.md, etc.)
- Local had only 3 files (.env, .gitignore, download/README.md) — direct push would have destroyed remote project
- Fetched remote, merged with `--allow-unrelated-histories --no-rebase`
- Resolved single .gitignore add/add conflict by combining both versions (remote Python ignores + local `skills/`)
- Untracked `.env` via `git rm --cached` for security (merged .gitignore excludes it; file kept locally)
- Committed merge as 907bdd0 and pushed successfully: `6f881b8..907bdd0 main -> main`, upstream tracking set

Stage Summary:
- Local workspace now contains the full Net_Scan project (2280 tracked files) synced with GitHub
- `main` is tracking `origin/main`, fully in sync, clean tree
- `.env` remains on disk locally but is NOT in the repository (excluded via .gitignore)
- GitHub repo: https://github.com/alipedramiau-bit/Net_Scan

---
Task ID: 2
Agent: main (Z.ai)
Task: Include all report fields in the interface-flap CSV export and push to GitHub

Work Log:
- Analyzed frontend/src.jsx flap table (9 columns) vs backend/smart_reports.py interface_flaps_csv (8 columns)
- Found missing field: flap_count (تعداد تکرار لاگ) — shown in UI but absent from CSV/XLSX
- Rewrote interface_flaps_csv: 9 columns matching UI order exactly (ردیف، نام دستگاه، آی‌پی، تگ، اینترفیس، تعداد تکرار لاگ، تاریخ میلادی، تاریخ شمسی، نوع رویداد)
- Applied same 9-column layout to interface_flaps_xlsx for consistency
- Verified via scripts/test_flap_csv.py: 9-col header+rows, UTF-8 BOM present, flap_count values (3,4) rendered, XLSX builds clean
- Committed backend/smart_reports.py only (2572284), pushed 907bdd0..2572284 to origin/main

Stage Summary:
- CSV/XLSX flap exports now contain ALL report fields identical to the on-screen table
- Commit pushed to GitHub: 2572284 "Include all report fields in interface flap CSV export"
- Deployment note: server at 185.110.29.189:5001 needs git pull + service restart to pick up the change

---
Task ID: 3
Agent: main (Z.ai)
Task: Optimize device-management search + add database selection to smart reports, push to GitHub

Work Log:
- backend/db.py: added SEARCH_FIELDS whitelist + build_search_clause() (multi-term AND, scoped fields, injection-safe); query_devices gained q_fields param
- backend/main.py: /devices and /devices/export.csv accept q_fields; all 3 flap-report endpoints accept database param with _resolve_report_database() validation (404 unknown, empty = active DB); report metadata includes "database"
- frontend/src.jsx (DeviceReports): 350ms debounce (qInput/q split), AbortController for in-flight list requests, search scope <select> (12 options), Enter = instant search
- frontend/src.jsx (SmartReports): database selector from /api/databases with device counts, passes database to list+CSV URLs, source-DB badge, clears results on DB switch
- Tests: scripts/test_search_and_db.py — 12/12 PASS via FastAPI TestClient (temp DB registered/removed from catalog, active DB switched/restored)
- Rebuilt frontend/dist with vite (npm install + npm run build)
- Committed b8ae262, pushed 16dff0e..b8ae262 to origin/main

Stage Summary:
- Search: debounced, cancellable, multi-term AND, per-field scope (faster than scanning all columns incl. device_log)
- Smart reports: report generated from user-selected database; badge shows source; backend enforces validation
- Deployment: remote server needs git pull + service restart; browser hard-refresh for new hashed assets

---
Task ID: 4
Agent: main (Z.ai)
Task: Add admin login page (NetAdmin/NetAdmin), creative logo, session auth; push to GitHub

Work Log:
- backend/auth.py (new): HMAC-SHA256 signed tokens, persisted secret in databases/.auth_secret (0600), constant-time creds check, default NetAdmin/NetAdmin (env: NETSCAN_ADMIN_USER/PASSWORD, NETSCAN_SESSION_DAYS)
- backend/main.py: AuthMiddleware (protects /api/, /devices, /reports, /scans; OPTIONS + login/logout/auth-check + non-API paths open), POST /api/login (sets HttpOnly SameSite=Lax cookie, 7d), POST /api/logout, GET /api/auth/check; CORS -> allow_origin_regex=".*" + allow_credentials=True
- frontend/src.jsx: Logo component (radar sweep + network blips SVG), Login component (RTL card, show/hide password, error/loading), App wrapper auth gate (checking->out->in) with netscan:unauthorized global 401 listener via readJson, MainApp receives authUser/onLogout, header logout button
- frontend/style.css: login page styles (gradient backdrop, glow, card, inputs, button); frontend/public/logo.svg favicon + index.html icon link
- Fixed React hooks-order bug by splitting App (gate) / MainApp (content)
- Tests: scripts/test_auth.py — 24/24 PASS (401s, login ok/wrong, cookie flags, token tamper/expiry, logout, preflight CORS w/ credentials)
- Rebuilt dist; committed 1d545d2, pushed 76b3303..1d545d2 to origin/main

Stage Summary:
- App now requires admin login (NetAdmin/NetAdmin); session survives restarts via persisted secret
- Creative SVG logo on login page + favicon
- Deployment: git pull + restart on server; Ctrl+Shift+R for new assets

---
Task ID: 5
Agent: main (Z.ai)
Task: Re-push complete project to GitHub after user reset the remote repository

Work Log:
- Fetched origin: remote main was force-replaced by user with a fresh "Initial commit" containing only an accidentally-committed Windows venv (Lib/, Scripts/, pyvenv.cfg) - zero project code
- Enabled core.fileMode=false locally to silence 2264 permission-only diffs (644->755 noise, no content changes)
- Extended .gitignore: Lib/, Scripts/, pyvenv.cfg (Windows root venv), .idea/, .net_scan/
- Untracked pyvenv.cfg venv remnant
- Force-pushed complete local project (full history: CSV fix, search optimization + report DB selector, admin login + logo, auth secret/test) to origin/main

Stage Summary:
- origin/main now holds the complete Net_Scan project with all 4 completed tasks
- Remote's venv-only initial commit intentionally replaced (contained no project content)

---
Task ID: 6
Agent: main (Z.ai)
Task: Fix "smart report stopped working" (0 results) + restore admin/NetAdmin login spec; push to GitHub

Work Log:
- Diagnosed end-to-end: backend + report logic fully functional (79 events / 53 devices on the same 2131-device default.db via real HTTP, auth included) - the "0 results" case had NO explanation in UI and silently swallowed read errors
- backend/smart_reports.py: interface_flap_report now returns devices_scanned, devices_with_logs, newest_log_at(_jalali) and, when the window is newer than all logs, stale_logs=true + suggested_days (capped 90)
- backend/main.py: JSON report includes "error" field when device read fails; CSV/XLSX exports now raise HTTP 500 on read failure instead of silently exporting empty files
- frontend/src.jsx (SmartReports): loadList(days/threshold overrides) + diagnostics panel on empty results (devices scanned/with logs, newest log event in jalali+gregorian), red error box for DB read failures, one-click "report with N-day range" button for stale logs; DB switch clears diagnostics
- backend/auth.py: ADMIN_USER default fixed to "admin" (was "NetAdmin") per original spec - login is now admin/NetAdmin; NETSCAN_ADMIN_USER/PASSWORD env overrides unchanged
- frontend Login: username placeholder + fallback -> "admin"
- scripts/test_report_fix.py (18 checks) + scripts/test_auth.py updated: ALL PASS
- E2E re-verified over HTTP: login admin/NetAdmin 200, report 79 events, CSV 80 lines
- Rebuilt frontend/dist

Stage Summary:
- Empty report now explains itself: scanned/logged device counts, newest log timestamp, stale-log banner with wider-range button; real DB errors surface instead of fake "no results"
- Login credentials per original request: admin / NetAdmin (NetAdmin/NetAdmin no longer valid)
- Deployment: git pull + backend restart + browser hard refresh (Ctrl+Shift+R)

---
Task ID: 7
Agent: main (Z.ai)
Task: Fix smart report ROOT CAUSE revealed by Task-6 error box ("نام دیتابیس نامعتبر است"); push to GitHub

Work Log:
- User screenshot showed the red error box added in Task 6: "خواندن دستگاه‌ها از دیتابیس «default» ناموفق بود: نام دیتابیس نامعتبر است (۱ تا ۶۴ کاراکتر)" - the previously silently-swallowed exception
- Root cause: _ip_info_dir(db_path) passed a full FILESYSTEM PATH into db_path_for(), which expects a database NAME; _safe_db_name() then sanitized the whole path and raised ValueError whenever the result exceeded 64 chars (typical Windows project paths). query_devices -> enrich_devices_from_ip_info raised -> endpoints returned empty (old code) / error (Task 6)
- backend/db.py _ip_info_dir: now detects filesystem paths (suffix .db or multi-part) and uses path.parent/ip_info directly; plain names still resolve via db_path_for(); None -> active db
- scripts/test_ip_info_path_fix.py: 12 checks incl. >64-char sanitized path reproduction, Path/str/name/None inputs, end-to-end query_devices + ip_info enrichment + flap report on a long path, real default.db sanity - ALL PASS
- scripts/test_search_and_db.py: repaired stale test (login after Task-4 auth middleware, cleanup ordering, leftover zz_search_test.db) - ALL PASS
- Full regression: report_fix 18/18, auth OK, search_and_db OK

Stage Summary:
- Smart report now works regardless of project path length (fixes user's Windows deployment where C:\Users\...\Net_Scan exceeded 64 chars after sanitization)
- Data files (catalog.json / *.db) intentionally left out of this commit to avoid overwriting user's live data on git pull

---
Task ID: 8
Agent: main (Z.ai)
Task: Commit and push the latest version to GitHub (user: «آخرین نسخه را روی گیت هاب کامیت کن»)

Work Log:
- Verified working tree clean; one local commit (auto-created with UUID message) held the user's two uploaded problem screenshots (scan tab "Failed to fetch" + smart report DB-name error)
- Confirmed Task-7 root-cause fix 4f43e96 already on origin/main; re-ran regressions: test_ip_info_path_fix 12/12, test_report_fix 18/18 - ALL PASS
- Amended UUID commit message to descriptive text (975959e)
- Appended this worklog entry, committed, pushed both commits to origin/main

Stage Summary:
- origin/main now in sync with local main including the Task-7 fix and user screenshots
- Deployment reminder for user: git pull on server + backend restart + Ctrl+Shift+R

---
Task ID: 9
Agent: main (AI Studio Build)
Task: Fix scan tab "Failed to fetch" root cause, relative API URLs, and rebuild frontend dist; push to GitHub

Work Log:
- Investigated user screenshot `upload/IMG_20261024_103007.jpg` showing the light-pink error box on the Network Scan tab: "Failed to fetch"
- Identified root cause in `frontend/src.jsx`: `API` variable only returned relative URL `""` if hostname was strictly `"127.0.0.1"` or `"localhost"`. When accessed via remote IP (e.g. `http://185.110.29.189:5001`), it evaluated to `http://${h}:8001`. Client browsers attempting to call port 8001 directly failed due to firewall restrictions, cross-origin restrictions, or un-forwarded ports on remote servers, throwing `TypeError: Failed to fetch`.
- Updated `API` in `frontend/src.jsx` to always return same-origin relative path `""` in the browser, allowing Vite's port 5001 proxy (`/scans`, `/devices`, `/health`, `/api`, `/reports`) or FastAPI to serve requests reliably without opening port 8001 publicly.
- Improved `start()`, `transferScan()`, and `stopScan()` to use `readJson`, properly catching and dispatching `netscan:unauthorized` on 401 status.
- Added retry resilience to scan status polling interval to avoid flashing errors on single transient hiccups.
- Rebuilt production assets via `vite build` into `frontend/dist`.

Stage Summary:
- Scan tab no longer fails with "Failed to fetch" when accessed remotely via IP or custom domain.
- Frontend dist rebuilt and synchronized.
- Ready to push to GitHub origin/main.


---
Task ID: 10
Agent: main (Z.ai)
Task: Add "خروجی CSV میکروتیک" button — export selected MikroTik devices with all previously-read fields

Work Log:
- Read latest commit 66b18b6 ("Update backend files"): venv package refresh + databases/ip_info runtime data + dist rebuild; no source changes to backend/frontend
- backend/db.py: added _is_mikrotik_device() (classification=mikrotik_candidate OR ports 8291/8728 open) and mikrotik_selected_to_csv(ips) — full CSV export, one column per previously-read field (identity name, device type, tags, ping, open ports, port states 8291/8728, classification, interfaces, ip_addresses, ip_neighbors, wireless_info, device_log, mac_info, first/last seen, seen_count) with Persian headers matching UI terminology; enriches empty fields from ip_info/{ip}.txt via fetch_devices_by_ips; raises ValueError when no MikroTik in selection
- backend/main.py: new POST /devices/export-mikrotik.csv endpoint (ExportSelectedBody{ips}); filters non-MikroTik out, 400 with Persian message when selection has no MikroTik or is empty; returns CSV with UTF-8 BOM and Content-Disposition mikrotik_selected_{stamp}.csv
- frontend/src.jsx: added exportCsvMikrotikSelected() (POST selectedIps, blob download, filename from Content-Disposition, error toast on 400) and button "خروجی CSV میکروتیک (N)" in the خروجی tool-group of the device-management toolbar (above the device list), disabled without selection
- Rebuilt frontend/dist with vite (npm install + npm run build)
- Test: scripts/test_export_mikrotik_csv.py — 30/30 PASS via FastAPI TestClient (temp DB: 3 MikroTik + 1 non-MikroTik; verifies filtering, 18-column Persian header, per-field values incl. multiline device_log quoting, BOM, filename header, 400 paths, 401 for unauthenticated)
- Full unittest suite: 15/15 OK

Stage Summary:
- Device-management tab now exports the SELECTED MikroTik devices' complete read data to CSV, field by field
- Ready to push to GitHub origin/main

---
Task ID: 11
Agent: main (Z.ai)
Task: Rework "خواندن اطلاعات دستگاه با API" — parallel probe + live segmented progress chart

Work Log:
- Reviewed backend/routeros_api.py probe_devices_via_api_many: was strictly sequential (one device at a time, up to 12s timeout each) — large selections took many minutes
- Rewrote it with a bounded ThreadPoolExecutor (max_workers, default 6, clamp 1..16): each worker opens its own RouterOS API connection; results reassembled in input order; cooperative cancel preserved (workers skip when event set, partial results kept); shared progress dict now tracks ok/failed live counts besides total/done/current_ip (thread-safe via lock)
- backend/main.py: ApiProbeRequest gained max_workers (1..16, default 6) and passes it through; GET /api/devices/probe-api/progress now returns ok/failed/remaining as well
- frontend/src.jsx: replaced the single-color bar with a labeled progress chart — heading shows which probe runs (API/SNMP) + current target IP; segmented bar (green=ok, red=failed, gray track=remaining); stat chips: موفق / ناموفق / باقی‌مانده / done-of-total / درصد. SNMP probe (no ok/failed fields) falls back to the classic percent bar — UI is defensive via typeof checks
- frontend/style.css: .progress-seg.ok/.fail, .probe-progress-head, .probe-stat chips (+reduced-motion guard)
- Rebuilt frontend/dist with vite
- Test: scripts/test_api_probe_progress.py — parallel wall time 3.0s for 4×3s probes (vs ~12s sequential), order preserved, ok/failed counters, endpoint fields, pre-cancel and empty-list paths — ALL PASS; unit suite 15/15 OK

Stage Summary:
- API probe is now ~6× faster on large selections and the UI shows a live segmented progress chart
- Ready to push to GitHub origin/main (together with Task 10 CSV export commit)

---
Task ID: 12
Agent: main (Z.ai)
Task: Fix empty detail fields in MikroTik CSV export (live auto-read) + AGENTS.md + docs refresh

Work Log:
- Root cause of empty CSV fields (user report: interfaces/ip/neighbors/wireless/log/mac empty for ~31 devices out of 386): those devices were never fully read via RouterOS API (only SNMP name or scan-level data), so no data existed in DB or ip_info txt files to export
- backend/db.py: added DETAIL_CORE_FIELDS (interfaces, ip_addresses, device_log, mac_info), device_details_complete() and device_read_status(); mikrotik_selected_to_csv now writes a 19th column «وضعیت خواندن» (کامل / ناقص — اطلاعات کامل خوانده نشد) so every row explains its own completeness
- backend/main.py: ExportSelectedBody gained read_missing/username/password/port/timeout/max_workers; export endpoint now live-reads incomplete selected devices via routeros_api.probe_devices_via_api_many (parallel, same API_PROBE_PROGRESS + cancel event) and persists them BEFORE building the CSV; new shared _persist_api_probe_results() extracted from the probe endpoint (single source of truth for DB+ip_info txt persistence); collect-ip-info txt files now written with standard "----- section -----" headers so enrich_devices_from_ip_info can parse them
- frontend/src.jsx: export button now sends read_missing=true + RouterOS credentials (apiUser/apiPass) and polls /api/devices/probe-api/progress during export — the segmented progress chart (نمودار پیشرفت) shows live with title "نمودار پیشرفت خواندن اطلاعات برای خروجی CSV"; success toast reports how many devices were freshly read / failed; state csvReading added
- AGENTS.md created: Persian agent guide (architecture, key paths, run/test/build commands, commit conventions incl. scripts/ gitignore force-add + worklog Task IDs, feature map, gotchas, security rules)
- README.md updated: multi-DB catalog + new devices columns + ip_info enrichment, new sections «خواندن اطلاعات دستگاه‌ها (SNMP و RouterOS API)» (parallel probe + segmented progress chart) and «خروجی CSV دستگاه‌های میکروتیک انتخاب‌شده» (19 columns, auto-read, status column), new API endpoints listed, pointer to AGENTS.md
- frontend/dist rebuilt (vite)
- Test: scripts/test_export_mikrotik_csv.py extended to 40 checks — 19-column header, per-column values incl. multiline log (csv.reader parse), status column کامل/ناقص, read_missing flow (only incomplete device probed, credentials+progress+max_workers passed, X-Export-* headers, live data in CSV, DB+txt persistence, no re-read when complete), 400 paths, 401 — ALL PASS; tests/ unit suite 15/15 OK; scripts/test_api_probe_progress.py ALL PASS

Stage Summary:
- CSV export now guarantees real data: devices without complete details are read live (with progress chart) before export, and the «وضعیت خواندن» column makes completeness explicit per row
- AGENTS.md + README.md document the project for humans and AI agents
- Ready to push to GitHub origin/main (together with Task 10 + Task 11 commits)

---
Task ID: 13
Agent: main (Z.ai)
Task: JSON export of selected MikroTik devices (same fields as CSV)

Work Log:
- backend/db.py: exported-row logic refactored out of mikrotik_selected_to_csv into new mikrotik_selected_rows() + MIKROTIK_EXPORT_FIELDS (the 19 Persian headers as single source of truth); CSV builder now just serializes those rows — CSV output byte-identical
- backend/main.py: live auto-read flow extracted to shared _live_read_missing_devices() used by BOTH export endpoints; new POST /devices/export-mikrotik.json returns {"exported_at","database","count","fields","devices"} (devices = array of dicts keyed by the Persian CSV headers), attachment mikrotik_selected_{stamp}.json, application/json; charset=utf-8, same X-Export-* headers
- frontend/src.jsx: new button «خروجی JSON میکروتیک (N)» beside the CSV button with exportJsonMikrotikSelected() (blob download, filename from Content-Disposition, read_missing=true + same progress chart polling); new RbIcon "json"
- Test: scripts/test_json_export_route_report.py — JSON happy path (count/fields/row values incl. multiline log + read status), rows keyed exactly by the 19 fields, read_missing no-probe path, 400 paths, non-MikroTik exclusion

Stage Summary:
- CSV and JSON MikroTik exports now share one row builder, so both always carry identical data in the same Persian fields

---
Task ID: 14
Agent: main (Z.ai)
Task: «گزارش روت» — tracert route report of filtered MikroTik devices as CSV

Work Log:
- new backend/route_report.py: which_tracer_tool() (tracert on Windows / traceroute / tracepath), build_command() (tracert -d -h N -w ms | traceroute -n -m N -w s -q 1 | tracepath -n -m N), tolerant parse_trace_output() for all three formats (hop no, IP, latency, Persian status: پاسخ داد / بدون پاسخ (timeout) / غیرقابل‌دسترس), trace_route(), trace_many() (ThreadPool, order preserved, deduped) and build_route_report_csv() (UTF-8 BOM, 7 Persian columns: IP مبدأ، IP مقصد، نام دستگاه، شماره مرحله، IP مرحله، تاخیر (ms)، وضعیت)
- backend/main.py: POST /devices/route-report.csv + RouteReportBody (ips, source_ip default 172.19.1.6, dest_ip default 172.19.1.6, max_hops 1..30 default 15, timeout_ms, max_workers) — traces the route to EACH filtered MikroTik device IP (`tracert -d ip_device`), records user-provided مبدأ/مقصد in the report, and when مبدأ≠مقصد additionally traces the مبدأ→مقصد base route at the top of the report; 400 Persian errors for empty/no-MikroTik selections; headers X-Route-Devices / X-Route-Hops
- frontend/src.jsx: new button «گزارش روت» in the خروجی group → openRouteModal() fetches ALL devices matching the CURRENT report search filter (limit 100000, client-side MikroTik filter) and opens a dialog with IP مبدأ / IP مقصد (both default 172.19.1.6) + حداکثر Hop select; submitRouteReport() downloads route_report_{stamp}.csv; new RbIcon "route"; dialog explains that traces run from the app server and can take minutes
- AGENTS.md: feature map updated (JSON export + route report), new test script listed; README.md: API list + two new sections «خروجی JSON دستگاه‌های میکروتیک انتخاب‌شده» و «گزارش روت (tracert)»
- frontend/dist rebuilt (vite)
- Test: scripts/test_json_export_route_report.py extended with route-report suite + parser unit checks (real Windows tracert -d / Linux traceroute -n / tracepath samples) — live trace to 127.0.0.1 device verified (single instant hop, X-Route-Devices, BOM, exact 7-column header, base-route block when مبدأ≠مقصد, 400 paths) — ALL PASS; existing suites re-run: test_export_mikrotik_csv.py ALL PASS, test_api_probe_progress.py ALL PASS, unit 15/15 OK

Stage Summary:
- Route report button now traces every MikroTik device matching the report filter with tracert -d equivalents and saves a Persian CSV; source/destination asked from the user with 172.19.1.6 defaults
- Ready to push to GitHub origin/main (together with Task 10..13 commits)
---
Task ID: 15
Agent: main (Z.ai)
Task: «گزارش مسیر تا روتر مرکزی» در گزارش هوشمند — توپولوژی PDF یک‌صفحه‌ای per device

Work Log:
- new backend/route_topology.py: collect_topology_info() (structured read of identity/resource/interfaces/ip addresses/MNDP neighbors/routes/arp via RouterOS API 8728 using the user-supplied credentials), collect_topology_info_many() (ThreadPool up to 16 workers, ordered results, live progress dict {total,done,ok,failed,current_ip}, cooperative cancel), ip helpers (subnet matching, gateway parsing "ip%iface,ip2"), build_topology() (nodes from queried devices + ghost nodes from MNDP + virtual core node; edges from MNDP neighbor address→peer interface lookup, shared-subnet matching, route-gateway→central-IP; BFS shortest path device→core; per-hop interface mapping A[if,ip]↔B[if,ip] with evidence mndp/subnet/route; main_ip = interface IP toward core), next_hop_evidence() for the PDF
- new backend/route_pdf.py: ReportLab one-page-per-device A4 PDF mirroring the user's "Detailed Router Path Topology" sample — navy header band (Router i of N / Target / Core Router), Router Information 2-col grid (name, main IP, type, ping, open ports, tags, RouterOS, board, uptime, interface count), "IP Addresses & Interfaces" table, 3-column Interfaces grid with up/down state, Shortest Path box diagram with "iface <-> iface" connector labels + MNDP/SUBNET/ROUTE evidence tags, Hop-by-Hop Link Verification table, Routing & Adjacency Evidence lines, footer; "CONNECTION FAILED" banner pages keep DB-known info for unreachable devices; all text sanitized to Latin-1 (Helvetica core font); lists truncated with "... and N more" so a page can never overflow
- backend/main.py: RouteTopologyRequest (database, optional ips, central_router_ip default 172.19.1.6, username, password, port/timeout/max_workers/max_devices≤200) + TOPOLOGY_STATE/TOPOLOGY_CANCEL + _select_topology_targets() (explicit ips or every MikroTik of the chosen DB) + background worker; endpoints POST /api/reports/route-topology/start (409 if one already running, 422 bad IP, 404 unknown DB, 400 no MikroTik), GET /progress (percent/ok/failed/current_ip/phase/ready), POST /cancel, GET /result.pdf (attachment route_topology_{stamp}.pdf + X-Topology-Devices/Reachable/Unreachable/Failed/Links/Database/Central-Router headers)
- frontend/src.jsx: new RouteTopologyReport section in the «گزارش هوشمند» tab (database select + IP روتر مرکزی 172.19.1.6 + نام کاربری/رمز عبور API + «ایجاد گزارش مسیر (PDF)» + «توقف»), 1.2s progress polling with live phase/counts/percent bar, auto-download of the finished PDF; useRef added to the React import; dist rebuilt (index-DikK0gVg.js)
- backend/requirements.txt: + reportlab==4.2.5
- scripts/test_route_topology_unit.py (19 graph/BFS/interface-mapping checks, no network) and scripts/test_route_topology_pdf.py (28 E2E checks: 404 idle, 400/422/404 validation, monkeypatched collector happy path → 3-page PDF with correct X-Topology-* headers, cancel-when-idle, all-connection-failed still 3 pages); also fixed pre-existing hardcoded "/home/z/my-project/backend" sys.path in 6 older scripts (test_auth/test_flap_csv/test_search_and_db/diag_http/diag_flap/cleanup_test_dbs) to a relative path — all suites now pass
- AGENTS.md (module map, feature map Task 15, PDF gotchas) + README.md (new section «گزارش مسیر تا روتر مرکزی (توپولوژی PDF)»)

Stage Summary:
- The Smart Reports tab can now build a per-device PDF topology report: real path from every MikroTik device to the user-entered core router IP with exact interface-to-interface links, IPs, neighbors and interfaces of every device — sample output verified visually (3 pages: edge router, core router, connection-failed page)

---
Task ID: 16
Agent: main (Z.ai)
Task: «انتخاب دستگاه‌ها از دیتابیس» — جستجو/فیلتر/انتخاب چندگانه برای گزارش مسیر

Work Log:
- backend/main.py: GET /devices پارامتر اختیاری `database` گرفت (اعتبارسنجی با _resolve_report_database → 404 برای نام ناشناخته، db_path به db.query_devices) تا فهرست دستگاه‌های هر دیتابیس کاتالوگ — نه فقط دیتابیس فعال — قابل دریافت باشد
- backend/route_topology.py FIX (باگ Task 15): collect_topology_info_many دیگر فلگ running پیشرفت را نمی‌نویسد (قبلاً پس از پایان خواندن running=False می‌شد در حالی که فازهای graph/pdf هنوز در جریان بود؛ نتیجه: فرانت‌اند polling را زودتر قطع و PDF را نمی‌گرفت) — مالک running فقط worker گزارش است
- frontend/src.jsx: کامپوننت جدید DevicePickerModal (مودال RTL با کلاس‌های modal-* موجود): دریافت فهرست از /devices?database=…&limit=100000&sort=ip؛ جستجوی آزاد کلاینت‌ساید (IP/نام/تگ/نوع/دسته)، فیلتر «فقط دستگاه‌های میکروتیک» (همان قاعدهٔ isMikrotik: classification یا پورت 8291/8728) و «فقط پینگ‌خورده»؛ لیست با چک‌باکس (نمایش ۳۰۰ ردیف اول + هشدار شمارشی)، «انتخاب همه موارد فیلترشده»، «حذف انتخاب‌ها»، شمارندهٔ زنده، سقف ۲۰۰ دستگاه با خطای قرمز و غیرفعال‌شدن تایید
- frontend/src.jsx: بخش «گزارش مسیر تا روتر مرکزی» دکمهٔ «انتخاب دستگاه‌ها از دیتابیس» + چیپ وضعیت گرفت («انتخاب دستی: N دستگاه ✕» یا «همه دستگاه‌های میکروتیک دیتابیس (حداکثر ۸۰)»)؛ startReport با انتخاب دستی ips + max_devices=min(200,max(80,N)) می‌فرستد؛ تغییر دیتابیس انتخاب را پاک می‌کند
- frontend/style.css: استایل‌های device-picker-modal/list/row/tag/class
- frontend/dist بازسازی شد (index-C7AVjBVp.js)
- scripts/test_device_picker.py (۱۸ بررسی): پارامتر database در /devices (دیتابیس‌های A/B موقت، پیش‌فرض فعال، 404)، فیلترها با database (classification/q/ping_ok)، گزارش مسیر با انتخاب صریح (حذف غیرمیکروتیک، devices=2، X-Topology-Devices=2، ۲ صفحه PDF)، سقف max_devices، 400 برای انتخاب فقط-غیرمیکروتیک — ALL PASS؛ رگرسیون: test_route_topology_pdf/unit، test_export_mikrotik_csv، test_json_export_route_report، test_api_probe_progress، test_search_and_db، pytest tests/ (20) — همه PASS
- AGENTS.md (فهرست تست‌ها، feature map، گاتچا مالکیت running) + README.md (پارامتر database در API، بند «انتخاب دستگاه‌ها از دیتابیس» در بخش گزارش مسیر)

Stage Summary:
- کاربر می‌تواند در گزارش هوشمند، از لیست دستگاه‌های دیتابیس انتخاب‌شده جستجو/فیلتر کند و فقط زیرمجموعه‌ای از دستگاه‌های میکروتیک را برای «گزارش مسیر تا روتر مرکزی» برگزیند (بدون انتخاب = رفتار قبلی)
- باگ رقابتی پیشرفت گزارش مسیر (قطع‌شدن زودهنگام polling در فاز graph/pdf) رفع شد
---
Task ID: 17
Agent: main (Z.ai)
Task: نمودار پیشرفت انتقال کانفیگ گروهی + دکمه «انتخاب همه فیلترشده‌ها» + یافتن مسیر روتر مرکزی با روت پیش‌فرض و hop بالادست

Work Log:
- (تکمیل کار نیمه‌تمام R7) frontend/src.jsx: نمودار پیشرفت زندهٔ انتقال کانفیگ رندر شد (بلوک `cfg-progress` زیر نوار ابزار، مشترک برای «انتقال کانفیگ» و «کانفیگ گروهی»): نوار درصد سه‌بخشی (سبز موفق / قرمز ناموفق / خاکستری باقی‌مانده)، شمارنده‌های کل/موفق/ناموفق/باقی‌مانده، «در حال اجرا: IP فعلی»، شبکهٔ خانه‌های کوچک به ازای هر دستگاه (تا ۴۰۰ خانه؛ tooltip = IP + علت)، دکمهٔ «توقف انتقال» در حین اجرا و جدول «جزئیات نتایج» پس از پایان با علت فارسی هر خطا؛ دکمهٔ «تلاش مجدد فقط ناموفق‌ها» حالا از state جدید `cfgLast` (آخرین ips/user/pass/script هر اجرا) استفاده می‌کند تا در حالت quick هم درست کار کند؛ دکمه‌های پنل کانفیگ گروهی به‌جای snmpBusy از cfgBusy غیرفعال می‌شوند
- backend (از جلسهٔ قبل، اینک تست و کامیت شد): `POST /api/devices/push-config/start|progress|cancel` با worker پس‌زمینهٔ موازی (`push_config_many_parallel` تا ۱۶ رشته، توقف مشارکتی `CFG_PUSH_CANCEL`، مالک فلگ running فقط worker — درس Task 16) و `classify_push_error` برای دسته‌بندی فارسی خطاها (timeout → «سرویس api فعال نیست یا پورت 8728 فیلتر است»، refused، unreachable، credentials/policy، reset، trap/syntax)
- frontend/src.jsx: دکمهٔ جدید «انتخاب همه فیلترشده‌ها (N)» در گروه «دستگاه‌ها» (`selectAllFiltered`) — همهٔ دستگاه‌های منطبق با فیلتر جاری در همهٔ صفحات انتخاب می‌شوند (همان params بدون offset با limit=100000)؛ چک‌باکس هدر جدول همچنان فقط صفحهٔ جاری؛ آیکون جدید `select` در RbIcon؛ frontend/style.css: استایل‌های `cfg-progress/cfg-bar/cfg-seg/cfg-stats/cfg-cells/cfg-results` + sticky header جدول نتایج
- backend/route_topology.py — یافتن مسیر روتر مرکزی با روش بهتر (درخواست کاربر بر اساس PDF نمونه که دو روتر «unreachable» داشتند با وجود روت‌های پیش‌فرض): تابع جدید `_route_next_hops()` (اول طولانی‌ترین پیشوندِ منطبق با IP مرکزی با کم‌ترین distance و پشتیبانی ECMP، وگرنه روت پیش‌فرض 0.0.0.0/0 با کم‌ترین distance = hop بالای دستگاه)؛ بخش 3-ج بازنویسی شد: یال‌های روتینگ همیشه ساخته می‌شوند (قبلاً فقط وقتی core خوانده نشده بود)، گیت‌وی → یال مستقیم به core (gw==central) یا به دستگاه خوانده‌شدهٔ دارای آن IP (زنجیرهٔ بالادست بین روترها) یا گرهٔ شبح جدید `g:<ip>` با فلگ `upstream`؛ `_addr_iface_toward()` اینترفیس/IP سمت دستگاه روی لینک گیت‌وی را پیدا می‌کند؛ اولویت شواهد mndp > subnet > route > default؛ روتر مرکزی خودش در 3-ج پردازش نمی‌شود؛ برای دستگاه‌های unreachable «زنجیرهٔ بالادست best-effort» (حداکثر ۶ گام، مقاوم به حلقه) در `path["upstream"]` + `summary["upstream_only"]`
- backend/route_pdf.py: برای دستگاه‌های unreachable با زنجیرهٔ بالادست، نمودار باکس‌های کهربایی «Best-effort upstream path (via default route / longest prefix)» با برچسب DEFAULT-ROUTE/ROUTE و یادداشت «Evidence ends at …» اضافه شد؛ برچسب‌های شواهد DEFAULT-ROUTE در نمودار مسیر و «Default-route gateway» در جدول hop-by-hop؛ شمارندهٔ Shortest Path حالت جدید «(unreachable - best-effort upstream path shown)»؛ خط اول شواهد با next-hopِ زنجیرهٔ بالادست علامت «<< next-hop» می‌گیرد
- scripts/test_push_config_progress.py (جدید، ۲۱ بررسی): اعتبارسنجی start (اسکریپت خالی/ips خالی)، اجرای موازی با فیک push (۲ موفق + ۱ timeout → علت فارسی در results)، فیلدهای progress (total/done/ok/failed/percent/remaining/current_ip/running/ready)، 409 برای اجرای هم‌زمان، توقف مشارکتی وسط کار (علت «متوقف شد»)، cancel-when-idle، و unit checks دسته‌بندی خطا — ALL PASS؛ نکتهٔ تست: پچ باید روی هر دو شیء ماژول routeros_api (`import routeros_api` و `appm.routeros_api`) انجام شود وگرنه اتصال واقعی می‌زند (در AGENTS.md ثبت شد)
- scripts/test_route_topology_unit.py: انتظار ev یال گیت‌ویِ روت پیش‌فرض از "route" به "default" به‌روز شد + ۱۳ بررسی جدید: longest-prefix بر default مقدم است، ECMP، کم‌ترین distance، زنجیرهٔ A→B→core از طریق گیت‌وی پیش‌فرضِ دستگاه خوانده‌شده، زنجیرهٔ بالادست best-effort با گرهٔ شبح (سناریوی RB-Salmaneh از PDF کاربر)، شمارش upstream_only و پایان یافتن حلقهٔ روتینگ — ALL PASS
- frontend/dist بازسازی شد (index-0Z7sqtqm.js)؛ AGENTS.md (تست‌ها، نقشهٔ قابلیت Task 17، گاتچای پچ دوماژولی) + README.md (بخش جدید «انتخاب همه دستگاه‌های فیلترشده و انتقال کانفیگ گروهی»، به‌روزرسانی بخش توپولوژی) 
- رگرسیون: test_route_topology_pdf/unit، test_device_picker، test_export_mikrotik_csv، test_json_export_route_report، test_api_probe_progress، test_search_and_db، pytest tests/ (20) — همه PASS

Stage Summary:
- انتقال کانفیگ گروهی نمودار پیشرفت زندهٔ کامل دارد: درصد، تفکیک موفق/ناموفق/باقی‌مانده، خانهٔ هر دستگاه، علت فارسی خطا برای هر IP (پاسخ به «با وجود فعال بودن api/winbox برخی دستگاهها کانفیگ ناموفق است» — حالا مشخص می‌شود چرا) و تلاش مجدد فقط ناموفق‌ها
- کاربر می‌تواند با یک کلیک همهٔ نتایج فیلترشده (همهٔ صفحات) را انتخاب و روی همه با هم کانفیگ گروهی اجرا کند
- گزارش مسیر حالا از روت پیش‌فرض و hop بالای دستگاه‌ها برای یافتن مسیر روتر مرکزی استفاده می‌کند: دستگاه‌هایی که قبلاً «unreachable» بودند یا مسیر کامل می‌گیرند (وقتی گیت‌ویشان بین دستگاه‌های اسکن‌شده باشد) یا دست‌کم زنجیرهٔ بالادست تا سرِ شواهد نمایش داده می‌شود
---
Task ID: 18
Agent: main (Z.ai)
Task: بارگذاری کانفیگ روتر مرکزی سیسکو برای «گزارش مسیر تا روتر مرکزی»

Work Log:
- کاربرد: روتر مرکزی شبکه کاربر سیسکو است و از RouterOS API خوانده نمی‌شود؛ کاربر می‌خواهد کانفیگ آن را بارگذاری کند تا در یافتن مسیر دستگاه‌ها تا روتر مرکزی استفاده شود
- backend/cisco_config.py (جدید): parse_cisco_config برای کانفیگ متنی IOS/IOS-XE — اینترفیس‌ها (فیزیکی، زیراینترفیس dot1Q با vlan، SVI، Loopback، Tunnel، Port-channel) با description/shutdown/vrf، آدرس‌های IP اصلی و secondary با تبدیل ماسک به پیشوند، روت‌های استاتیک (پشتیبانی vrf، گیت‌وی IP یا اینترفیس، ECMP، distance، name) و ساب‌نت‌های connected؛ توابع کمکی find_connected_iface (طولانی‌ترین پیشوند، رد shutdown، ترجیح primary)، routes_toward (longest-first)، central_ip_known، summary و looks_like_cisco_config (اعتبارسنجی سرانگشتی)؛ همه فقط با stdlib و خطوط نامفهوم نادیده گرفته می‌شوند
- backend/route_topology.py: build_topology پارامتر cisco گرفت — گرهٔ core (وقتی روتر مرکزی بین دستگاه‌های خوانده‌شده نباشد) با hostname/آدرس‌ها/اینترفیس‌های سیسکو غنی‌سازی می‌شود (_cisco_addresses/_cisco_interfaces در شکل RouterOS)؛ بخش جدید 3-د: گیت‌ویِ هر روت استاتیک سیسکو → یال core↔دستگاهِ دارای آن IP (شاهد cisco) یا گرهٔ شبح؛ گیت‌وی دستگاه‌ها اگر IP دقیق یا داخل ساب‌نت‌های سیسکو باشد به core وصل می‌شود (_core_iface_toward) — همین تغییر در _upstream_chain هم اعمال شد تا زنجیرهٔ بالادست به core ختم شود؛ اشتراک ساب‌نت (3-ب) حالا core را هم شرکت می‌دهد؛ helper جدید _arp_iface_toward برای اینترفیسِ گیت‌وی‌های off-link از جدول ARP؛ اولویت شواهد جدید: mndp > cisco > subnet > route > default (در _add_edge و BFS)؛ خروجی topo کلیدهای cisco (متادیتا + central_ip_found) و cisco_data و summary[cisco_loaded/cisco_hostname] را گرفت
- backend/route_pdf.py: هدر صفحه «Core Router: <hostname> (<ip>)» وقتی کانفیگ سیسکو استفاده شده؛ برچسب CISCO-ROUTE در نمودار مسیر، «Cisco static route» در جدول hop-by-hop؛ تابع _cisco_evidence_lines — روت‌های استاتیک سیسکو که ساب‌نتِ دستگاه را پوشش می‌دهند (همهٔ آدرس‌های دستگاه + main_ip بررسی می‌شوند، حداکثر ۳ خط) به ابتدای بخش Routing & Adjacency Evidence اضافه می‌شوند
- backend/main.py: کانفیگ در databases/cisco_central_config.txt ذخیره می‌شود (CISCO_CONFIG_PATH، دایمی بین اجراها)؛ اندپوینت‌های POST (multipart با فیلد file یا JSON با فیلد text، سقف ۲MB، اعتبارسنجی looks_like_cisco_config و خطاهای ۴۰۰/۴۱۳ فارسی) + GET (خلاصهٔ پارس‌شده + uploaded_at) + DELETE؛ worker گزارش کانفیگ را قبل از build_topology می‌خواند (خرابی کانفیگ گزارش را نمی‌بندد) و stats[cisco] + هدر X-Topology-Cisco را پر می‌کند
- frontend/src.jsx: دکمهٔ «بارگذاری کانفیگ روتر مرکزی (Cisco)» + input فایل مخفی (accept .txt/.cfg/.conf) + چیپ وضعیت سبز (hostname + تعداد اینترفیس/آدرس/روت + ✕ حذف) یا هشدار کهربایی «بارگذاری نشده»؛ وضعیت در mount از GET خوانده می‌شود؛ توضیح بخش به‌روزرسانی شد؛ frontend/dist بازسازی شد (index-CdCN61Nq.js)
- scripts/test_cisco_config.py (جدید، ۶۱ بررسی): پارس کانفیگ واقع‌گرایانه (۵ اینترفیس، secondary، dot1Q، shutdown، /۳۰، /۳۲، ۵ روت شامل vrf/interface-gw/distance/name)، helperها، اندپوینت‌ها (GET قبل/بعد، POST json/multipart/خطاهای ۴۰۰، DELETE)، E2E توپولوژی با کانفیگ ذخیره‌شده (X-Topology-Cisco=hostname، هر دو دستگاه reachable، CORE-ISR-4331 و GigabitEthernet0/0/1.200 و CISCO-ROUTE و «Cisco static route» و خطوط شواهد داخل PDF با pypdf/pdftotext) و همان اجرا بدون کانفیگ (هدر خالی، DEV-24 unreachable)؛ backup/restore کانفیگ واقعی کاربر در تست
- رگرسیون: test_route_topology_unit، test_route_topology_pdf، test_device_picker، test_push_config_progress، test_export_mikrotik_csv، test_json_export_route_report، test_api_probe_progress، test_search_and_db، pytest tests/ (۲۰) — همه PASS
- AGENTS.md (ماژول جدید، تست جدید، قابلیت Task 18، گاتچاهای وضعیت دایمی کانفیگ و استخراج متن PDF) + README.md (بند «بارگذاری کانفیگ روتر مرکزی (سیسکو)» و به‌روزرسانی شواهد پنج‌گانه)

Stage Summary:
- کاربر می‌تواند کانفیگ روتر مرکزی سیسکو را در تب گزارش هوشمند بارگذاری کند؛ گزارش مسیر حالا از ساب‌نت‌های connected و روت‌های استاتیک سیسکو برای یافتن مسیر و نمایش اینترفیس سمتِ مرکز استفاده می‌کند و گرهٔ روتر مرکزی با hostname و اینترفیس‌های واقعی در PDF ظاهر می‌شود

---

Task ID: 19
Agent: main (Z.ai)
Task: گزارش CSV دستگاه‌های ناموفق در کانفیگ گروهی

Work Log:
- کاربرد: در انتقال کانفیگ گروهی برخی دستگاه‌ها ناموفق می‌مانند (R7)؛ کاربر خواست فهرست ناموفق‌ها به‌صورت فایل CSV قابل دریافت باشد
- backend/main.py: اندپوینت جدید `GET /api/devices/push-config/failed-csv` — از `CFG_PUSH_STATE["results"]` آخرین اجرای کانفیگ گروهی فقط ردیف‌های ناموفق (شامل متوقف‌شده‌های cancel با برچسب «متوقف شد») را برمی‌گرداند؛ هر ردیف با دیتابیس فعال غنی‌سازی می‌شود (نام دستگاه identity، نوع دستگاه، تگ — با fetch_devices_by_ips و سقوط نرم در صورت خطای دیتابیس)؛ ۹ ستون فارسی: ردیف، IP دستگاه، نام دستگاه (identity)، نوع دستگاه، تگ، وضعیت، علت (خروجی فارسی classify_push_error)، جزئیات خطا (متن خام)، زمان پایان اجرا؛ CSV با BOM (`\xef\xbb\xbf`) و filename=`config_failed_{stamp}.csv`؛ بدون اجرا یا بدون ناموفق → 404 با پیام فارسی؛ importهای stdlib `csv`/`io` اضافه شد
- backend/main.py: `CFG_PUSH_STATE["finished_at"]` جدید — در start به None ریست و در `finally`ِ `_cfg_push_worker` (هر سه مسیر done/canceled/error) با `datetime.now(timezone.utc).astimezone().isoformat()` پر می‌شود؛ ستون «زمان پایان اجرا» گزارش از همین مقدار می‌خواند
- frontend/src.jsx: تابع `downloadFailedCsv()` (الگوی دانلود blob مشابه exportExcelSelected با استخراج filename از Content-Disposition و پیام فارسی) + دکمهٔ «گزارش CSV ناموفق‌ها» در سرستون نمودار پیشرفت، کنار «تلاش مجدد فقط ناموفق‌ها»، فقط وقتی اجرا تمام شده و خطا > 0 است (هر دو مسیر «کانفیگ گروهی» و «انتقال کانفیگ» را پوشش می‌دهد)؛ frontend/style.css: کلاس `cfg-csv` (سبز، هم‌خانوادهٔ cfg-retry با margin-inline-start=6px تا جایگاه auto دکمهٔ retry حفظ شود)؛ frontend/dist بازسازی شد (index-DjVZ2_F6.js)
- scripts/test_push_config_failed_csv.py (جدید، ۲۸ بررسی): 404 قبل از اجرا با پیام فارسی، اجرای فیک (۲ موفق + timeout + refused)، 200/قواعد CSV (BOM، سرستون دقیق، فقط ناموفق‌ها، شماره‌گذاری از ۱)، علت فارسی هر دو خطا، غنی‌سازی از دیتابیس موقت (identity/type/tags) و خالی‌بودن برای IP ناشناس، finished_at پرشده، برچسب «متوقف شد» برای cancel، 404 پس از اجرای کاملاً موفق، مسدود بودن درخواست بدون احراز هویت؛ مقاوم‌سازی setup برای حذف باقی‌ماندهٔ دیتابیس تست از اجرای خراب (اگر فعال مانده باشد)
- رگرسیون: test_push_config_progress، test_route_topology_unit، test_device_picker، test_export_mikrotik_csv، test_cisco_config، pytest tests/ (20) — همه PASS

Stage Summary:
- پس از هر کانفیگ گروهی، کاربر با یک کلیک فایل CSV فقط دستگاه‌های ناموفق را با نام و تگ و علت فارسی خطا می‌گیرد و می‌تواند برای پیگیری/گزارش‌دهی از آن استفاده کند

---

Task ID: 20
Agent: main (Z.ai)
Task: رفع «موفقِ» کاذب در کانفیگ گروهی — تأیید پس از اعمال (باگ گزارش‌شدهٔ کاربر: دستگاه اعلام موفق می‌شود ولی کانفیگ اعمال نشده، api/winbox فعال و یوزر درست)

Work Log:
- ریشه‌یابی در backend/routeros_api.py: مسیرهای انتهایی run_script کور بودند — «/execute» و «/system/script/add + run» به‌محضِ «شروعِ» اسکریپت !done برمی‌گردانند و خطاهای داخل اسکریپت (user already exists، خطای نگارشی، [find] و ...) هرگز به فراخواننده نمی‌رسیدند → موفقِ کاذب؛ همچنین «set [find ...]» به‌اشتباه به sentence با ?query ترجمه می‌شد که در API فقط روی print مجاز است
- backend/routeros_api.py — اجرای قابل‌اتکا: مسیر /execute حذف شد؛ اسکریپت‌های کنسولی داخل «:do { ... } on-error={ :set NetScanPushXXXX "failed" }» پیچیده می‌شوند و ابتدای اسکریپت وضعیت "running" و پایانِ موفق "ok" در یک متغیر global یکتا (NetScanPush+هشت‌کاراکتر تصادفی) نوشته می‌شود؛ وضعیت با poll روی /system/script/environment/print خوانده می‌شود (هر ۰٫۴ ثانیه، سقف PUSH_STATUS_TIMEOUT=30s)؛ failed → خطای فارسی «اسکریپت روی دستگاه خطا داد (on-error)»؛ بدون وضعیت → «وضعیت اجرای اسکریپت در زمان مجاز خوانده نشد»؛ پاک‌سازی متغیر (با .id از print) و حذف اسکریپت موقت در finally
- backend/routeros_api.py — پارسر: _parse_terminal_line بازنویسی شد → خروجی (sentence, path_def) با معنای «خط ادامهٔ» کنسول (/snmp community و set بعدی یک دستورند)؛ «[find ...]» روی set/remove/enable/disable دیگر ترجمه نمی‌شود و به مسیر کنسول می‌رود (فقط روی print با ?query مجاز)؛ unquote مشترک (_unquote) برای رمزهای داخل کوتیشن مثل password="Olom@2026$"
- backend/routeros_api.py — تأیید پس از اعمال: _extract_verify_intents از متن خام اسکریپت تغییراتِ وعده‌داده را درمی‌آورد (user add/set با name+password، system identity set، snmp set enabled، ip service enable/disable با numbers/اسم ساده) و verify_push همان وضعیت را دوباره می‌خواند: کاربر = اتصال مجدد و login با همان نام/رمز (قوی‌ترین مدرک)، identity = /system/identity/print، snmp = /snmp/print، سرویس = /ip/service/print؛ عدمِ تطبیق → (False, جزئیات فارسی)
- push_config: پس از اجرای موفق verify می‌کند؛ verified=False → نتیجه «ناموفق» با reason=«کانفیگ اجرا شد اما تأیید اعمال نشد: ...» و error="verify: ..." (در progress/CSV/retry خودکار شمرده می‌شود)؛ ok=True با verified=True/None؛ except عمومی حالا reason دسته‌بندی‌شده هم دارد؛ _one دیگر reason موجود را بازنویسی نمی‌کند؛ classify_push_error: الگوی «already have such user» → «کاربر از قبل روی دستگاه وجود دارد — برای تغییر رمز از set استفاده کنید»
- frontend/src.jsx + style.css: ستون جدید «تأیید اعمال» در جدول «جزئیات نتایج» — نشان «تأیید شد» (سبز) / «اعمال نشد» (قرمز) / «—» (بدون قصدِ قابل‌تأیید) با کلاس cfg-verify؛ frontend/dist بازسازی شد (index-DcuW4mST.js)
- scripts/test_push_verification.py (جدید، ۳۷ بررسی): لایهٔ فیک talk/connect/close با لاگین plaintext+challenge و md5 واقعی؛ سناریوی دقیق کاربر (دستگاه done می‌گوید ولی کاربر نمی‌سازد → نهایتاً «ناموفق» با علت فارسی)، کاربر واقعاً ساخته‌شده، identity/snmp اعمال‌شده و نشده، اسکریپت کنسول (wrapper روی :do/on-error در source ثبت‌شده، وضعیت ok/failed/هرگز)، سقف timeout کوتاه‌شده، اجرای موازی از API (۱ موفق + دروغ‌گو + refused → failed=2) و اتصال به CSV ناموفق‌های Task 19 — ALL PASS
- رگرسیون: test_push_config_progress، test_push_config_failed_csv، test_route_topology_unit، pytest tests/ (20) — همه PASS

Stage Summary:
- «موفق» در کانفیگ گروهی حالا یعنی «اجرا شد و نتیجه‌اش روی دستگاه تأیید شد»؛ دستگاه‌های دروغ‌گو (done بدون اعمال) با علت فارسی در نمودار پیشرفت، جدول نتایج، ستون «تأیید اعمال» و گزارش CSV ناموفق‌ها دیده می‌شوند و دکمهٔ «تلاش مجدد فقط ناموفق‌ها» آن‌ها را هم پوشش می‌دهد

---

Task ID: 21
Agent: main (Z.ai)
Task: گزارش CSV «دلیل نرسیدن» هر روتر به روتر مرکزی + بررسی همهٔ اینترفیس‌ها/IPهای هر روتر در مسیریابی

Work Log:
- کاربرد: کاربر گزارش کرد در گزارش مسیر تا روتر مرکزی برخی روترها به مرکز نمی‌رسند و دلیل را در فایل CSV می‌خواهد؛ یادآوری کرد که هر روتر چند IP روی اینترفیس‌های مختلف دارد و «تمام اینترفیس‌ها و IPهای آن برای مسیریابی باید چک شوند»
- backend/route_topology.py — بررسی همهٔ مسیرها: `_route_all_next_hops()` جدید — برخلاف `_route_next_hops` (فقط بهترین روت)، گیت‌وی‌های «همهٔ» روت‌های پوشش‌دهندهٔ IP مرکزی (روت خاص هر اینترفیس، روت‌های جایگزین با distance بدتر، روت پیش‌فرض) را مرتب‌شده (پیشوند بلندتر ← distance کمتر ← ترتیب جدول) و بدون تکرار برمی‌گرداند؛ گیت‌وی اینترفیسی (مثل "ether5") قابل دنبال‌کردن نیست و حذف می‌شود (قبلاً گرهٔ شبح بی‌معنی می‌ساخت)؛ بخش 3-ج حالا برای همهٔ کاندیدها یال می‌سازد و `_upstream_chain` همهٔ کاندیدها را امتحان می‌کند (اولین گیت‌وی که به دستگاه شناخته‌شده یا core برسد انتخاب می‌شود؛ gw==central صریحاً به core می‌رود)
- backend/route_topology.py — تحلیل دلیل: `_upstream_chain` حالا `(chain, end)` برمی‌گرداند و دلیلِ پایان زنجیره را در `path["upstream_end"]` ثبت می‌کند (core/ghost/loop/max/no-route/unknown-node)؛ `interface_route_verdicts()` تک‌تک آدرس‌های IP هر اینترفیس را برای مسیر به مرکز بررسی می‌کند — verdict مستقیم (مرکز در ساب‌نت همین IP) / روت خاص از گیت‌وی در ساب‌نت همین IP / فقط روت پیش‌فرض / هیچ — به‌همراه وضعیت اینترفیس (disabled → «غیرفعال»، running=false → «اتصال فیزیکی ندارد (no link)») و دیده‌شدن گیت‌وی در ARP؛ `unreachable_reason_rows(topo)` برای هر دستگاه unreachable ردیف CSV با دلیل فارسی می‌سازد: خوانده‌نشدن دستگاه (canceled → «بررسی متوقف شد»؛ بقیه با classify_push_error: timeout/refused/credentials/…)، روتر مرکزی شناسایی‌نشده (جزئیات)، بدون آدرس IP، جدول روتینگ خالی، بدون روت پوشش‌دهنده، گیت‌وی خارج از ساب‌نت همهٔ اینترفیس‌ها (recursive)، اینترفیس خروجی قطع/غیرفعال (اگر تنها ایگرس سالم نباشد → دلیل اصلی)، پایان زنجیره در گیت‌وی ناشناخته، حلقهٔ روتینگ، دستگاه بعدی بدون روت، بیش از ۶ گام + جزئیات («تمام N آدرس IP روی M اینترفیس بررسی شد»، هشدار ARP، هشدار اینترفیس قطع کنار ایگرس سالم)؛ `_route_next_hops` قدیمی برای سازگاری تست‌ها باقی است
- backend/main.py: worker گزارش بعد از build_topology ردیف‌ها را می‌سازد و در `TOPOLOGY_STATE["unreachable_rows"]` ذخیره می‌کند (خطای تحلیل گزارش را نمی‌بندد — `unreachable_error`)؛ start آن را ریست می‌کند؛ `progress` فیلد `unreachable` (از stats) را برمی‌گرداند؛ اندپوینت جدید `GET /api/reports/route-topology/unreachable-csv` — فقط دستگاه‌های بدون مسیر آخرین گزارش، ۱۲ ستون فارسی (ردیف، IP، نام (identity)، نوع، تگ، وضعیت، تعداد اینترفیس/آدرس، اینترفیس‌ها و آدرس‌های IP، نتیجهٔ بررسی هر اینترفیس، دلیل اصلی، جزئیات، زمان تولید)، BOM، filename=`route_unreachable_{stamp}.csv`، 409 حین اجرا و 404 بدون ردیف/بدون گزارش با پیام فارسی
- frontend/src.jsx: دکمهٔ «گزارش CSV دلایل نرسیدن به مرکز» کنار «ایجاد گزارش مسیر (PDF)» (فقط وقتی گزارش در حال اجرا نیست؛ 404 → پیام فارسی که همه مسیر داشته‌اند) با `downloadUnreachableCsv()` (الگوی blob + filename از Content-Disposition)؛ پیام پس از PDF حالا تعداد «بدون مسیر به مرکز» را از progress.unreachable نشان می‌دهد؛ توضیح بخش به‌روزرسانی شد (بررسی همهٔ اینترفیس‌ها/IPها)؛ frontend/style.css: `.topo-csv` سبز؛ frontend/dist بازسازی شد (index-BphxalUT.js)
- scripts/test_route_unreachable_csv.py (جدید، ۶۷ بررسی): unit — `_route_all_next_hops` (همهٔ روت‌ها/ترتیب/dedup/حذف گیت‌وی اینترفیسی)، `interface_route_verdicts` (direct/route/default/none + no-link + disabled + ARP + IP نامعتبر)، `unreachable_reason_rows` برای ۷ سناریو (ghost، حلقه، timeout، canceled، بدون آدرس، جدول خالی، بدون روت پوشش‌دهنده، اینترفیس قطع، گیت‌وی off-subnet)؛ E2E — اجرای ۶ دستگاه فیک از API (R-OK قابل دسترس + ۵ سناریوی ناموفق)، progress.unreachable=5، CSV: BOM/سرستون ۱۲گانه/فقط ناموفق‌ها/شماره‌گذاری/غنی‌سازی نوع و تگ از دیتابیس/دلیل فارسی هر سناریو/— برای دستگاه خوانده‌نشده، اجرای دوم تک‌دستگاههٔ همه-reachable → 404، مسدود بودن بدون احراز هویت؛ backup/restore کانفیگ سیسکوی واقعی + reset_state با unreachable_rows
- scripts/make_unreachable_csv_sample.py (جدید): تولید نمونهٔ واقعی ۵ردیفی از مسیر اندپوینت → download/نمونه-گزارش-CSV-دلایل-نرسیدن-به-روتر-مرکزی.csv
- رگرسیون: test_route_topology_unit (30)، test_route_topology_pdf (26)، test_cisco_config (62)، test_device_picker (17)، test_push_config_progress (27)، test_push_config_failed_csv، test_push_verification، test_export_mikrotik_csv، test_json_export_route_report، test_api_probe_progress، test_search_and_db، pytest tests/ (20) — همه PASS

Stage Summary:
- گزارش مسیر حالا «تمام» اینترفیس‌ها و IPهای هر روتر را برای مسیریابی به مرکز چک می‌کند (همهٔ روت‌های پوشش‌دهنده، نه فقط بهترین) و برای هر روتری که نمی‌رسد، دلیل دقیق فارسی — از جدول روتینگ خالی و اینترفیس قطع تا گیت‌وی ناشناخته و حلقه — همراه با نتیجهٔ بررسی تک‌تک اینترفیس‌ها در یک فایل CSV قابل دریافت می‌دهد

---

Task ID: 22
Agent: main (Z.ai)
Task: مهر تاریخ و ساعت جاری سیستم در انتهای نام تمامی فایل‌های CSV پروژه

Work Log:
- کاربرد: کاربر خواست روی نام تمامی فایل‌های CSV پروژه، تاریخ و ساعت جاری سیستم در انتهای نام ثبت شود (دانلودهای چندباره یکدیگر را بازنویسی نکنند و زمان تولید از نام فایل مشخص باشد)
- backend/main.py — helper مشترک `file_stamp()`: ساعت لوکال سیستم با الگوی `%Y%m%d_%H%M%S`؛ هر ۸ نقطهٔ تولید CSV به آن متصل شد:
  - چهار مسیرِ فاقد مهر مهردار شدند: `GET /devices/export.csv` (→ `devices_{stamp}.csv` / `new_devices_{stamp}.csv`)، `GET /scans/{id}/reports/{key}` (→ `{key}_{stamp}.csv`)، `GET /reports/interface-flaps/export.csv` (→ `interface_flaps_report_{stamp}.csv`)، `GET /reports/wireless-antenna-issues/export.csv` (→ `wireless_antenna_issues_{stamp}.csv`)
  - چهار CSVِ قبلاً مهردار (`export-mikrotik.csv`، `route-report.csv`، `unreachable-csv`، `failed-csv`) از `datetime.now(timezone.utc)` به `file_stamp()` (ساعت سیستم) منتقل شدند تا با خواست کاربر («ساعت جاری سیستم») یکی باشند
  - خروجی‌های غیر CSV (xlsx، json، pdf، zip، db) عمداً بدون تغییر ماندند
- frontend/src.jsx — helper ماژول‌Level `csvStamp()` (هم‌قالب با بک‌اند) + دو رفع باگ واقعی: دانلودرهای «گزارش هوشمند نوسان اینترفیس» و «قطع و وصل آنتن‌ها» نام سرور را نادیده می‌گرفتند و نام هاردکد (`interface_flaps_report.csv` / `wireless_antenna_issues.csv`) را بازنویسی می‌کردند — حالا از `Content-Disposition` می‌خوانند؛ fallbackهای `config_failed`/`mikrotik_selected`/`route_report`/`route_unreachable` هم مهرگرفتار شدند؛ frontend/dist بازسازی شد (index-C5oVXZPk.js)
- scripts/test_csv_filename_stamp.py (جدید، ۲۲ بررسی): unit `file_stamp` (قالب + تازگی <۵ثانیه)؛ E2E همهٔ ۸ نقطه: نام با الگوی `_YYYYMMDD_HHMMSS.csv`، مهر تازه (<۵دقیقه از now سیستم — اثبات «جاری» بودن)، دو دانلود با فاصلهٔ ۱٫۱ثانیه → نام متفاوت، new_only، مسیر گزارش اسکن با job تزریقی + csv_bytes پچ‌شده، route-report با trace پچ‌شده، unreachable/failed با تزریق وضعیت؛ restore کامل وضعیت (JOBS/CFG_PUSH_STATE/TOPOLOGY_STATE/csv_bytes/trace/db) — ALL PASS
- tests/test_csv_stamp.py (جدید، ۲ بررسی pytest): قالب و تازگی `file_stamp` + بررسی ساختاری که هر مسیر ختم‌به-csv در app از `file_stamp` استفاده می‌کند (≥۷ مسیر)
- رگرسیون: test_flap_csv، test_export_mikrotik_csv، test_json_export_route_report، test_push_config_failed_csv، test_route_unreachable_csv، pytest tests/ (22) — همه PASS

Stage Summary:
- تمامی فایل‌های CSV پروژه — از خروجی دستگاه‌ها و میکروتیک و گزارش روت تا گزارش‌های اسکن، نوسان اینترفیس، آنتن وایرلس، دلایل نرسیدن به مرکز و ناموفق‌های کانفیگ گروهی — اکنون نامی به شکل `{name}_YYYYMMDD_HHMMSS.csv` با تاریخ و ساعت جاری سیستم دارند؛ دانلود مجدد دیگر فایل قبلی را بازنویسی نمی‌کند و زمان تولید هر گزارش از نام آن خوانده می‌شود

---

Task ID: 23
Agent: main (Z.ai)
Task: روش مسیریابی جدید — جمع‌آوری کل IP اینترفیس‌ها + ای‌دی دستگاه‌ها و کشف hop بالاسری با default روت‌ها تا روتر مرکزی

Work Log:
- کاربرد: کاربر روش مسیریابی را اصلاح کرد — «اصولا برای مسیریابی قبلش اطلاعات کل IP اینترفیس‌ها به‌همراه ای‌دی دستگاه‌ها جمع‌آوری شود و با استفاده از default روت‌های دستگاه، hop بالاسری کشف شود تا به روتر مرکزی برسد»
- backend/route_topology.py — فاز صفر (جمع‌آوری پیش از مسیریابی) در build_topology: نقشهٔ مالکیت IP (`ip_owner`) — IP اتصال + «همهٔ» آدرس‌های اینترفیسی هر دستگاه (+ آدرس‌های کانفیگ سیسکوی مرکز) → کلید گره؛ هر گره `dev_id` (شناسهٔ ردیف دیتابیس) دارد؛ تطبیق «این گیت‌وی مالِ کدام دستگاه است» حالا از همین نقشه است (در یال‌های روتینگ 3-ج و `_upstream_chain`) به‌جای اسکن خطی
- backend/route_topology.py — اولویت default-اول: `_route_all_next_hops` کاندیدها را حالا به‌ترتیب «اول default روت‌ها (0.0.0.0/0؛ distance کمتر ← ترتیب جدول) بعد روت‌های خاص (پیشوند بلندتر ← distance کمتر)» برمی‌گرداند (قبلاً longest-prefix-first بود) — hop بالاسری با default روت کشف می‌شود و روت خاص فقط جایگزین/بدون-default است؛ helper جدید `_route_default_next_hops` فقط گیت‌وی‌های default را به همین ترتیب می‌دهد (گیت‌وی اینترفیسی حذف)
- backend/route_topology.py — BFS آگاه از default روت: `pref_edges`/`ordered_adj` — در هر گره، یالِ سمتِ گیت‌ویِ default (از روی نقشهٔ مالکیت) قبل از بقیهٔ یال‌ها (MNDP/subnet/route) امتحان می‌شود تا مسیر گزارش‌شده سلسله‌مراتب default روت‌ها را دنبال کند نه میان‌بر ساب‌نت همسایه یا روت خاص؛ BFS کامل روی همهٔ یال‌ها حفظ شده (اگر زنجیرهٔ default به core نرسد، جایگزین پیدا می‌شود)
- scripts/test_route_topology_unit.py — سناریوی جدید Task 23: D هم‌ساب‌نت S است ولی default گیت‌وی‌اش U است → مسیر باید D→U→core باشد نه D→S→core (۴ بررسی) + dev_id؛ scripts/test_route_unreachable_csv.py — بررسی‌های ترتیب برای default-اول + ۵ بررسی جدید `_route_default_next_hops` (فقط default، distance کمتر اول، بدون default → []، گیت‌وی اینترفیسی حذف)
- رگرسیون: test_route_topology_unit، test_route_unreachable_csv، test_route_topology_pdf، test_cisco_config، test_device_picker، pytest tests/ (22) — همه PASS
- مستندات: README.md (بازنویسی بخش «گزارش مسیر تا روتر مرکزی» با روش جدید) و AGENTS.md (بولت Task 23 + تیتر نقشه تا Task 23)

Stage Summary:
- کشف مسیر اکنون دقیقاً طبق روش کاربر کار می‌کند: اول همهٔ IPهای اینترفیس‌ها + ای‌دی دستگاه‌ها جمع‌آوری می‌شود (نقشهٔ مالکیت IP)، بعد hop بالاسری هر دستگاه از default روت‌های خودش (کم‌ترین distance، بعد ترتیب جدول) کشف و زنجیره تا روتر مرکزی دنبال می‌شود؛ مسیرِ گزارش‌شده دیگر از میان‌برهای ساب‌نت یا روت‌های خاص عبور نمی‌کند و فقط وقتی default وجود ندارد یا به جایی نمی‌رسد، از بقیهٔ شواهد (MNDP/ساب‌نت/روت خاص) به‌عنوان جایگزین استفاده می‌شود

---

Task ID: 24
Agent: main (Z.ai)
Task: ادامهٔ نمودار مسیر در سطر بعد — رفع بیرون‌زدگی دستگاه‌ها از کادر PDF گزارش مسیر و قابل رویت شدن روتر مرکزی

Work Log:
- کاربرد: کاربر با تصویر صفحهٔ PDF گزارش مسیر (دستگاه RB-Anbar-daruel-HapLite) گزارش داد «برخی از دستگاه‌ها از کادر بیرون می‌زند؛ ادامهٔ شکل در سطر بعد ادامه یابد تا روتر مرکزی قابل رویت باشد»
- ریشهٔ باگ در backend/route_pdf.py (`_path_diagram`): هر سطر per_row=3 hop یعنی ۴ جعبه دارد (شرط شکست سطر `col >= per_row + 1`) ولی gap با فرمول `(W − ۳×عرض)/۲` برای ۳ جعبه محاسبه می‌شد → عرض واقعی هر سطر ~۷۵۱pt در کادرِ ~۵۳۵pt؛ جعبهٔ چهارم هر سطر از لبهٔ صفحه بیرون می‌زد و روتر مرکزی (جعبهٔ آخر زنجیره) کاملاً بیرون صفحه می‌افتاد — هم در شاخهٔ reachable و هم در زنجیرهٔ upstream دستگاه‌های نارس
- backend/route_pdf.py — ثابت‌های هندسهٔ نمودار: `PATH_PER_ROW` (۳ hop در سطر)، `PATH_ROW_BOXES` (۴ جعبه)، `PATH_BOX_W` (۱۰۴) و `PATH_ROW_GAP = (PAGE_W − 2M − ۴×۱۰۴)/۳ ≈ ۳۹٫۸` → عرض سطر دقیقاً برابر کادر صفحه (۵۳۵٫۳pt)
- backend/route_pdf.py — `path_box_slot(i)`: موقعیت (سطر، ستون) جعبهٔ i-ام زنجیره؛ حلقهٔ رسم هر دو شاخه از row/col دستی به این تابع منتقل شد
- backend/route_pdf.py — `_row_wrap_connector()`: اتصال Z شکل ادامهٔ زنجیره به سطر بعد — از پایین جعبهٔ آخر سطر قبل پایین می‌آید، در فاصلهٔ بین دو سطر به چپ می‌رود (با برچسب لینک مثل «ether5 <-> ether1» و برچسب شاهد MNDP/SUBNET/ROUTE/DEFAULT-ROUTE/CISCO-ROUTE) و از بالای جعبهٔ اول سطر بعد وارد آن می‌شود؛ رنگ برچسب شاهد در شاخهٔ upstream کهربایی (مطابق برچسب‌های درون‌سطر همان شاخه)
- نمایش ۶ hop اول (۲ سطر × ۴ جعبه) مثل قبل حفظ شد تا «یک صفحه به ازای هر دستگاه» برقرار بماند؛ زنجیره‌های بلندتر همچنان با «... and N more link(s) to the core» خلاصه می‌شوند
- tests/test_route_pdf_wrap.py (جدید، ۵ تست): تساوی عرض سطر با کادر صفحه، شکست سطر در `path_box_slot`، سه پاره‌خط Z شکل + برچسب لینک/شاهد در اتصال، حالت بدون برچسب، و فراخوانده‌شدن اتصال در هر دو شاخهٔ reachable و upstream
- scripts/test_route_pdf_path_wrap.py (جدید، ۱۵ بررسی): بوم ضبط‌کنندهٔ ReportLab (roundRect/line/showPage) روی توپولوژی شبیه شبکهٔ واقعی کاربر (همان نام‌های تصویر پیوست، ۵ hop → ۶ جعبه) + دستگاه unreachable با زنجیرهٔ upstream ۵ hop + زنجیرهٔ ۹ hop؛ ثابت می‌شود هیچ جعبه‌ای خارج کادر نیست (بیشینهٔ x+w = 565.3 = لبهٔ کادر)، سطر اول ۴ جعبه و سطر دوم ۲ جعبه، اتصال Z شکل در گودال بین دو سطر روی هر دو صفحه و روتر مرکزی داخل کادر است؛ نمونهٔ PDF برای بازبینی بصری در /tmp/render/route_wrap_sample.pdf نوشته شد
- رگرسیون: pytest tests/ (۲۷) + unittest discover، test_route_topology_pdf، test_route_topology_unit، test_route_unreachable_csv، test_cisco_config — همه PASS؛ بازبینی بصری هر ۳ صفحهٔ نمونه با رندر JPEG (زنجیرهٔ wrap شده، upstream wrap شده، صفحهٔ خودِ روتر مرکزی)
- مستندات: README.md (بولت «نمودار مسیر همیشه داخل کادر صفحه است») و AGENTS.md (بولت Task 24 + تیتر نقشه تا Task 24)

Stage Summary:
- نمودار «Shortest Path» در PDF گزارش مسیر دیگر از کادر بیرون نمی‌زند: هر سطر دقیقاً داخل کادر صفحه جا می‌شود، زنجیره‌های بلند با اتصال Z شکل (با همان برچسب لینک و شاهد) به سطر بعد ادامه می‌یابند و روتر مرکزی (جعبهٔ سبز) همیشه داخل کادر و قابل رویت است — هم برای مسیرهای کامل و هم برای زنجیرهٔ upstream دستگاه‌هایی که به روتر مرکزی نمی‌رسند

---

Task ID: 25
Agent: main (Z.ai)
Task: اینونتوری IP اینترفیس‌ها + ای‌دی دستگاه‌ها در دیتابیس و پردازش لیست فیلترشدهٔ گزارش مسیر از روی آن + خوانا شدن برچسب اینترفیس‌های نمودار مسیر

Work Log:
- کاربرد: دو درخواست کاربر — «برای گزارش مسیریابی قبلش کل IPهای همهٔ اینترفیس‌های دستگاه‌ها به‌همراه ای‌دی دستگاه‌ها را در دیتابیس بخوان و بعد لیست فیلترشده را پردازش کن» و «طبق شکل پیوست، اینترفیس‌های دستگاه‌های سمت راست در نمودار مسیریابی مشخص نیست؛ اندازهٔ برچسب‌ها طوری تغییر کند که قابل خواندن باشند» (تصویر پیوست: صفحهٔ PDF 22Bahman-MK → KhezNabi-MK → SW-Wireless1 با برچسب‌های ریز و بریدهٔ «ether10 ↔…» و «CISCO-ROUTE»)
- backend/db.py — جدول جدید `device_interface_ips` در `_SCHEMA` (device_ip، device_id، identity، interface، address با ماسک، ip بدون ماسک، network، updated_at) + ایندکس‌های device_ip/ip؛ توابع جدید `replace_interface_inventory` (جایگزینی در سطح هر device_ip در یک تراکنش — دستگاه بدون ردیف تازه دست‌نخورده می‌ماند) و `load_interface_inventory`؛ `delete_devices` ردیف‌های اینونتوری دستگاه حذف‌شده را هم پاک می‌کند؛ `query_devices`/`fetch_devices_by_ips` حالا `id` (rowid ردیف devices) را هم برمی‌گردانند تا «ای‌دی دستگاه» واقعی و پایدار باشد
- backend/route_topology.py — `inventory_rows_from_infos(infos, devices)`: برای هر آدرس IP هر اینترفیسِ دستگاهِ سالمِ دارای آدرس یک ردیف با device_id/identity می‌سازد؛ دستگاه خوانده‌نشده یا بی‌آدرس عمداً ردیفی نمی‌گیرد تا اینونتوری قبلی‌اش در دیتابیس پاک نشود؛ `build_topology(..., inventory=None)` — فاز صفر حالا علاوه بر نقشهٔ زنده، مالکیت IP دستگاه‌های بدون آدرس زنده را از اینونتوری دیتابیس می‌گیرد (گیت‌ویِ دستگاهِ خطاخورده به دستگاه واقعی وصل می‌شود نه گرهٔ شبح) و گره‌های شبح hop بالادست با identity ثبت‌شده در دیتابیس نام‌گذاری می‌شوند (`from_inventory`/`inventory_dev_id`؛ helper داخلی `_ghost_node` در 3-ج و `_upstream_chain`)
- backend/main.py — فاز جدید `inventory` در `_route_topology_worker` بین collect و graph: ذخیره در دیتابیس فعال → خواندن کل اینونتوری از دیتابیس → پاس‌دادن به `build_topology` (پردازش واقعاً «از روی دیتابیس»)؛ خطای اینونتوری گزارش را نمی‌بندد (`inventory_error`)؛ stats جدید `inventory_devices`/`inventory_addresses`، ریست در start، فیلدهای پیشرفت `inventory_*` برای UI
- backend/route_pdf.py — برچسب‌های لینک نمودار مسیر خوانا شدند: helper جدید `_inrow_link_labels` — اینترفیسِ دستگاه چپ بالای خط اتصال و اینترفیسِ دستگاه راست زیر آن (هرکدام Helvetica-Bold 7.0 = `PATH_IF_SIZE`) و برچسب شاهد زیر آن (Helvetica-Oblique 6.0 = `PATH_TAG_SIZE`)؛ قبلاً هر دو در یک خط 5.8pt بودند که عرضشان (۵۳٫۲pt برای «ether10 <-> ether24») از گپ ۳۹٫۸pt بزرگ‌تر بود و همیشه با «...» بریده می‌شدند؛ `PATH_BOX_W` ۱۰۴→۹۴ تا گپ ~۵۳٫۱pt شود و طولانی‌ترین برچسب‌ها (`DEFAULT-ROUTE` در ۶٫۰ و `ether10-slave` در ۷٫۰ — تأییدشده با stringWidth) کامل جا شوند؛ فونت‌های اتصال شکست سطر (`_row_wrap_connector`) هم 5.8/5.2 → 7.2/6.4 (`PATH_WRAP_LBL_SIZE`/`PATH_WRAP_TAG_SIZE`)؛ هندسهٔ Task 24 (عرض سطر = کادر صفحه) دقیقاً حفظ شد؛ هر دو شاخهٔ reachable و upstream از helper خوانا استفاده می‌کنند
- frontend/src.jsx — برچسب فاز `inventory` در `phaseLabel` («ذخیرهٔ IP همهٔ اینترفیس‌ها + ای‌دی دستگاه‌ها در دیتابیس») + برچسب فاز graph به «پردازش لیست فیلترشده از دیتابیس و ساخت گراف مسیر» تغییر کرد + پیام پایان گزارش شمارش اینونتوری را نشان می‌دهد؛ frontend/dist بازسازی شد (index-BjxXujUb.js)
- tests/test_route_inventory.py (جدید، ۷ تست pytest): گردش replace/load و جایگزینی در سطح device_ip، نگاشت ردیف‌ها (device_id/identity/ip-بدون-ماسک + صرف‌نظر از خوانده‌نشده/بی‌آدرس)، مالکیت گیت‌وی دستگاه خوانده‌نشده از دیتابیس (یال به دستگاه واقعی، بدون شبح — و رفتار قبلی بدون اینونتوری)، نام‌گذاری شبح از identity دیتابیس (+ inventory_dev_id)، پاک‌سازی اینونتوری در delete_devices، سازگاری با inventory خالی
- tests/test_route_pdf_labels.py (جدید، ۷ تست pytest): هندسهٔ سطر هنوز دقیقاً داخل کادر، فونت‌های درشت‌تر از ناخوانای قبلی، جا شدن طولانی‌ترین برچسب‌ها در گپ (stringWidth واقعی reportlab)، رسم دورَقمی اینترفیس چپ/راست + شاهد با مختصات دقیق، حالت بدون شاهد، فونت‌های اتصال شکست سطر، استفادهٔ هر دو شاخه از helper
- scripts/test_route_inventory_e2e.py (جدید، ۳۰ بررسی): E2E کامل با ۴ دستگاه فیک (A سالم ۲ آدرس، B خطای timeout، D سالم، R1 خودِ روتر مرکزی) + پیش‌seed اینونتوری قبلی برای B (خوانده‌نشدنی) و دستگاه خارج از انتخاب (۹.۹.۹.۷۷ مالک گیت‌وی A با identity «Up-Core-MK»)؛ ثابت می‌شود: ذخیره فقط برای دستگاه‌های سالم (یک فراخوانی با db_path درست)، ردیف‌های B و ۹.۹.۹.۷۷ دست‌نخورده می‌مانند، پیشرفت/stats شمارش ۳ دستگاه و ۵ آدرس را دارند، `build_topology` اینونتوری خوانده‌شده از دیتابیس (۷ ردیف) را می‌گیرد، دلیل CSVِ D به دستگاه واقعی B با نام «B-MK» می‌رسد (مالکیت از دیتابیس — نه متن شبح) و PDF نام «Up-Core-MK» را برای hop بالادستِ A از دیتابیس نشان می‌دهد؛ اجرای دوم تک‌دستگاهه فقط دستگاه انتخابی را جایگزین می‌کند؛ پاک‌سازی تضمینی در هر مسیر خروج (کاتالوگ/دیتابیس تست/کانفیگ سیسکو/پچ‌ها)
- scripts/make_route_label_sample.py (جدید): نمونهٔ PDF با همان سناریوی تصویر کاربر (۹ آدرس 22Bahman-MK، KhezNabi-MK، هستهٔ SW-Wireless1) برای بازبینی بصری
- رگرسیون: pytest tests/ (۴۱) + unittest discover (۱۷) + test_route_unreachable_csv، test_route_topology_unit، test_route_topology_pdf، test_route_pdf_path_wrap، test_csv_filename_stamp، test_cisco_config، test_push_config_progress، test_push_verification، test_push_config_failed_csv، test_device_picker، test_export_mikrotik_csv، test_json_export_route_report، test_api_probe_progress، test_search_and_db — همه PASS
- بازبینی بصری: رندر صفحهٔ ۱ نمونه با pdftoppm و بررسی برش نمودار — برچسب‌های «ether10/ether10/MNDP» و «ether24/ether24/SUBNET» کامل و خوانا، روتر مرکزی داخل کادر
- مستندات: README.md (دو بولت جدید: اینونتوری دیتابیس Task 25 و برچسب خوانا) و AGENTS.md (بولت Task 25 + تیتر نقشه تا Task 25)

Stage Summary:
- گزارش مسیر حالا قبل از پردازش، IP همهٔ اینترفیس‌های هر دستگاه را با ای‌دی دستگاه (rowid) و identity آن در جدول device_interface_ips دیتابیس فعال ذخیره می‌کند و لیست فیلترشده را از روی همین دیتابیس پردازش می‌کند — گیت‌ویِ دستگاه‌هایی که این اجرا خوانده نشده‌اند از دیتابیس به دستگاه واقعی وصل می‌شود و hopهای ناشناخته با نام واقعی ثبت‌شده در دیتابیس نمایش داده می‌شوند؛ در نمودار PDF، اینترفیسِ دو سرِ هر لینک حالا دورَقمی و درشت (۷pt) و برچسب شاهد کامل (۶pt) رسم می‌شود و دیگر هیچ برچسبی بریده نمی‌شود

---

Task ID: 26
Agent: main (Z.ai)
Task: درشت و خوانا شدن نام دستگاه در گزارش مسیریابی (نوار بالای صفحه + جعبه‌های نمودار مسیر)

Work Log:
- کاربرد: درخواست کاربر — «فونت نام دستگاه در بالای گزارش مسیریابی را بزرگتر کن بهتر دیده شود»؛ پیش از این نام دستگاه در نوار بالای هر صفحه 7.5pt و در جعبه‌های نمودار مسیر 6.6pt بود که در چاپ/نمایش ناخوانا بود
- backend/route_pdf.py — نوار بالای صفحه (`_page_header`): خط «Target: name (ip)» که قبلاً کلش 7.5pt بود بازطراحی شد — برچسب «Target:» کوچک و روشن می‌ماند، خودِ نام دستگاه با **Helvetica-Bold 11** (`HEADER_NAME_SIZE`) و IP با 8pt در ادامه‌اش رسم می‌شود؛ عرض مجاز نام از روی عرض واقعی «Core Router: ...» سمت راست محاسبه می‌شود و نام خیلی بلند با «...» کوتاه می‌شود ولی هرگز از کادر صفحه بیرون نمی‌زند
- backend/route_pdf.py — جعبه‌های نمودار مسیر (`_path_diagram`): نام دستگاه در زنجیرهٔ اصلی 6.6→**8.5** (`PATH_NAME_SIZE`) و در زنجیرهٔ upstream 6.6→**8.0** (`PATH_UP_NAME_SIZE`)؛ IP زیر نام هم 6→6.3 و 5.8→6.0 (`PATH_IP_SIZE`/`PATH_UP_IP_SIZE`)
- backend/route_pdf.py — helper جدید `_fit_lines`: نام‌های بلند به‌جای بریدن با «...» تا **دو سطر** داخل جعبه شکسته می‌شوند؛ چون نام‌های میکروتیک معمولاً «بدون فاصله» و با خط تیره/نقطه‌اند (مثل RB-Anbar-daruel-HapLite که در رندر اول فقط با «...» بریده می‌شد)، شکستن در مرز فاصله/خط تیره/نقطه/زیرخط/دو نقطه/اسلش هم انجام می‌شود و نام کامل در دو سطر حفظ می‌شود؛ فقط اگر باز جا نشود سطر آخر با «...» کوتاه می‌شود؛ هر سطر خروجی تضمیناً عرضش ≤ عرض جعبه است
- backend/route_pdf.py — هندسه: ارتفاع جعبهٔ اصلی 30→36 (`PATH_BOX_H`) و upstream 26→32 (`PATH_UP_BOX_H`) برای جای نام دورَقمی؛ فاصلهٔ عمودی سطرهای نمودار 34→30 (`PATH_ROW_STRIDE`)؛ برای جبران ارتفاع اضافه، فاصلهٔ سطر جدول‌ها کمی جمع شد (kv 13→12.5، آدرس 11.5→11، اینترفیس 11→10.6، جدول hop 12→11.2، شواهد 11→10) تا «یک صفحه به ازای هر دستگاه» برقرار بماند و در بدترین حالت (۸ hop + ۱۲ آدرس + ۲۴ اینترفیس + ۶ شاهد) هیچ متنی روی فوتر نیفتد — هندسهٔ Task 24 (عرض سطر = کادر صفحه) و برچسب‌های خوانای Task 25 دست‌نخورده ماندند
- scripts/test_route_pdf_path_wrap.py — فیلترهای ارتفاع جعبه از مقدار ثابت (30/26) به ثابت‌های جدید (`PATH_BOX_H`/`PATH_UP_BOX_H`) و گودال اتصال شکست سطر به `PATH_BOX_H` وابسته شد
- tests/test_route_name_font.py (جدید، ۱۰ تست pytest): ثابت‌های بزرگ‌تر از مقادیر قبلی، تک‌سطری بودن نام کوتاه، دورَقمی شدن نام بلند با فاصله داخل عرض مجاز، «...» برای تک‌توکن خیلی بلند، **حفظ کامل نام‌های خط‌تیره‌دار (RB-Anbar-daruel-HapLite / RB-UMS-SHDGN-CoreRouter / VL-Shadegan-Shabankareh) در دو سطر بدون «...»**، رسم نام در هدر با Bold 11 و IP در ادامه‌اش، کوتاه‌شدن نام خیلی بلند هدر با «...» داخل کادر، استفادهٔ `_path_diagram` از ثابت‌های جدید و حذف فونت قدیمی 6.6، و جبران‌بودن ریاضی کاهش فاصلهٔ سطرها نسبت به رشد جعبه‌ها
- scripts/test_route_name_font_e2e.py (جدید، ۱۶ بررسی): PDF با بوم ضبط‌کننده روی توپولوژی شبیه شبکهٔ واقعی کاربر (زنجیرهٔ **۸ hop** + ۱۲ آدرس + ۲۴ اینترفیس + نام خیلی بلند + دستگاه نارس با upstream ۵ hop)؛ ثابت می‌شود: نام هدر با Bold 11 و بدون بریدگی رسم شده، نام جعبه‌ها با 8.5/8.0، هیچ متنِ داخل جعبه از عرض جعبه بیرون نمی‌زند، همهٔ جعبه‌ها داخل کادر صفحه‌اند، نام بلند دورَقمی شده، و در هر دو صفحهٔ بدترین حالت، پایین‌ترین متن بدنه با فاصلهٔ تمیز بالای خط فوتر است (min y=81.0 و 370.4 در برابر خط فوتر y=32)؛ نمونهٔ PDF در /tmp/render/route_name_sample.pdf برای بازبینی بصری
- رگرسیون: pytest tests/ (۵۱) + unittest discover + تمام اسکریپت‌های E2E (test_route_topology_pdf، test_route_topology_unit، test_route_unreachable_csv، test_cisco_config، test_csv_filename_stamp، test_route_inventory_e2e، test_route_pdf_path_wrap، test_route_name_font_e2e و بقیه) — همه PASS
- بازبینی بصری: رندر هر ۳ صفحهٔ نمونه با pdftoppm — نام «RB-Anbar-daruel-HapLite» در نوار بالا درشت و کامل، نام‌های جعبه‌ها (RB-Anbar-daruel-HapLite، RB-UMS-SHDGN-CoreRouter، VL-Shadegan-Shabankareh) کامل و دورَقمی، زنجیرهٔ upstream و اتصال Z شکل سالم، هیچ متنی روی فوتر نیست
- مستندات: README.md (بولت «نام دستگاه درشت و خوانا است») و AGENTS.md (بولت Task 26 + تیتر نقشه تا Task 26)

Stage Summary:
- نام دستگاه در گزارش مسیر حالا در دو نقطهٔ کلیدی درشت و خواناست: نوار بالای هر صفحه (Bold 11 با IP در ادامه) و جعبه‌های نمودار «Shortest Path» (8.5 در مسیر کامل و 8.0 در زنجیرهٔ upstream)؛ نام‌های بلند به‌جای بریدن در دو سطر داخل جعبه جا می‌شوند و چیدمان صفحه (یک صفحه به ازای هر دستگاه، نمودار داخل کادر، برچسب‌های خوانای لینک) بدون رگرسیون حفظ شده است

---

Task ID: 27
Agent: main (Z.ai)
Task: افزودن دستگاه همسایهٔ متصل به اینترفیس flapشده (شامل IP و نام همسایه) به گزارش هوشمند + ارسال تغییرات به گیت‌هاب

Work Log:
- کاربرد: درخواست کاربر — «در گزارش هوشمند، flap دستگاه همسایهٔ متصل به اینترفیس گزارش‌شده شامل IP و نام دستگاه همسایه به گزارش اضافه شود»
- backend/smart_reports.py — موتور تشخیص همسایه: `_ip4` (پاک‌سازی IPv4 و حذف ماسک)، `_KV_RE` عمومی برای توکن‌های `کلید=value` هر دو شکل ذخیره‌شدهٔ متن RouterOS (خطوط جمع‌شدهٔ `collect_device_info` مثل «1 identity=Core-SW address=.. interface=ether2» و dump جمله‌ای `collect_ip_info` مثل «interface=ether2 mac-address=.. address=.. identity=..») — مقدار هر کلید در توکن `کلید=` بعدی تمام می‌شود تا کلیدهای ناشناخته (board-name/uptime/…) مقدار قبلی را نبلعند (باگ رگرسیون تست خودش کشف و ثابت شد)
- backend/smart_reports.py — `parse_neighbor_entries` (ردیف‌های /ip neighbor بدون اینترفیس محلی حذف می‌شوند)، `parse_self_addresses` (IP/ماسک هر اینترفیس از متن /ip address ذخیره‌شده)، `build_neighbor_context(devices, inventory_rows)` — ایندکس IP→دستگاه و identity→دستگاه از لیست دستگاه‌ها + اینونتوری دیتابیس `device_interface_ips` (Task 25) + متن ip_addresses هر دستگاه؛ ایندکس LLDP به تفکیک device_ip/اینترفیس
- backend/smart_reports.py — `_resolve_neighbor`: اولویت (۱) ردیف‌های LLDP/MNDP خودِ دستگاه برای همان اینترفیس — تطبیق آدرس و بعد identity با دستگاه‌های شناخته‌شده؛ دستگاه شناخته‌شده → نام/IP واقعی، ناشناخته → مقادیر خام LLDP؛ ردیف خودبینی (آدرسِ خودِ دستگاه) حذف؛ چند همسایه متمایز با «،»؛ (۲) fallback ساب‌نت — دستگاه دیگری که IPاش در ساب‌نتِ IP همان اینترفیس است (اینونتوری یا متن ip_addresses، با `ipaddress.ip_network(strict=False)`)؛ خروجی: `neighbor_name`/`neighbor_ip`/`neighbor_via` (lldp/subnet/خالی)
- backend/smart_reports.py — `interface_flap_report(..., inventory_rows=None)` بعد از ردیف‌بندی هر رویداد را enrich می‌کند؛ `interface_flaps_csv` و `interface_flaps_xlsx` دو ستون «نام دستگاه همسایه» و «IP دستگاه همسایه» بعد از «اینترفیس» گرفتند (۱۱ ستون)
- backend/main.py — هر سه اندپوینت flap (`/reports/interface-flaps` و export.csv و export.xlsx) اینونتوری دیتابیس همان گزارش را با `db.load_interface_inventory(db_path=...)` می‌خوانند (خطا → لیست خالی، گزارش نمی‌بندد) و به گزارش پاس می‌دهند؛ باگ پیش‌مخفی واقعی `export.xlsx` رفع شد — `BytesIO` خام به `Response` پاس داده می‌شد و `.encode` آن همیشه ۵۰۰ می‌داد (این اندپوینت تا دیروز بدون E2E بود) — حالا `data.getvalue()`
- frontend/src.jsx — دو ستون همسایه در جدول UI گزارش هوشمند بعد از «اینترفیس» (min-width جدول 800→980)؛ `frontend/dist` بازسازی شد (index-Daf-tAjM.js)
- tests/test_flap_neighbor.py (جدید، ۱۲ تست pytest): پارس هر دو فرمت /ip neighbor + حذف خطوط بی‌اینترفیس، همسایهٔ شناخته‌شدهٔ LLDP، همسایهٔ ناشناخته با مقادیر خام، تطبیق identity بدون آدرس، حذف خودبینی (و رسیدن به همسایهٔ واقعی از fallback ساب‌نت)، fallback ساب‌نت از اینونتوری و از متن ip_addresses، حالت بدون هیچ همسایه، ستون‌های جدید در CSV (جای دقیق ۵/۶، ۱۱ ستون، تراز عرض ردیف) و xlsx
- scripts/test_flap_neighbor_e2e.py (جدید، ۲۸ بررسی): E2E با TestClient روی اپ واقعی + دیتابیس موقت کاتالوگ‌دار با ۴ دستگاه (A با flap روی ether2/ether3/ether4، B همسایهٔ شناخته‌شدهٔ LLDP، C همسایهٔ هم‌سابنت بدون LLDP، D بی‌ربط) + اینونتوری واقعی با `replace_interface_inventory`؛ ثابت می‌شود JSON سه رویداد با neighbor درست (lldp/subnet)، CSV سرستون‌ها در جای درست + مقادیر درست + BOM، و xlsx همان ستون‌ها را دارد؛ لاگ‌های flap نسبت به زمان جاری ساخته می‌شوند تا تست کهنه نشود؛ پاک‌سازی تضمینی دیتابیس در finally
- scripts/test_ip_info_path_fix.py — دو بررسیِ کهنه‌شونده اصلاح شد (بدون تغییر نیت تست): مهر لاگ ip_info به‌جای تاریخ ثابت 2026/10/23 حالا نسبت به زمان جاری ساخته می‌شود (تاریخ ثابت بعد از چند روز از پنجرهٔ days_back خارج و تست می‌بُرَخت) و بررسی «real default.db still has events» که به تازگی لاگ‌های همان محیط وابسته است به «گزارش بدون خطا ساخته می‌شود» گیت شد (با NOTE وقتی رویداد تازه‌ای نیست) — هر دو خطا قبل از این تسک هم بدون تغییر کد گزارش، به‌دلیل تاریخ/محیط رخ می‌داد (با git stash اثبات شد)
- رگرسیون: pytest tests/ (۶۳) + unittest discover (۲۹) + هر ۲۱ اسکریپت E2E در scripts/ (test_route_topology_pdf، test_route_topology_unit، test_route_unreachable_csv، test_cisco_config، test_csv_filename_stamp، test_route_inventory_e2e، test_route_pdf_path_wrap، test_route_name_font_e2e، test_push_config_progress، test_push_verification، test_push_config_failed_csv، test_device_picker، test_export_mikrotik_csv، test_json_export_route_report، test_api_probe_progress، test_search_and_db، test_auth، test_report_fix، test_flap_csv، test_flap_neighbor_e2e، test_ip_info_path_fix) — همه PASS
- مستندات: README.md (بخش جدید «گزارش هوشمند: نوسان (flap) اینترفیس‌ها» با توضیح ستون‌های همسایه و منابع lldp/subnet) و AGENTS.md (بولت Task 27 + تیتر نقشه تا Task 27)

Stage Summary:
- در گزارش هوشمند، هر رویداد flap اینترفیس حالا دستگاه همسایهٔ متصل به همان اینترفیس را هم نشان می‌دهد — دو ستون «نام دستگاه همسایه» و «IP دستگاه همسایه» در جدول UI، CSV و xlsx: همسایه از ردیف‌های LLDP/MNDP خود دستگاه با تطبیق IP/identity روی دستگاه‌های شناخته‌شدهٔ دیتابیس (و در نبود آن، fallback ساب‌نت از اینونتوری IP اینترفیس‌های Task 25) شناسایی می‌شود و دستگاه‌های ناشناخته با مقادیر خام LLDP گزارش می‌شوند؛ ضمناً اندپوینت دانلود xlsx گزارش flap که به‌دلیل پاس‌دادن BytesIO خام همیشه خطای ۵۰۰ می‌داد تعمیر شد

---

Task ID: 28
Agent: main (Z.ai)
Task: انتقال ستون‌های «نام دستگاه» و «آی‌پی دستگاه» به ستون سمت چپ گزارش هوشمند + اصلاح پهنای فیلدها

Work Log:
- کاربرد: درخواست کاربر — «ستون‌های نام دستگاه و ای پی دستگاه به ستون سمت چپ گزارش منتقل شود؛ پهنای فیلدها اصلاح/adjust شود»
- نکتهٔ چیدمان: جدول گزارش RTL است (و شیت اکسل rightToLeft) — پس انتهای آرایهٔ ستون‌ها لبهٔ چپ گزارش است؛ برای رفتن نام/IP دستگاه به «ستون سمت چپ» این دو ستون به انتهای ترتیب منتقل شدند و «نام دستگاه» چپ‌ترین ستون شد
- backend/smart_reports.py — ترتیب ستون‌ها در `interface_flaps_csv` و `interface_flaps_xlsx` جدید و یکسان شد: ردیف، تگ دستگاه، اینترفیس، نام دستگاه همسایه، IP دستگاه همسایه، تعداد تکرار لاگ، تاریخ و زمان (میلادی)، تاریخ و زمان (شمسی)، نوع رویداد، آی‌پی دستگاه، نام دستگاه (۱۱ ستون؛ محتوای داده بدون تغییر، فقط جای ستون‌ها) — تا UI/CSV/xlsx یک‌شکل باشند
- frontend/src.jsx — جدول گزارش flap از ردیف‌نویسی دستی td به پیکربندی ستون‌محور `FLAP_COLS` (۱۱ ستون با label/key/w/wrap/center/get) تبدیل شد؛ جدول با `table-layout:fixed` و `min-width:1400` رندر می‌شود تا پهنای هر فیلد دقیقاً رعایت شود؛ سرستون‌ها وسط‌چین و قابل شکستن دوخطی؛ ستون‌های متنی (نام/تگ/اینترفیس/نام همسایه/نوع رویداد) با `overflow-wrap:break-word` داخل سلول می‌شکنند و ستون‌های عددی/IP/تاریخ nowrap یک‌خطی می‌مانند
- پهنای ستون‌ها (px، با `box-sizing:border-box`): ردیف 56، تگ 100، اینترفیس 120، نام دستگاه همسایه 150، IP دستگاه همسایه 130، تعداد تکرار لاگ 80، تاریخ میلادی 170، تاریخ شمسی 175، نوع رویداد 110، آی‌پی دستگاه 130، نام دستگاه 175 (مجموع 1396) — نکتهٔ دام‌دار کشف‌شده در بازبینی بصری: بدون border-box، پدینگ 24px هر سلول به عرض ستون اضافه می‌شد، جمع ستون‌ها ~1607px از کادر بیرون می‌زد و دو ستون راست (تگ/ردیف) در اسکرول گم می‌شدند
- frontend/dist بازسازی شد (index-By1d3JMJ.js)
- tests/test_flap_neighbor.py — اندیس‌های ستون همسایه در CSV/xlsx از 5/6 به 3/4 و بررسی جدید جای نام/IP دستگاه در اندیس‌های 9/10 + مقادیر تگ/اینترفیس در 1/2
- scripts/test_flap_neighbor_e2e.py — همان تغییر اندیس‌ها + ۴ بررسی جدید: «آخرین ستون CSV = نام دستگاه (لبهٔ چپ)»، «اندیس 9 = آی‌پی دستگاه» و مقادیر IP/نام دستگاه A در لبهٔ چپ CSV و xlsx (اندیس اینترفیس برای گروه‌بندی ردیف‌ها هم 4→2 شد)
- بازبینی بصری: بازتولید DOM جدول با همان استایل‌های inline رندر React (فونت 13px اپ) و اسکرین‌شات Playwright در دو عرض 1440 و 900 — در 1440 هر ۱۱ ستون داخل کادر است، نام دستگاه چپ‌ترین ستون و آی‌پی کنارش، تاریخ‌ها/IPها یک‌خطی و نام بلند (RB-Anbar-daruel-HapLite) کامل جا می‌شود؛ در 900 اسکرول افقی با چیدمان سالم
- رگرسیون: pytest tests/ (۶۳) + unittest discover (۲۹) + هر ۲۱ اسکریپت E2E در scripts/ (test_route_topology_pdf، test_route_topology_unit، test_route_unreachable_csv، test_cisco_config، test_csv_filename_stamp، test_route_inventory_e2e، test_route_pdf_path_wrap، test_route_name_font_e2e، test_push_config_progress، test_push_verification، test_push_config_failed_csv، test_device_picker، test_export_mikrotik_csv، test_json_export_route_report، test_api_probe_progress، test_search_and_db، test_auth، test_report_fix، test_flap_csv، test_flap_neighbor_e2e، test_ip_info_path_fix) — همه PASS
- مستندات: README.md (به‌روزرسانی ترتیب ستون‌های گزارش هوشمند) و AGENTS.md (بولت Task 28 + تیتر نقشه تا Task 28)

Stage Summary:
- در گزارش هوشمند flap ستون‌های «نام دستگاه» و «آی‌پی دستگاه» به لبهٔ چپ جدول منتقل شدند و برای نخستین‌بار پهنای تک‌تک فیلدها مشخص و ثابت شد (table-layout:fixed + box-sizing:border-box + عرض اختصاصی هر ستون)؛ همان ترتیب در CSV و xlsx هم اعمال شد تا جدول UI، فایل CSV و اکسل هر سه یک‌شکل باشند — «نام دستگاه» چپ‌ترین و «آی‌پی دستگاه» ستون کنار آن است

---

Task ID: 29
Agent: main (Z.ai)
Task: ترکیب دقیق ۸ ستونی گزارش CSV فلاپ — نام دستگاه، ای پی دستگاه، اینترفیس، تعداد تکرار لاگ، نوع رویداد، تاریخ و زمان شمسی، نام دستگاه همسایه و ای پی دستگاه همسایه

Work Log:
- کاربرد: درخواست کاربر — «ترکیب ستون‌ها نام دستگاه، ای پی دستگاه، اینترفیس، تعداد تکرار لاگ، نوع رویداد، تاریخ و زمان شمسی، نام دستگاه همسایه و ای پی دستگاه همسایه — این فیلدها در گزارش csv flap بیایند با همین ترکیب»
- ترکیب جدید فقط ۸ فیلد است: ستون‌های «ردیف»، «تگ دستگاه» و «تاریخ و زمان (میلادی)» از گزارش حذف شدند و «تاریخ و زمان (شمسی)» بعد از «نوع رویداد» نشست؛ همسایه‌ها (نام و IP) به انتهای ترتیب بصری (سمت راستِ گزارش RTL) رفتند
- نکتهٔ چیدمان (ادامهٔ قرارداد Task 28): جدول UI و شیت اکسل راست‌به‌چپ‌اند و انتهای آرایهٔ ستون‌ها چپ‌ترین ستون است — پس آرایهٔ ستون‌ها در CSV/xlsx/UI معکوسِ ترتیب بصری خواسته‌شده نوشته شد: IP دستگاه همسایه، نام دستگاه همسایه، تاریخ و زمان (شمسی)، نوع رویداد، تعداد تکرار لاگ، اینترفیس، آی‌پی دستگاه، نام دستگاه؛ یعنی بصری از چپ دقیقاً همان ترکیب کاربر: نام دستگاه، ای پی دستگاه، اینترفیس، تعداد تکرار لاگ، نوع رویداد، تاریخ و زمان شمسی، نام دستگاه همسایه، IP دستگاه همسایه
- backend/smart_reports.py — `interface_flaps_csv` و `interface_flaps_xlsx` با سرستون و ترتیب مقدار ۸ ستونی جدید بازنویسی شدند (فیلدهای دادهٔ رویداد بدون تغییر؛ data مهر فایل از Task 22 سر جایش است)؛ شیت اکسل همچنان rightToLeft با استایل سرستون/عرض خودکار ستون‌ها
- frontend/src.jsx — `FLAP_COLS` به ۸ ستون جدید به‌روز شد؛ عرض ستون‌ها (px): IP همسایه 130، نام همسایه 150، شمسی 175، نوع رویداد 110، تعداد 80، اینترفیس 120، آی‌پی دستگاه 130، نام دستگاه 175 (مجموع 1070) و `min-width` جدول 1400→1080؛ همان قرارداد table-layout:fixed + box-sizing:border-box + break-word ستون‌های متنی حفظ شد؛ کلید React ردیف‌ها همچنان از فیلد `row` سرور (که در JSON می‌ماند) استفاده می‌کند
- frontend/dist بازسازی شد (index-DH3p4FxF.js)
- tests/test_flap_neighbor.py — `ExportColumnsTests` با ترکیب جدید: ۸ سرستون در اندیس‌های 0..7 + مقادیر (IP همسایه 10.10.10.2 در 0، نام همسایه SW-Core-MK در 1، نوع رویداد Up در 3، تعداد 4 در 4، اینترفیس ether2 در 5، IP/نام دستگاه در 6/7) + گیت نبودن «ردیف»/«تگ دستگاه»/«میلادی» + همان بررسی‌ها برای xlsx
- scripts/test_flap_neighbor_e2e.py — بخش CSV/XLSX با اندیس‌های جدید (گروه‌بندی ردیف‌ها بر اساس اینترفیس در اندیس 5) + بررسی جدید الگوی تاریخ شمسی `^\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}$` روی ستون شمسی + بررسی برابری کامل سرستون xlsx با CSV؛ `import re` اضافه شد
- scripts/test_report_fix.py — بررسی CSV که به «ردیف» وابسته بود به بررسی شروع سرستون با «IP دستگاه همسایه» تغییر کرد؛ scripts/test_search_and_db.py و scripts/diag_http.py هم همین‌طور به‌روز شدند
- رگرسیون: pytest tests/ (۶۳ PASS) + اسکریپت‌های E2E مرتبط — test_flap_neighbor_e2e (همه PASS)، test_report_fix (18/0)، test_search_and_db، test_flap_csv (خروجی ۸ ستونه + BOM + تاریخ شمسی 1405/07/29)، test_csv_filename_stamp، test_auth، test_route_unreachable_csv، test_push_config_failed_csv، test_ip_info_path_fix (12/0) — همه PASS
- مستندات: README.md (ترکیب ستون‌های گزارش هوشمند تا Task 29) و AGENTS.md (بولت Task 29 + تیتر نقشه تا Task 29)

Stage Summary:
- گزارش CSV فلاپ (و xlsx و جدول UI) حالا دقیقاً همان ۸ فیلد با همان ترکیب خواسته‌شدهٔ کاربر را دارد: نام دستگاه، ای پی دستگاه، اینترفیس، تعداد تکرار لاگ، نوع رویداد، تاریخ و زمان شمسی، نام دستگاه همسایه و ای پی دستگاه همسایه — ستون‌های اضافی (ردیف، تگ، تاریخ میلادی) حذف شدند و هر سه خروجی یک‌شکل‌اند

---

Task ID: 30
Agent: main (Z.ai)
Task: همسایهٔ گزارش‌شده فقط مختص اینترفیس flapدار + چیدمان قرینهٔ ستون‌ها از راست به چپ

Work Log:
- کاربرد: دو درخواست کاربر — «نام و ای پی دستگاه همسایه فقط مربوط به اینترفیسی باشد که flap دارد» و «کل ستون‌ها قرینه چیده شوند یعنی از راست به چپ»
- بخش ۱ (همسایهٔ مختص اینترفیس): در `build_neighbor_context` نقشهٔ «قفل‌شدگی» (`pinned`) اضافه شد — هر ردیف LLDP/MNDP خودِ هر دستگاه، همسایه را با آدرس و identity به اینترفیس(های) دیدارشده قفل می‌کند؛ کشف از دادهٔ واقعی دیتابیس (349 دستگاه دارای ip_neighbors): مقدار interface در `/ip neighbor` می‌تواند فهرست جدا-با-کاما باشد (نمونهٔ واقعی `wlan1,bridge1` در 172.18.1.243) — ردیف به تک‌تک اجزا تقسیم و هر جز جداگانه ایندکس/قفل شد (قبلاً flap روی wlan1 چنین همسایه‌ای را از مسیر LLDP نمی‌دید)
- بخش ۱ (ادامه): در fallback ساب‌نتِ `_resolve_neighbor` هر کاندیدی که LLDP همان دستگاه آن را روی اینترفیس دیگری (غیر از اینترفیس flapدار) دیده باشد حذف می‌شود — یعنی همسایهٔ ether2 (مثلاً SW-Core-MK) دیگر به‌خاطر هم‌سابنتی به ردیف flap اینترفیس دیگری سرریز نمی‌شود؛ ستون‌های همسایه در آن ردیف خالی می‌مانند. مسیر اصلی LLDP هم از قبل/حالا فقط ردیف‌های همان اینترفیس را می‌بیند
- بخش ۲ (چیدمان قرینه): ترتیب آرایهٔ ستون‌ها در هر سه خروجی (جدول UI، CSV و xlsx) با ترتیب راست‌به‌چپ کاربر یکی شد — نام دستگاه، آی‌پی دستگاه، اینترفیس، تعداد تکرار لاگ، نوع رویداد، تاریخ و زمان (شمسی)، نام دستگاه همسایه، IP دستگاه همسایه؛ در جدول RTL و شیت rightToLeft اکسل، ستون اول آرایه راست‌ترین ستون است پس «نام دستگاه» راست‌ترین و «IP دستگاه همسایه» چپ‌ترین ستون گزارش است (قرینهٔ کامل چیدمان قبلی)
- backend/smart_reports.py — `build_neighbor_context` (pinned + split کاما)، `_resolve_neighbor` (استثنای کاندیدای قفل‌شده به اینترفیس دیگر)، `interface_flaps_csv` و `interface_flaps_xlsx` (ترتیب جدید)
- frontend/src.jsx — `FLAP_COLS` با ترتیب راست‌به‌چپ جدید؛ frontend/dist بازسازی شد (index-BbW4ZoQs.js)
- tests/test_flap_neighbor.py — اندیس‌های ExportColumnsTests با ترتیب جدید + کلاس جدید `InterfaceSpecificNeighborTests` (۳ تست: نشت‌نکردن همسایهٔ قفل‌شده به اینترفیس دیگر — ether5 هم‌سابنت ether2؛ کنترل LLDP همان اینترفیس همچنان حل می‌شود؛ مقدار interface کامادار `wlan1,bridge1` به هر دو جزء پین می‌شود و flap روی wlan1 همسایه را از مسیر lldp می‌بیند)
- scripts/test_flap_neighbor_e2e.py — سناریوی ether5 (آدرس 10.40.10.77/24 در متن ip_addresses + اینونتوری → اینونتوری ۴→۵ ردیف، رویدادها ۳→۴) + بررسی خالی‌بودن همسایهٔ ether5 در JSON/CSV/XLSX + اندیس‌های جدید (نام/IP دستگاه 0/1، اینترفیس 2، تعداد 3، رویداد 4، شمسی 5، همسایه 6/7)؛ نکته: openpyxl رشتهٔ خالی را None برمی‌گرداند — بررسی خالی با truthy
- scripts/test_report_fix.py، scripts/test_search_and_db.py، scripts/diag_http.py — بررسی سرستون با «نام دستگاه» (ستون اول جدید)
- رگرسیون: pytest tests/ (۶۶ PASS) + unittest discover (OK) + اسکریپت‌های E2E — test_flap_neighbor_e2e (همه PASS)، test_report_fix (18/0)، test_search_and_db، test_flap_csv (خروجی ۸ ستونه با ترتیب راست‌به‌چپ)، test_csv_filename_stamp، test_auth — همه PASS
- مستندات: README.md (چیدمان راست‌به‌چپ + همسایهٔ مختص اینترفیس) و AGENTS.md (بولت Task 30 + تیتر نقشه تا Task 30)

Stage Summary:
- در گزارش هوشمند flap، نام و IP دستگاه همسایه حالا فقط از داده‌های همان اینترفیس flapدار می‌آید: اول LLDP/MNDP خود دستگاه برای همان اینترفیس (با پشتیبانی از مقادیر کامادار مثل wlan1,bridge1) و در fallback ساب‌نت هم کاندیدایی که LLDP آن را روی اینترفیس دیگری از همان دستگاه قفل کرده حذف می‌شود؛ ضمناً چیدمان هر سه خروجی (UI/CSV/xlsx) قرینه شد و ستون‌ها از راست به چپ به ترتیب نام دستگاه، ای پی دستگاه، اینترفیس، تعداد تکرار لاگ، نوع رویداد، تاریخ و زمان شمسی، نام دستگاه همسایه، IP دستگاه همسایه چیده می‌شوند

---
Task ID: 31
Agent: main (Z.ai)
Task: دکمهٔ Winbox کنار نام دستگاه در جدول گزارش flap

Work Log:
- کاربرد: درخواست کاربر — «در گزارش flap در جلوی نام دستگاه دکمهٔ winbox را بزار که دستگاه را با این پی بازکنم»
- وضعیت پایه: Task 30 (همسایهٔ مختص اینترفیس + چیدمان راست‌به‌چپ) با کامیت bdd2bbc کامیت و push شده بود؛ این نوبت فقط دکمهٔ Winbox
- frontend/src.jsx (SmartReports): تابع `openWinbox(ip)` اضافه شد — `POST /devices/{ip}/winbox` (همان مسیر جدول دستگاه‌ها) با پیام موفقیت «Winbox اجرا شد: IP» و در خطا نمایش detail فارسی بک‌اند (مثلاً تنظیم‌نبودن مسیر exe) + راهنمای «مسیر Winbox»/tools/winbox در همان پنل گزارش (msg/err محلی SmartReports، بدون وابستگی به App)
- frontend/src.jsx (FLAP_COLS): سلول «نام دستگاه» حالا `div.name-cell` است — نام + دکمهٔ `▣ Winbox` با کلاس‌های موجود `btn-winbox btn-winbox-inline` (title: «باز کردن Winbox — IP»، stopPropagation)؛ دکمه فقط وقتی ردیف IP دارد رندر می‌شود؛ چون در جدول RTL اولین فرزند راست‌ترین است، نام سمت راست و دکمه بلافاصله جلوی آن قرار می‌گیرد
- پهناها: ستون نام 175→215 و min-width جدول 1080→1120 تا نام + دکمه راحت جا شوند؛ CSS جدید لازم نشد (name-cell/name-actions/btn-winbox-inline از قبل موجود بودند) — frontend/dist بازسازی شد (index-D1H5_fNp.js؛ css بدون تغییر)
- تست: scripts/test_flap_winbox_button.py — ۱۱ بررسی (باندل dist شامل کلاس دکمه/فراخوانی POST winbox/پیام‌های پنل flap + endpoint با TestClient: IP نامعتبر 400، بدون exe 404 با detail فارسی، exe ساختگی → Popen([exe, ip]) و 200 ok=true) — 11/0 PASS
- رگرسیون: pytest tests/ (۶۶ PASS) + scripts/test_flap_neighbor_e2e.py (ALL PASS) + scripts/test_report_fix.py (18/0)
- مستندات: README.md (بولت Task 31 در بخش گزارش flap) و AGENTS.md (بولت Task 31 + تیتر نقشه تا Task 31)

Stage Summary:
- جدول گزارش flap حالا کنار «نام دستگاه» دکمهٔ ▣ Winbox دارد که همان دستگاه را با IP همان ردیف باز می‌کند (همان زیرساخت Winbox چندمسیری برنامه؛ حل exe از مسیر پیش‌فرض/تنها مسیر تنظیم‌شده یا کشف خودکار)؛ نتیجه و خطا در خود پنل گزارش دیده می‌شود و ستون نام برای جا‌دادن دکمه پهن‌تر شد

---
Task ID: 32
Agent: main (Z.ai)
Task: انتقال برگهٔ کارتابل پروژه دژبان (frontend12.zip) به شبکه‌بان + بک‌اند کارتابل + رکورد نمونه هر بخش

Work Log:
- کاربرد: «برگهٔ کارتابل این فایل زیپ را در پوشه frontend به پروژه منتقل کن؛ برگهٔ کارتابل پروژه دقیقاً برگهٔ کارتابل فایل زیپ شود با رعایت تم گرافیکی پروژه؛ قسمت بک‌اند را برای برگه کارتابل ایجاد کن؛ برای تست هر قسمت و تست ذخیره‌سازی آیتم‌ها یک رکورد نمونه برای هر بخش ایجاد کن» (پیوست: frontend12.zip پروژهٔ dejban + اسکرین‌شات صفحه)
- تحلیل زیپ: کارتابل دژبان در src/App.jsx (خطوط 346-1450 + مدال قالب‌ها 2216+) با منوی ۷ پوشه‌ای، کارت بنفش آمار، اطلاعیه، تقویم کاری، مدال ۴ قالب Word و صفحهٔ ویرایش نامه؛ CSS مدال در index.css (خطوط 535-764)
- بک‌اند جدید backend/kartable.py: دیتابیس مستقل databases/kartable.db (مستقل از دیتابیس‌های دستگاه‌ها تا با تغییر DB فعال از بین نرود) — جدول‌های kartable_items/kartable_announcements/kartable_events؛ همان الگوریتم شمسی smart_reports (کپی gregorian_to_jalali)؛ توابع list/create/update/delete/summary برای آیتم‌ها + announcements/events؛ بذر خودکار در اولین استفاده: یک رکورد برای هر یک از ۷ پوشه (صندوق ورودی/جهت اقدام خوانده‌نشده، نامه‌های اقدامی/جهت امضا، رونوشت‌ها/جهت اطلاع، پیش‌نویس‌ها/پیش‌نویس‌های من، ارسال شده ها/جهت اطلاع، پیگیری و ارجاعات/فعال، بایگانی شخصی/پوشه عمومی) + نمونهٔ محرمانه در پوشه محرمانه (برای شمارندهٔ «محرمانه») + اطلاعیهٔ help.pdf + رویداد «جلسه اداری» به تاریخ امروز شمسی
- backend/main.py: ایمپورت دوگانهٔ kartable (الگوی موجود) + مدل‌های Pydantic و ۸ endpoint: GET /api/kartable/summary، GET/POST /api/kartable/items، PUT/DELETE /api/kartable/items/{id}، GET/POST /api/kartable/announcements، GET/POST /api/kartable/events (ایجاد/انتقال با اعتبارسنجی پوشه/زیرپوشه در برابر منوی دژبان → 422) + مسیر /template.docx در بلوک سرو UI (FileResponse با MIME صحیح docx)
- frontend/src.jsx: کامپوننت Kartable (پورت کامل دژبان با تم شبکه‌بان): سایدبار آکاردئونی «منوی کارتابل» با بج زنده، هدر «میز کار اداری و مکاتبات» + دکمهٔ سبز «New (جدید)» با دراپ‌داون، کارت بنفش «گزارش مکاتبات اداری» (۴ شمارندهٔ زنده)، کارت «اطلاعیه مهم اداری»، «رویدادها و تقویم کاری» هفتهٔ جاری شنبه-جمعه با تبدیل شمسی سمت کلاینت (kbG2J) و هایلایت رویداددار، جدول «آیتم‌های بخش انتخابی» با «خوانده شد» (PUT) و «حذف» (DELETE)؛ جریان ایجاد نامه: مدال قالب‌ها (کلاس‌های tpl-* عیناً از دژبان با جستجو) → صفحهٔ A4 نامه (بسمه تعالی، مثلث بنفش، تاریخ شمسی روز، «ویرایش نامه (Word)» با ms-word:ofe|u|) + دکمهٔ «ثبت در پیش‌نویس‌ها»؛ «ایجاد یادداشت» → POST پیش‌نویس؛ تب «🗂️ کارتابل» به نوار ribbon و بلوک رندر mainTab اضافه شد
- frontend/style.css: بخش «کارتابل اداری» با کلاس‌های kb-* (چیدمان RTL، رنگ‌های عیناً دژبان: بنفش 6366f1→4f46e5، سبز 10b981→059669، آبی تقویم eff6ff/93c5fd) + کلاس‌های tpl-* مدال قالب (پورت کامل از index.css دژبان، بدون تداخل نام) + ریسپانسیو ۸۶۰px
- frontend/public/template.docx: کپی قالب Word از زیپ دژبان (در build به dist می‌رود و با /template.docx سرو می‌شود)
- frontend/dist بازسازی شد: index-C4BdJAgA.js (۳۷۷KB) + index-CXvbuTGK.css + template.docx — بررسی باندل: منو/آمار/تقویم/مدال/بسمه‌تعالی/ms-word/summary همه در باندل هستند
- تست: tests/test_kartable.py — ۱۱ تست روی دیتابیس موقت (بذر هر بخش، فیلتر پوشه/زیرپوشه، راند‌ترِیپ ذخیره/خوانده‌شدن/انتقال بین پوشه‌ها/حذف، تغییر آمار پس از خوانده‌شدن، رد پوشه/تاریخ نامعتبر 422، اطلاعیه‌ها، رویداد شمسی امروز، 401 بدون احراز، سرو template.docx) — 11 PASS
- رگرسیون: pytest tests/ کل (۷۷ PASS) + scripts/test_flap_winbox_button.py (11/0)؛ آزمون زندهٔ مسیر واقعی (بذر ۸ آیتم/۱ اطلاعیه/۱ رویداد + template.docx 200) و پاک‌سازی فایل sandbox — سرور کاربر در اولین استفاده خودش بذر می‌زند
- مستندات: README.md (بخش «کارتابل اداری») و AGENTS.md (ردیف kartable.py در نقشهٔ مسیرها + بولت Task 32 + تیتر نقشه تا Task 32)

Stage Summary:
- برگهٔ کارتابل دژبان به‌طور کامل (منو، آمار، اطلاعیه، تقویم، قالب‌های Word، ویرایش نامه) به شبکه‌بان منتقل شد و حالا به دادهٔ واقعی وصل است: بک‌اند مستقل kartable.db با ۸ endpoint و بذر خودکارِ «یک رکورد نمونه برای هر بخش»؛ ذخیره‌سازی/خوانده‌شدن/انتقال/حذف آیتم‌ها و افزودن اطلاعیه/رویداد از طریق UI و API قابل تست است

---
Task ID: 33
Agent: main (Z.ai)
Task: حذف گزارش تکراری دستگاه‌ها در «ایجاد گزارش مسیر (PDF)» بر اساس نام یا ای‌دی دستگاه

Work Log:
- کاربرد: درخواست کاربر — «در برگه گزارش هوشمند زمانی که دکمه ایجاد گزارش مسیر را میزنم دستگاههایی که گزارش آنها تولید شده با در نظر گرفتن نام یا ای دی دستگاهها در گزارش بصورت تکراری تولید نکن»
- ریشهٔ مشکل: `_select_topology_targets` فقط IP اتصال را یکتا می‌کرد؛ دستگاهی که با دو IP (دو ردیف هم‌نام) در دیتابیس ثبت شده بود دو صفحهٔ PDF می‌گرفت
- backend/main.py — `_select_topology_targets`: حذف تکراری حالا با سه کلید انجام می‌شود — IP اتصال (رفتار قبلی)، ای‌دی ردیف دیتابیس (device_id) و نام دستگاه (device_name با casefold)؛ ردیف بی‌نام از identity ثبت‌شدهٔ اینونتوری اینترفیس‌ها (جدول device_interface_ips — Task 25) نام می‌گیرد؛ نخستین ردیفِ هر دستگاه گزارش می‌شود و تعداد ردیف‌های حذف‌شده برگردانده می‌شود (خروجی تاپل (targets, skipped))؛ خطای خواندن اینونتوری انتخاب را نمی‌بندد
- backend/main.py — route_topology_start: `duplicates_skipped` در پاسخ و TOPOLOGY_STATE + پیام فارسی «(N ردیف تکراری با نام/ای‌دی یکسان از گزارش حذف شد — هر دستگاه فقط یک‌بار گزارش می‌شود)»؛ route_topology_progress: فیلد `duplicates_skipped`؛ worker: آمار duplicates_skipped؛ result.pdf: هدر `X-Topology-Duplicates-Skipped`
- frontend/src.jsx — پیام شروع گزارش شمار تکراری‌ها را با اعداد فارسی نشان می‌دهد («— N ردیف تکراری (نام/ای‌دی یکسان) گزارش نمی‌شود») + یک جملهٔ توضیحی در پاراگراف راهنمای پنل گزارش مسیر؛ frontend/dist بازسازی شد (index-C4kNTpPY.js؛ css بدون تغییر)
- تست: tests/test_route_dedupe.py — ۱۲ تست با جایگزینی db (هم‌نام دو IP، هم‌ای‌دی، هم‌IP رگرسیون، نام بدون حساسیت حروف، fallback اینونتوری برای بی‌نام، برتری نام ردیف بر identity، بی‌نام بدون اینونتوری می‌ماند، غیرمیکروتیک تکراری حساب نمی‌شود، IP خالی، سقف max_devices روی یکتاها، انتخاب دستی ips، نگه‌داشتن دستگاه‌های متمایز)
- scripts/test_route_dedupe_e2e.py — ۱۴ بررسی روی اپ واقعی + دیتابیس موقت: سناریوی کاربر (۳ ردیف → ۲ دستگاه، duplicates_skipped=1، پیام «تکراری»، هدر X-Topology-Duplicates-Skipped=1، PDF دقیقاً ۲ صفحه)، حالت «همهٔ دستگاه‌ها» (۵ ردیف → ۳ دستگاه، skipped=2 شامل تکراری اینونتوری)، حالت بدون تکراری (skipped=0)
- رگرسیون: pytest tests/ کل (۸۹ PASS) + scripts/test_device_picker.py (ALL OK — مسیر API با فیلد جدید) + test_route_topology_unit/pdf/inventory_e2e/unreachable_csv (ALL OK) + test_flap_winbox_button (11/0) + test_csv_filename_stamp (ALL PASS)
- مستندات: README.md (بولت «حذف گزارش تکراری هر دستگاه (Task 33)» در بخش گزارش مسیر) و AGENTS.md (بولت Task 33 + تیتر نقشه تا Task 33)

Stage Summary:
- دکمهٔ «ایجاد گزارش مسیر (PDF)» دیگر برای یک دستگاه چند گزارش تولید نمی‌کند: هر دستگاه (با هر کدام از IPهایش) فقط یک صفحهٔ PDF می‌گیرد؛ یکتایی با نام دستگاه و ای‌دی ردیف دیتابیس (به‌علاوهٔ IP قبلی) سنجیده می‌شود و برای ردیف‌های بی‌نام از identity اینونتوری استفاده می‌شود؛ شمار ردیف‌های تکراریِ حذف‌شده در پیام شروع، پیشرفت و هدر PDF گزارش می‌شود

---
Task ID: 34
Agent: main (Z.ai)
Task: جعبهٔ جستجوی بزرگ مرکزچین بالای جدول + پوشهٔ backup و دکمهٔ پشتیبان‌گیری rsc

Work Log:
- کاربرد: درخواست کاربر — «جعبه جستجو یا search box جاش مناسب نیست بزارش بالای اسکرول در مرکز صفحه جای کادر سبز اندازه اش بزرگتر شود» + «یک فولدر به نام backup در مسیر برنامه ایجاد کن که با یک دکمه backup بتواند از طریق api و ورود یوزر پسورد بک آپ دستگاههای میکروتیک با پسوند rsc بگیرد با نام ای دی دستگاهها و ای پی دستگاه در فولدر backup ذخیره کند» (پیوست: اسکرین‌شات با کادر سبز بالای جدول)
- نکتهٔ اجرا: بخشی از این تسک (backup_rsc.py + endpointهای main.py) در اجرای قبلیِ نیمه‌قطع‌شده ساخته شده بود؛ این نوبت تکمیل، تست، اتصال UI و مستندات انجام شد
- frontend/src.jsx (جستجو): بلوک `filter-search` از ردیف فیلترها حذف شد؛ به‌جای آن `div.main-search-bar` بین نوار «لغو انتخاب» و `table-scroll-top` (دقیقاً بالای اسکرول جدول، همان جای کادر سبز اسکرین‌شات) با چیدمان مرکزچین نشست: آیکن 🔍 + input بزرگ (placeholder جدید: «جستجو در IP، نام دستگاه، تگ، اینترفیس‌ها، همسایه‌ها، وایرلس، MAC و لاگ…») + منوی «محدوده جستجو» با همان ۱۲ گزینه + ✕ پاک‌کردن؛ stateهای q/qInput/qField و debounce 350ms/Enter بدون تغییر — فقط جا و اندازه عوض شد
- frontend/style.css: کلاس‌های `.main-search-bar` (flex center، gap 8، wrap)، `.main-search-input` (font-size 15.5px، padding 12px 16px، flex-basis 640px، border آبی 1.5px + focus ring)، `.main-search-field` و `.btn-backup-rsc` (کهربایی b45309) اضافه شد
- frontend/src.jsx (پشتیبان‌گیری): stateهای backupBusy/backupProg + توابع `backupRsc(ips)` (POST /api/devices/backup-rsc با کاربر/رمز API نوار، پایش پیشرفت هر 500ms، پیام موفق/ناموفق + نمونهٔ فایل‌ها، خطای هر دستگاه ناموفق در setError) و `stopBackupRsc` (cancel + abort)؛ دکمهٔ کهربایی «پشتیبان‌گیری rsc (N)» + «توقف پشتیبان» در نوار API کنار «خواندن با API» — دستگاه‌های هدف: انتخاب‌های دارای پورت API (`selectedMikrotikWithApi`)؛ نمودار پیشرفت مشترک نوار با `pp = backupBusy?backupProg:probeProg` برای پشتیبان‌گیری هم فعال شد (عنوان اختصاصی)
- backend/backup_rsc.py (از اجرای قبلی، تکمیل/بازبینی این نوبت): پوشهٔ BACKUP_DIR = <ریشهٔ برنامه>/backup با mkdir در ایمپورت؛ `backup_filename` = «نام‌دستگاه_آی‌پی.rsc» (بی‌نام: device-<id>؛ پاک‌سازی کاراکترهای غیرمجاز)؛ `export_config_via_api` با RouterOSClient پروژه (پورت 8728، timeout حداقل 60s برای /export) و پارس پاسخ (تک !done با =ret= یا چند !re تکه‌ای؛ !trap/!fatal با پیام فارسی)؛ `backup_devices` موازی (ThreadPool، یکتاسازی IP، پیشرفت total/done/ok/failed/current_ip/percent، لغو مشارکتی)؛ `list_backup_files` (فهرست rscها، جدیدترین اول)
- backend/main.py (از اجرای قبلی، بازبینی این نوبت): endpointهای `POST /api/devices/backup-rsc` (ips + username/password + port/timeout/max_workers → نتیجهٔ هر دستگاه + folder)، `GET /api/devices/backup-rsc/progress`، `POST /api/devices/backup-rsc/cancel`، `GET /api/devices/backup-rsc/files` + ایمپورت دوگانهٔ backup_rsc
- .gitignore: `backup/` اضافه شد (پشتیبان‌ها دادهٔ کاربرند و نباید کامیت شوند)؛ خود پوشه با ایمپورت ماژول در هر اجرا ساخته می‌شود
- frontend/dist بازسازی شد: index-kzqRIENY.js + index-LLasaM87.css (CSS جدید برای جستجو/دکمه)
- تست: tests/test_backup_rsc.py — ۱۴ تست (نام فایل با نام/IP/ای‌دی و پاک‌سازی کاراکتر، پارس export تک‌تکه/چندتکه/خالی/trap، ذخیره و پیشرفت، ردیف خطا، لغو وسط کار، endpointها با TestClient لاگین‌شده شامل 422 بدون ips/username و 404 دستگاه ناشناخته و فهرست فایل‌ها) — دام: باید `backend.routeros_api` جایگزین می‌شد نه ماژول هم‌نامِ top-level (ایمپورت دوگانه)
- scripts/test_backup_button.py — ۱۷ بررسی: باندل شامل main-search-bar/input/placeholder جدید، حذف filter-search قدیمی، دکمه/endpointها/عنوان نمودار پشتیبان، CSS مرکزچین و فونت بزرگ‌تر و btn-backup-rsc، endpoint files با TestClient (200) و وجود پوشهٔ backup/ کنار برنامه — ALL OK
- رگرسیون: pytest tests/ کل (۱۰۳ PASS) + scripts/test_route_dedupe_e2e.py (ALL OK) + test_flap_winbox_button.py (11/0) + test_csv_filename_stamp.py (ALL PASS)
- مستندات: README.md (بولت «جعبهٔ جستجوی بزرگ و مرکزچین» + بخش جدید «پشتیبان‌گیری کانفیگ دستگاه‌ها با پسوند rsc») و AGENTS.md (ردیف backup_rsc.py در نقشهٔ ماژول‌ها + بولت Task 34 + تیتر نقشه تا Task 34)

Stage Summary:
- جعبهٔ جستجوی برگهٔ دستگاه‌ها حالا دقیقاً بالای ناحیهٔ اسکرول جدول و مرکز صفحه است (جای کادر سبز اسکرین‌شات) و بزرگ‌تر شده؛ امکانات قبلی (محدودهٔ فیلد، چندواژه، debounce، پاک‌کردن) حفظ شد
- پوشهٔ backup/ کنار برنامه + دکمهٔ «پشتیبان‌گیری rsc» در نوار API: با کاربر/رمز RouterOS از طریق API به دستگاه‌های انتخابی وصل می‌شود، /export را می‌خواند و کانفیگ هر دستگاه را با نام «نام‌دستگاه_آی‌پی.rsc» (بی‌نام: ای‌دی دیتابیس) در پوشهٔ backup ذخیره می‌کند؛ پیشرفت زنده، توقف مشارکتی و فهرست فایل‌ها از طریق endpointها قابل استفاده است

---
Task ID: 35
Agent: main (Z.ai)
Task: تقویت سرعت رابط کاربری — رفع کندی تایپ در جعبه‌های متنی

Work Log:
- کاربرد: درخواست کاربر — «سرعت رابط کاربری را تقویت کن؛ رابط کاربری برای ورود اطلاعات به بکس متنی خیلی کند است»
- ریشه‌یابی: DeviceReports کامپوننتی تک‌تکه با ~۸۵۰ خط است که همهٔ stateهایش (جستجو، فرم افزودن دستگاه، وینباکس، SNMP، کانفیگ گروهی، روت، دیتابیس و…) در یکجا تعریف شده؛ هر کلید در هر ورودی متنی کل کامپوننت را دوباره رندر می‌کرد — از جمله rows.map کل جدول دستگاه‌ها (تا ۱۸ ستون در هر ردیف، صفحهٔ «همه» تا ۱۰۰٫۰۰۰ ردیف) و هیچ useMemo/React.memo/useCallback در فایل نبود. دو تقویت‌کنندهٔ کندی: (۱) MainApp هنگام اسکن فعال هر ۱.۲ ثانیه setJob می‌زند و فرزندانش (از جمله DeviceReports) را رندر می‌کرد؛ (۲) هنگام SNMP/API/پشتیبان rsc، استعلام پیشرفت هر ۴۰۰-۵۰۰ms همین کار را می‌کرد. ویرایشِ درجایِ نام هم valueاش state بود → هر کلیدش کل جدول را رندر می‌کرد.
- frontend/src.jsx — جدول دستگاه‌ها داخل useMemo (نام tableEl، وابستگی‌ها: rows/selected/visibleCols/editNameIp/sortBy/sortOrder) ساخته می‌شود؛ تایپ در هر ورودی دیگر جدول را نمی‌سازد. توابع جدول (openWinbox/saveName/toggleSelect/toggleSelectAll/handleSort) از liveRef.current (useRef) صدا زده می‌شوند تا JSXِ memo شده بدون stale closure همیشه تازه‌ترین نسخه را صدا بزند (setTextModal/setEditNameIp ستتر پایدارند). ویرایش درجایِ نام uncontrolled شد: ref={editNameInputRef} + defaultValue={d.device_name}، saveName مقدار را از ref می‌خواند، state editNameVal حذف شد → تایپ در ویرایشگر نام صفر رندر. کلیلک روی نام فقط setEditNameIp می‌زند.
- frontend/src.jsx — شش کارت سنگین با React.memo بسته شدند: DeviceReportsM/EmailServerCardM/SmartReportsM/KartableM/VpnManagerCardM/BackendCardM و در MainApp استفاده شدند (props ثابت → bail-out)؛ onRoutes با useCallback پایدار شد (بدون آن memo بی‌اثر بود). جستجوی DevicePickerModal (تا ۱۰۰٫۰۰۰ ردیف فیلتر + ۳۰۰ ردیف نمایش) با useDeferredValue فیلتر می‌شود.
- frontend/dist بازسازی شد: index-BKrWn6Sc.js (۳۸۱KB؛ +۴KB نسبت به قبل) — CSS بدون تغییر
- تست: scripts/test_ui_speed_react_memo.py — ۲۵ بررسی: نشانگرهای سورس (useMemo جدول با وابستگی‌های کامل، liveRef، uncontrolled بودن ویرایش نام، حذف editNameVal، شش React.memo، DeviceReportsM در تب‌ها، useCallback، useDeferredValue) + باندل (index.html → باندل موجود، رشته‌های شاخص فارسی، defaultValue) + سلامت بک‌اند (auth/check 401 بدون نشست، سرو UI، لاگین، databases) — 25 PASS
- رگرسیون: pytest tests/ کل (۱۰۳ PASS) + scripts/test_backup_button.py (ALL OK) + test_flap_winbox_button.py (11/0) + test_csv_filename_stamp.py (ALL PASS)
- مستندات: README.md (بولت «سرعت رابط کاربری (Task 35)») و AGENTS.md (تیتر نقشه تا Task 35 + بولت Task 35 + گاتچا «JSX جدول داخل useMemo است؛ وابستگی‌ها و liveRef را به‌روز کنید»)

Stage Summary:
- تایپ در همهٔ جعبه‌های متنی برگه‌های برنامه سبک شد: کلیدهای تایپ دیگر جدول دستگاه‌ها (تا هزاران سلول) را رندر نمی‌کنند — جدول فقط با تغییر واقعی داده/ستون/انتخاب/مرتب‌سازی دوباره ساخته می‌شود؛ استعلام‌های دوره‌ای (وضعیت اسکن ۱.۲s، پیشرفت خواندن/پشتیبان ۴۰۰-۵۰۰ms) هم فقط خودِ نمودار را به‌روز می‌کنند نه کل برگه را. رفتار و ظاهر قبلی دست‌نخورده ماند (همان debounce ۳۵۰ms جستجو، همان امکانات جدول) — فقط سرعت.

---
Task ID: 36
Agent: main (Z.ai)
Task: تغییر نام پوشهٔ backup به mik_backup + عیب‌یابی شکست پشتیبان‌گیری rsc با یوزر/پسورد درست

Work Log:
- کاربرد: «فولدر backup را به نام mik_backup تغییر نام بده» + «شکل را ببین؛ با اینکه لاگین اطلاعاتش شامل یوزر پسورد درسته ولی نتونست بک اپ rsc را بگیرد؛ بررسی کن نتیجه را بفرست» + «روی گیت هاب فایلهای داکیومنت و AGENTS.md را بروز کن» (پیوست: اسکرین‌شات نمودار پیشرفت با ok=1/failed=2/باقی‌مانده=۴۵ از ۵۰ دستگاه)
- تغییر نام پوشه: BACKUP_DIR در backend/backup_rsc.py از backup/ به mik_backup/؛ تابع `_migrate_old_backup_folder` هنگام ایمپورت پوشهٔ قدیمی backup/ را به mik_backup/ منتقل می‌کند (اگر مقصد نباشد rename یک‌جا؛ اگر هر دو باشند فقط rscهای تکراری‌نشدنی؛ دادهٔ کاربر از بین نمی‌رود)؛ .gitignore به mik_backup/ تغییر کرد؛ متن‌های UI (۵ جای «پوشهٔ backup/») و docstringهای endpointهای main.py به‌روز شدند؛ در اجرای تست، پوشهٔ خالی backup/ پروژه واقعاً به mik_backup/ منتقل شد
- عیب‌یابی شکست (ریشهٔ مشکل): «خواندن با API» و پشتیبان‌گیری از یک کلاینت (RouterOSClient) و یک ورود استفاده می‌کنند؛ پس رمز/کاربر درست است. دو علت اصلی شکستِ export: (۱) سرویس api (پورت 8728) روی دستگاه فعال/در دسترس نیست — Winbox از سرویسِ جداگانهٔ 8291 می‌آید و با API ربطی ندارد (تأیید «Known issues» کلاینت‌های رایج: `/ip service enable api`)؛ کاربر هم باید مجوز policy «api» داشته باشد؛ (۲) دستور /export روی خودِ روتر اجرا می‌شود و روی RouterOS v7 با کانفیگ بزرگ CPU ۱۰۰٪ می‌زند و دقیقه‌ها طول می‌کشد (تأیید فروم میکروتیک: «100% CPU use running the /export command and timeout errors»؛ hAP lite v7.14) — قبلاً کفِ timeout ۶۰ ثانیه بود و اتصال اولیه هم همان timeout را می‌گرفت؛ با ۶ رشته روی ۵۰ دستگاه، صف کند می‌شد و پیام خطاها انگلیسی/عمومی بود
- اصلاحات بک‌اند: `_friendly_error(e, stage)` در backup_rsc.py — علت فارسیِ دقیق بر اساس مرحلهٔ شکست: connect-refused («سرویس API روی دستگاه غیرفعال است… /ip service enable api»)، connect-timeout («فایروال پورت را فیلتر می‌کند؛ Winbox 8291 جداگانه است»)، login («رمز یا مجوز policy «api»»)، read-timeout («/export بیش از حد طول کشید — کانفیگ دستگاه بزرگ است؛ timeout را بیشتر کنید»)، reset/قطع اتصال؛ متن خام خطا داخل پیام حفظ می‌شود. RouterOSClient پارامتر `connect_timeout` جداگانه گرفت (در بک‌آپ سقف ۱۲ ثانیه) تا دستگاه بی‌API صف را نیندازد؛ کفِ timeout خواندن export از ۶۰ به ۹۰ ثانیه و سقف مجاز درخواست (BackupRscRequest) از ۱۲۰ به ۶۰۰ ثانیه با پیش‌فرض ۴۵ رسید
- frontend/src.jsx: پیام‌ها/عنوان نمودار/tooltip دکمه به «پوشهٔ mik_backup/» تغییر کرد؛ frontend/dist بازسازی شد (index-CtmlfBlx.js؛ CSS بدون تغییر)
- تست: tests/test_backup_rsc.py — ۱۴ تست قبلی + ۹ تست جدید (پیام عیب‌یابی refused/timeout/login، classify مرحله در export واقعیِ شبیه‌سازی‌شده، جدایی connect_timeout از read_timeout، مهاجرت پوشه در حالت rename و merge، نام جدید BACKUP_DIR) = ۲۳ PASS
- رگرسیون: pytest tests/ کل (۱۱۲ PASS) + scripts/test_backup_button.py (بررسی نام mik_backup + مهاجرت + پیام‌های عیب‌یابی — ALL OK) + test_ui_speed_react_memo.py (25 PASS) + test_flap_winbox_button.py (11/0) + test_csv_filename_stamp.py (ALL PASS)
- مستندات: README.md (بخش rsc: نام پوشهٔ جدید + مهاجرت خودکار + بولت «عیب‌یابی خطاهای پشتیبان‌گیری» با دو علت رایج و راه حل) و AGENTS.md (ردیف ماژول، تیتر نقشه تا Task 36، بولت کامل Task 36)
- گیت: کامیت قبلی Task 35 (ba59257) که push نشده بود در شروع این نوبت push شد؛ کامیت جدید Task 36 جداگانه push می‌شود

Stage Summary:
- پوشهٔ پشتیبان‌های rsc حالا mik_backup/ است و پوشهٔ قدیمی با فایل‌ها خودکار منتقل می‌شود
- علت شکست بک‌آپ با یوزر/پسورد درست دو چیز شایع است: غیرفعال/فیلتر بودن سرویس api روی دستگاه (پورت 8728 — جدا از Winbox 8291) یا کندی ذاتی /export روی روترهای پرکانفیگ (v7، CPU سنگین)؛ حالا علت هر دستگاه ناموفق به فارسیِ دقیق با راهنمای رفع نمایش داده می‌شود، اتصال اولیه سریع fail می‌شود و پنجرهٔ انتظار export بزرگ‌تر است

---
Task ID: 37
Agent: main (Z.ai)
Task: گزینهٔ ثبت لاگ خطا در برگهٔ راهبری سیستم + رفع خطای پشتیبان‌گیری rsc با یوزر/پسورد درست

Work Log:
- کاربرد: «نتونست بک اپ بگیره؛ یک گزینه ثبت لاگ خطا در برگهٔ مدیریت سیستم ایجاد کن؛ خطا را برطرف کن؛ یوزر پسورد ورود مشکلی نداره» (پیوست: اسکرین‌شات جعبهٔ خطا — «۵ دستگاه ناموفق بود: 172.17.12.34 – ورود API ناموفق (6) …؛ 172.18.1.106 – خروجی /export خالی بود…»)
- ریشه‌یابی با مستندات/فروم میکروتیک: (۱) «invalid user name or password (6)» پیام واقعی RouterOS است و فقط رمزِ غلط نیست — روی ROS قدیمی (<6.43) روش ورودِ جدید (v6.43+) رد می‌شود و اگر گروه کاربر مجوز policy «api» نداشته باشد هم ورود API رد می‌شود (نمونه‌های گزارش‌شده: RouterOS-api issue#45، MikroTik::API#11 — «99.9% sure credentials are correct»)؛ تلاش دومِ قبلی روی همان سوکت انجام می‌شد که پس از یک ورود ناموفق ممکن است بسته باشد؛ (۲) «خروجی /export خالی بود» رفتار مستند ROS 6 است: خروجی مستقیم /export از API فقط !done می‌دهد (فروم «Export configuration via API» و «How to read file content using API?») — باید export=file گرفت و محتوا را خواند؛ خواندن محتوا هم سقف ~۴KB دارد
- backend/errorlog.py (جدید): ثبت خطاها با زمان/منبع/IP/stage/علت در mik_log/errorlog.jsonl (هر خط JSON، thread-safe با Lock)، کلید فعال/خاموش ماندگار در mik_log/config.json (پیش‌فرض فعال)، چرخش خودکار در ۲MB (نگه‌داشتن ۵۰۰ رویداد آخر)، read_errors (جدیدترین اول + فیلتر منبع) و count/clear
- backend/backup_rsc.py: تابع `_export_via_file` — روش دوم خواندن کانفیگ: «/export =file=mikbk-<hex>» (trap آن با راهنمای مجوز «read,write,api»)، پول «/file/print ?name=… =.proplist=.id,name,size» تا ثبات اندازه دو بار پشت‌سرهم (۱۲ تلاش، ثانیه‌ای؛ پوشش پسوند اضافه‌نشدنِ .rsc)، خواندن «=.proplist=contents»، حذف فایل موقت با «/file/remove» (خطایش بی‌ضرر)؛ export_config_via_api حالا دومرحله‌ای است (مستقیم → روش فایل) و پیام نهایی هم پاسخ مستقیم و هم علت شکست روش فایل را نگه می‌دارد؛ خطای هر دستگاه ناموفق + خلاصهٔ پایان کار (فقط وقتی failed>0) در errorlog ثبت می‌شود
- backend/routeros_api.py — login(): پس از ردشدن ورود مستقیم (v6.43+)، روش چالش-پاسخ قدیمی روی **اتصال تازه** (close+connect) امتحان می‌شود؛ در شکست هر دو روش، پیام خام روتر (نمونه: (6)) + نتیجهٔ روش دوم در یک پیام ترکیبی بالا می‌آید
- backend/main.py: سه endpoint — GET /api/errorlog (لیست + count + فولدر + فیلتر منبع)، POST /api/errorlog/toggle، POST /api/errorlog/clear + ثبت خطاهای probe-api در لاگ؛ endpointها زیر همان AuthMiddleware
- frontend/src.jsx: کامپوننت `ErrorLogCard` (با React.memo → ErrorLogCardM) در برگهٔ «راهبری سیستم» بالای DeviceReportsM: کلید «ثبت لاگ خطا فعال باشد»، دکمه‌های نمایش/به‌روزرسانی/پاک‌کردن (با confirm)، شمارندهٔ رویدادها، فیلتر متنی (useMemo روی ۲۰۰ رویداد آخر) و جدول زمان/منبع/دستگاه/علت (متن خام جدا با کلاس کم‌رنگ)؛ فراخوانی فقط در mount — بدون polling تا رندر اضافه نشود؛ style.css: کلاس‌های .errorlog-* (بوردر کهربایی، جدول سبک tablewrap)
- frontend/dist بازسازی شد: index-l5P27r00.js (۳۸۵KB) + index-J6Ia62E7.css (CSS تغییر کرد)
- تست: tests/test_backup_rsc.py — ۳۳ تست (۱۰ جدید: روش فایل موفق/حذف فایل موقت/فایل بزرگ‌تر از ۴KB/trap مستقیم→فایل/trap مجوز write، ورود با اتصال تازه/پیام ترکیبی (6)، ثبت خطا در errorlog/خاموش‌بودن ثبت، roundtrip سه endpoint) — _FakeClient هم اسکریپت چندمرحله‌ای شد (هر talk یک مرحله؛ آخرین تکرار)؛ scripts/test_errorlog_ui.py (جدید) — ۳۰ بررسی سورس/باندل/CSS/endpoint/بک‌اند
- رگرسیون: pytest tests/ کل (۱۲۲ PASS) + test_backup_button.py (ALL OK) + test_ui_speed_react_memo.py (25/0) + test_flap_winbox_button.py (11/0) + test_csv_filename_stamp.py (ALL PASS)
- مستندات: README.md (بخش rsc: عنوان + روش دو‌مرحله‌ای export + علت جدید (6) با راهنما + بولت کارت لاگ خطا) و AGENTS.md (ردیف errorlog در نقشهٔ ماژول، تیتر تا Task 37، بولت کامل Task 37، دو گاتچا: پول روش فایل در تست‌ها و patch مسیرهای errorlog)

Stage Summary:
- حالا هر خطای پشتیبان‌گیری/خواندن API در برگهٔ راهبری سیستم قابل مرور است: کارت «لاگ خطاها» با کلید فعال/خاموش، فیلتر و جدول زمان/منبع/دستگاه/علت — داده‌ها در mik_log/errorlog.jsonl می‌مانند و با ری‌استارت برنامه از بین نمی‌روند
- دو علت واقعی شکستِ «با یوزر/رمز درست» رفع یا شفاف شد: (۱) خروجی خالی /export روی RouterOS 6 — حالا با روش فایل خودکار جبران می‌شود (تا سقف ~۴KB که خودِ RouterOS می‌گذارد؛ پیام خطا اندازهٔ فایل را می‌گوید)؛ (۲) ورود (6) روی ROS قدیمی — روش چالش-پاسخ روی اتصال تازه دوباره امتحان می‌شود؛ اگر گروه کاربر مجوز «api» نداشته باشد، پیام دقیقاً می‌گوید چه policy‌ای لازم است

---
Task ID: 37 (ادامه — ادغام دلتا روی نسخهٔ ریموت)
Agent: main (Z.ai)
Task: همگام‌سازی با کامیت موازی 34aa550 (نشست دیگر همان درخواست را اجرا و push کرده بود) + افزودن مکمل‌ها بدون تکرار

Work Log:
- وضعیت: push این نشست reject شد چون کامیت 34aa550 («feat(errorlog): error log card in system tab + two-step rsc export (file method) + fresh-connection login retry») پیش‌تر روی ریموت بود — همان درخواست کاربر با معماری دیگری (errorlog.py در mik_log/، endpointهای /api/errorlog، ErrorLogCard، روش دو‌مرحله‌ای export=file برای ROS 6). به‌جای تحمیل دو پیاده‌سازی موازی: reset به 34aa550 و افزودن «دلتای مکمل» به‌صورت یک کامیت تمیز (نسخهٔ کامل این نشست در شاخهٔ محلی task37-alt-backup حفظ شد)
- مکمل‌های افزوده‌شده روی معماری ریموت:
  1) `_friendly_error` مرحلهٔ login: پیام «(6)» حالا سه علت رایج + مسیر رفع (Winbox ← System → Users ← رمز یکسان/مجوز api و read/RADIUS) می‌دهد — تجربهٔ کاربر: همان یوزر/رمز روی 172.18.1.106/107 ورود موفق داشته پس رد شدن ۵۰ دستگاه دیگر سمت روتر است
  2) errorlog.py: پارامتر level (پیش‌فرض error — سازگار با فراخوانی‌های موجود) + helperهای log_warn/log_info + فیلتر level و جستجوی آزاد q در read_errors (case-insensitive روی message/raw/ip/source)
  3) main.py: GET /api/errorlog پارامترهای level/q گرفت؛ endpoint جدید GET /api/errorlog/csv (BOM + filename=error_log_<file_stamp>.csv + ۷ ستون فارسی)؛ هوک لاگ برای انتقال کانفیگ گروهی (_log_push_failures در _cfg_push_worker شامل مسیر لغو) و خواندن SNMP + سقف per-run (_LOG_PER_RUN_CAP=500) + خلاصهٔ اجرا برای probe-api/SNMP/push/backup
  4) backup_rsc.py: خلاصهٔ هر اجرای پشتیبان‌گیری همیشه ثبت می‌شود — warn اگر خطا داشته، info اگر کاملاً موفق (قبلاً فقط در صورت خطا و با level=error)
  5) frontend/src.jsx — ErrorLogCard: ستون «سطح» با بج رنگی (خطا/هشدار/اطلاع) + دکمهٔ «خروجی CSV» (نام از Content-Disposition با fallback csvStamp)؛ style.css: کلاس‌های errorlog-badge-*؛ dist بازسازی شد (index-D2ahaQqg.js / index-CCzi-HrQ.css)
  6) تست‌ها: tests/test_login_protocol.py (۶ تست سوکتی با سرور API تقلبی — روی login نسخهٔ ریموت هم پاس: plaintext/رمز غلط (6)/چالش-پاسخ v6/اتصال تازه/بی‌چالش/اتصال دوم معیوب)؛ tests/test_errorlog_delta.py (۶ تست: سطوح/پیش‌فرض error برای ردیف قدیمی/فیلتر q/endpoint فیلترها/CSV با BOM و مهر/401)؛ به‌روزرسانی test_friendly_error_login_hint + ۲ تست جدید ((6) و سطح خلاصهٔ اجرا) در test_backup_rsc.py
  7) رگرسیون: pytest tests/ کل = ۱۳۶ PASS + scripts/test_errorlog_ui.py (30 بررسی — بدون تغییر پاس) + build dist موفق

Stage Summary:
- مخزن حالا یک پیاده‌سازی منسجم دارد (نه دو موازی): معماری errorlog ریموت + عیب‌یابی سه‌علتهٔ ورود، سطح‌بندی warn/info، جستجوی سرورساید، خروجی CSV و پوشش لاگ برای هر چهار عملیات (پشتیبان‌گیری/خواندن API/انتقال کانفیگ/SNMP)

---
Task ID: 38
Agent: main (Z.ai)
Task: دکمهٔ «نمایش کانفیگ» کنار نام هر دستگاه — نمایش فایل rsc ذخیره‌شده در mik_backup/

Work Log:
- کاربرد: «در کنار نام هر دستگاه یک دکمه نمایش کانفیگ ایجاد کن که کانفیگ با پسوند rsc دستگاه را در فولدر mik_backup نمایش دهد اگر کانفیگ وجود نداشته باشد این دکمه غیرفعال باشد»
- backend/backup_rsc.py: دو تابع جدید — `find_backup_for_device(device_name, ip, dev_id)` (اول نام دقیق backup_filename، سپس fallback الگوی «*_<IP>.rsc» برای فایل‌های با نام قدیمی، جدیدترین بر اساس mtime؛ خروجی file/size/modified یا None) و `read_backup_file(filename)` (خواندن امن متن rsc: فقط نام سادهٔ فایل + اصرار خروج resolve داخل BACKUP_DIR (ضد path traversal) + پسوند .rsc اجباری + سقف ۲MB + errors=replace)
- backend/main.py: دو endpoint زیر AuthMiddleware — GET /api/devices/backup-rsc/check?ips=… (نقشهٔ ip → {exists,file,size,modified} با خواندن نام دستگاه از دیتابیس فعال — مبنای فعال/غیرفعال بودن دکمه) و GET /api/devices/backup-rsc/view?file=… (متن کانفیگ؛ 404 فایل ناموجود، 400 نام نامعتبر/مسیرگیری)
- frontend/src.jsx: state `backupMap` + `refreshBackupMap(list)` (fetch check برای دستگاه‌های صفحهٔ جاری؛ useEffect روی rows + فراخوانی در finallyِ backupRsc تا دکمهٔ دستگاه‌های تازه بک‌آپ‌گرفته فوراً فعال شود) + `showDeviceConfig(ip)` (fetch view → setTextModal)؛ دکمهٔ «نمایش کانفیگ» (btn-detail btn-cfg-rsc، سبز) در name-actions کنار نام هر دستگاه — بدون توجه به میکروتیک بودن، ولی disabled وقتی فایل نیست (title راهنما: «کانفیگ rsc در mik_backup/ موجود نیست — ابتدا پشتیبان‌گیری rsc بگیرید»)؛ backupMap به depsِ useMemo جدول اضافه شد (بدون آن دکمه هرگز فعال نمی‌شد)؛ مدال متن: نمایش متادیتا (نام فایل/تاریخ ذخیره/حجم فارسی) + دکمهٔ جدید «دانلود .rsc» (Blob) وقتی textModal.downloadFile هست — مدال‌های قبلی دست‌نخورده
- frontend/style.css: کلاس‌های .btn-detail.btn-cfg-rsc (سبز: #dcfce7/#166534/#86efac) + :disabled (cursor:not-allowed، opacity .4)
- frontend/dist بازسازی شد: index-C5S6BqMn.js (۳۸۸KB) + index-BF1IIM_C.css
- تست: scripts/test_backup_view_button.py (جدید، ۲۳ بررسی — ALL OK): سورس فرانت/CSS + find_backup_for_device (نام دقیق/fallback نام قدیمی/None) + هر چهار endpoint با TestClient (check exists=true/false، view محتوا+متا، 404، مسیرگیری ../ → 400، پسوند غیر rsc → 400) + پاک‌سازی؛ رگرسیون: scripts/test_backup_button.py (ALL OK) + tests/test_backup_rsc.py (exit 0)
- بررسی بصری با مرورگر واقعی (uvicorn + dist): ۵۰ ردیف صفحه → ۵۰ دکمه (۴۹ disabled، ۱ enabled برای فایل تست)؛ کلیک دکمهٔ فعال → مدال با عنوان «کانفیگ rsc — <IP>»، متادیتا و متن کانفیگ + دکمهٔ «دانلود .rsc» تأیید شد (اسکرین‌شات هر دو حالت)

Stage Summary:
- کنار نام هر دستگاه دکمهٔ «نمایش کانفیگ» هست: اگر فایل rsc آن دستگاه در mik_backup/ باشد کلیک‌پذیر است و متن کانفیگ را (با نام فایل، تاریخ ذخیره و حجم) در مدال نشان می‌دهد و امکان دانلود .rsc هم دارد؛ اگر فایل نباشد دکمه غیرفعال با tooltip راهنماست
- یافتن فایل فقط به نام دقیق وابسته نیست: اگر نام دستگاه بعد از بک‌آپ عوض شده باشد فایل با الگوی «*_<IP>.rsc» پیدا می‌شود (جدیدترین فایل ملاک است)

---
Task ID: 39
Agent: main (Z.ai)
Task: اصلاح رنگ و فونت دو دکمهٔ بی‌متنِ مدال «انتخاب دستگاه‌ها از دیتابیس» (حذف انتخاب‌ها / انتخاب همه موارد فیلترشده)

Work Log:
- کاربرد (با اسکرین‌شات): «رنگ و فونت این دکمه ها را درست کن» — دو دکمهٔ میانی پایین مدال انتخاب دستگاه خالی/بی‌متن دیده می‌شدند (دو جعبهٔ سفید کنار «انصراف» و «تایید انتخاب»)
- ریشه‌یابی: آن دو دکمه کلاس CSS نداشتند؛ قانون سراسری button (خط ۴ style.css) متن سفید می‌دهد و قانون .modal-actions button پس‌زمینهٔ سفید — متن سفید روی سفید = نامرئی
- frontend/src.jsx: کلاس btn-modal-secondary به هر دو دکمهٔ DevicePickerModal («انتخاب همه موارد فیلترشده» و «حذف انتخاب‌ها») اضافه شد
- frontend/style.css: استایل جدید .btn-modal-secondary (زمینهٔ آبی روشن #e0f2fe، متن سرمه‌ای #075985، حاشیهٔ #7dd3fc، فونت inherit/Vazirmatn + bold، سایز هم‌اندازهٔ btn-modal-save/close با !important برای غلبه بر قانون line-86) + hover (#bae6fd) + حالت disabled؛ ضمانت ریشه‌ای: به قانون .modal-actions button نیز color:#1f2937 اضافه شد تا هر دکمهٔ بی‌کلاس آینده هم متن مرئی داشته باشد
- frontend/dist بازسازی شد: index-CdfnG5kq.js + index-Lhdrnayg.css
- رگرسیون: scripts/test_device_picker.py (ALL OK) — عملکرد دو دکمه هم در مرورگر واقعی تست شد: «انتخاب همه موارد فیلترشده» ۳۸۶ دستگاه را انتخاب کرد (شمارندهٔ انتخاب‌شده: ۳۸۶) و «حذف انتخاب‌ها» صفر کرد
- بررسی بصری: اسکرین‌شات مدال — هر چهار دکمه (تایید/انتخاب همه/حذف/انصراف) متن واضح و سبک هماهنگ دارند

Stage Summary:
- دو دکمهٔ فرعی مدال انتخاب دستگاه حالا با رنگ آبی روشن/متن سرمه‌ای و فونت bold کاملاً مرئی‌اند؛ علت اصلی (متن سفید روی زمینهٔ سفید برای دکمه‌های بی‌کلاس در modal-actions) نیز از ریشه بسته شد
