#!/bin/sh
set -eu

project_root=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
cd "$project_root"

dashboard_port=8010
runtime_dir="$project_root/.tmp"
pid_file="$runtime_dir/server-${dashboard_port}.pid"
state_file="$runtime_dir/server-${dashboard_port}.state"
log_file="$runtime_dir/server-${dashboard_port}.log"
service_label="com.herald-decoder.dashboard"
service_domain="gui/$(id -u)"
service_plist="/Users/$(id -un)/Library/LaunchAgents/${service_label}.plist"
service_template="$project_root/dashboard/launchd/${service_label}.plist.template"
command="${1:-start}"
takeover_option="${2:-}"
case "$takeover_option" in ''|--takeover) ;; *) printf 'Unknown option: %s\n' "$takeover_option" >&2; exit 2 ;; esac

mkdir -p "$runtime_dir"

# The dashboard serves the live Lab 002 decoder artifact, so it must use the
# same fail-closed, version-pinned runtime as every numerical decoder run.
# Do not fall back to a bare interpreter: that would silently disable Numba
# and make an interactive artifact appear to be an algorithmic regression.
research_launcher="$project_root/run_research_python.sh"
if [ ! -x "$research_launcher" ]; then
    printf 'Accelerated research launcher is unavailable: %s\n' "$research_launcher" >&2
    exit 2
fi

saved_pid() { [ -f "$pid_file" ] && sed -n '1p' "$pid_file"; }
listener_pid() {
    pid=""
    if command -v lsof >/dev/null 2>&1; then
        pid=$(lsof -tiTCP:"$dashboard_port" -sTCP:LISTEN 2>/dev/null | sed -n '1p')
    fi
    if [ -z "$pid" ] && command -v ss >/dev/null 2>&1; then
        pid=$(ss -ltnp "sport = :$dashboard_port" 2>/dev/null | sed -n 's/.*pid=\([0-9][0-9]*\).*/\1/p' | sed -n '1p')
    fi
    if [ -z "$pid" ]; then
        pid=$(python3 -c "
import os, pathlib
port = $dashboard_port
inodes = set()
for path in ('/proc/net/tcp', '/proc/net/tcp6'):
    candidate = pathlib.Path(path)
    if not candidate.exists():
        continue
    for line in candidate.read_text().splitlines()[1:]:
        parts = line.split()
        if parts[3] != '0A':
            continue
        if int(parts[1].rsplit(':', 1)[1], 16) == port:
            inodes.add(parts[9])
if not inodes:
    raise SystemExit
for proc in pathlib.Path('/proc').iterdir():
    if not proc.name.isdigit():
        continue
    try:
        for entry in (proc / 'fd').iterdir():
            try:
                target = os.readlink(entry)
            except OSError:
                continue
            if target.startswith('socket:[') and target[8:-1] in inodes:
                print(proc.name, end='')
                raise SystemExit
    except (FileNotFoundError, PermissionError):
        continue
" 2>/dev/null)
    fi
    printf '%s' "$pid"
}
process_command() { ps -p "$1" -o command= 2>/dev/null | sed -n '1p'; }
process_cwd() {
    if command -v lsof >/dev/null 2>&1; then
        lsof -a -p "$1" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p' | sed -n '1p'
        return
    fi
    readlink -f "/proc/$1/cwd" 2>/dev/null
}
project_api_identity() {
    curl -fsS --max-time 1 "http://localhost:$dashboard_port/api/project" 2>/dev/null \
        | grep -F -- '"title": "Herald Decoder"' >/dev/null
}
is_this_dashboard_process() {
    candidate_pid=$1
    candidate_command=$(process_command "$candidate_pid")
    candidate_cwd=$(process_cwd "$candidate_pid")
    if [ "$candidate_cwd" = "$project_root" ]; then
        # The fixed port plus the exact project working directory is sufficient
        # when a restricted environment hides the process command line.
        if [ -z "$candidate_command" ] || printf '%s' "$candidate_command" | grep -E -- 'dashboard(/server\.py|\.server)' >/dev/null; then
            return 0
        fi
    fi
    project_api_identity
}
dashboard_is_tracked() {
    pid=$(saved_pid)
    listener=$(listener_pid)
    [ -n "$pid" ] && [ "$pid" = "$listener" ] && kill -0 "$pid" 2>/dev/null
}
stop_process() {
    pid_to_stop=$1
    kill "$pid_to_stop"
    attempts=0
    while kill -0 "$pid_to_stop" 2>/dev/null && [ "$attempts" -lt 25 ]; do attempts=$((attempts + 1)); sleep 0.2; done
    if kill -0 "$pid_to_stop" 2>/dev/null; then print_dashboard_card "FAILED" "process did not stop" "PID $pid_to_stop" >&2; return 1; fi
}
# Prefer GNU sha1sum. macOS shasum is a Perl script and spam-warns when
# LANG requests a locale the machine does not have generated.
checksum() {
    if command -v sha1sum >/dev/null 2>&1; then
        sha1sum "$@"
    else
        LC_ALL=C shasum "$@"
    fi
}
dashboard_fingerprint() {
    find dashboard -type f -name '*.py' -print | sort | while IFS= read -r path; do checksum "$path"; done | checksum | awk '{print $1}'
}
saved_fingerprint() { [ -f "$state_file" ] && sed -n 's/^fingerprint=//p' "$state_file" | sed -n '1p'; }
write_state() { printf 'pid=%s\nfingerprint=%s\n' "$1" "$(dashboard_fingerprint)" >"$state_file"; }
dashboard_is_current() { dashboard_is_tracked && [ -n "$(saved_fingerprint)" ] && [ "$(saved_fingerprint)" = "$(dashboard_fingerprint)" ]; }
remove_dashboard_state() { rm -f "$pid_file" "$state_file"; }
service_is_loaded() { launchctl print "$service_domain/$service_label" >/dev/null 2>&1; }
wait_for_dashboard() {
    attempts=0
    while [ "$attempts" -lt 25 ]; do
        if project_api_identity; then return 0; fi
        attempts=$((attempts + 1)); sleep 0.2
    done
    return 1
}
install_service() {
    if [ ! -f "$service_template" ]; then
        printf 'LaunchAgent template is unavailable: %s\n' "$service_template" >&2; return 2
    fi
    listener=$(listener_pid)
    if [ -n "$listener" ] && is_this_dashboard_process "$listener"; then stop_process "$listener"; fi
    remove_dashboard_state
    service_dir=$(dirname "$service_plist")
    mkdir -p "$service_dir" "$runtime_dir"
    temporary_plist="${service_plist}.tmp-$"
    sed "s|__PROJECT_ROOT__|$project_root|g" "$service_template" >"$temporary_plist"
    plutil -lint "$temporary_plist" >/dev/null
    mv "$temporary_plist" "$service_plist"
    launchctl bootout "$service_domain/$service_label" >/dev/null 2>&1 || true
    launchctl bootstrap "$service_domain" "$service_plist"
    launchctl kickstart "$service_domain/$service_label"
    if wait_for_dashboard; then print_dashboard_card "RUNNING" "launchd · persistent" "$service_label"; return 0; fi
    print_dashboard_card "FAILED" "launchd service did not answer" "$service_label" >&2; return 1
}
uninstall_service() {
    launchctl bootout "$service_domain/$service_label" >/dev/null 2>&1 || true
    rm -f "$service_plist"; remove_dashboard_state
    print_dashboard_card "STOPPED" "persistent service removed" "—"
}

print_dashboard_card() {
    status_label=$1; code_label=$2; pid_label=${3:-—}
    printf '\n┌─ Herald Decoder Server ──────────────────────\n'
    printf '│ Status    %s\n' "$status_label"
    printf '│ Address   http://localhost:%s\n' "$dashboard_port"
    printf '│ Process   %s\n' "$pid_label"
    printf '│ Code      %s\n' "$code_label"
    printf '│\n'
    printf '│ Commands  start · status · restart · stop · logs\n'
    printf '└─────────────────────────────────────────────\n'
}
print_usage_card() {
    printf '\nHerald Decoder Server launcher\n\n'
    printf '  ./run_server.sh           Start, or take over a previous Herald Decoder instance\n'
    printf '  ./run_server.sh status    Show service health\n'
    printf '  ./run_server.sh restart   Stop and start the service\n'
    printf '  ./run_server.sh stop      Stop the managed service\n'
    printf '  ./run_server.sh logs      Show the last 100 log lines\n'
    printf '  ./run_server.sh install-service  Install and start the persistent macOS LaunchAgent\n'
    printf '  ./run_server.sh uninstall-service  Stop and remove the persistent macOS LaunchAgent\n\n'
    printf '  ./run_server.sh foreground  Run under a supervising terminal or agent\n\n'
    printf '  Add --takeover to start or stop an unrelated process on the selected port.\n'
    printf 'This project always uses port 8010.\n'
}
start_dashboard() {
    if service_is_loaded; then
        if project_api_identity; then print_dashboard_card "RUNNING" "launchd · persistent" "$service_label"; return 0; fi
        launchctl kickstart -k "$service_domain/$service_label"
        if wait_for_dashboard; then print_dashboard_card "RUNNING" "launchd · restarted" "$service_label"; return 0; fi
        print_dashboard_card "FAILED" "launchd service did not answer" "$service_label" >&2; return 1
    fi
    if dashboard_is_tracked; then
        if dashboard_is_current; then print_dashboard_card "RUNNING" "current" "PID $(saved_pid)"; return 0; fi
        stop_dashboard quiet
    fi
    listener=$(listener_pid)
    if [ -n "$listener" ]; then
        if is_this_dashboard_process "$listener"; then
            printf 'Taking over previous Herald Decoder Server (PID %s)…\n' "$listener"
            stop_process "$listener"; remove_dashboard_state
        elif [ "$takeover_option" = --takeover ]; then
            printf 'Taking over port %s from PID %s…\n' "$dashboard_port" "$listener"
            stop_process "$listener"; remove_dashboard_state
        else
            print_dashboard_card "UNAVAILABLE" "port $dashboard_port is owned by another process" "PID $listener" >&2
            printf 'Owner: %s\n' "$(process_command "$listener")" >&2
            printf 'Run ./run_server.sh start --takeover to replace it, or choose another port.\n' >&2
            return 1
        fi
    fi
    remove_dashboard_state
    nohup env HERALD_SERVER_LAUNCHED=1 HERALD_SERVER_PORT="$dashboard_port" \
        "$research_launcher" -m dashboard.server >>"$log_file" 2>&1 </dev/null &
    pid=$!
    printf '%s\n' "$pid" >"$pid_file"
    write_state "$pid"
    attempts=0
    while [ "$attempts" -lt 25 ]; do
        if dashboard_is_tracked; then print_dashboard_card "RUNNING" "current" "PID $pid"; return 0; fi
        if ! kill -0 "$pid" 2>/dev/null; then
            print_dashboard_card "FAILED" "server exited during startup" "PID $pid" >&2
            printf '\nLast 30 log lines:\n' >&2; tail -n 30 "$log_file" >&2 || true
            remove_dashboard_state; return 1
        fi
        attempts=$((attempts + 1)); sleep 0.2
    done
    print_dashboard_card "FAILED" "server did not bind to port $dashboard_port" "PID $pid" >&2
    printf '\nRun ./run_server.sh logs for details.\n' >&2; return 1
}
foreground_dashboard() {
    listener=$(listener_pid)
    if [ -n "$listener" ]; then
        if is_this_dashboard_process "$listener"; then
            printf 'Taking over previous Herald Decoder Server (PID %s)…\n' "$listener"
            stop_process "$listener"; remove_dashboard_state
        elif [ "$takeover_option" = --takeover ]; then
            printf 'Taking over port %s from PID %s…\n' "$dashboard_port" "$listener"
            stop_process "$listener"; remove_dashboard_state
        else
            print_dashboard_card "UNAVAILABLE" "port $dashboard_port is owned by another process" "PID $listener" >&2
            printf 'Owner: %s\n' "$(process_command "$listener")" >&2
            printf 'Run ./run_server.sh foreground --takeover to replace it, or choose another port.\n' >&2
            return 1
        fi
    fi
    remove_dashboard_state
    pid=$$
    printf '%s\n' "$pid" >"$pid_file"
    write_state "$pid"
    print_dashboard_card "RUNNING" "foreground · current" "PID $pid"
    exec env HERALD_SERVER_LAUNCHED=1 HERALD_SERVER_PORT="$dashboard_port" \
        "$research_launcher" -m dashboard.server
}
stop_dashboard() {
    quiet=${1:-}
    if service_is_loaded; then
        launchctl bootout "$service_domain/$service_label"
        remove_dashboard_state
        if [ "$quiet" != quiet ]; then print_dashboard_card "STOPPED" "persistent service stopped" "—"; fi
        return 0
    fi
    if ! dashboard_is_tracked; then
        listener=$(listener_pid)
        if [ -n "$listener" ]; then
            if is_this_dashboard_process "$listener" || [ "$takeover_option" = --takeover ]; then
                stop_process "$listener"; remove_dashboard_state
                if [ "$quiet" != quiet ]; then print_dashboard_card "STOPPED" "previous dashboard instance stopped" "—"; fi
                return 0
            fi
            print_dashboard_card "UNAVAILABLE" "port $dashboard_port is owned by another process" "PID $listener" >&2
            printf 'Owner: %s\n' "$(process_command "$listener")" >&2
            printf 'Run ./run_server.sh stop --takeover to stop it explicitly.\n' >&2; return 1
        fi
        remove_dashboard_state
        if [ "$quiet" != quiet ]; then print_dashboard_card "STOPPED" "not running" "—"; fi
        return 0
    fi
    pid=$(saved_pid); stop_process "$pid"; remove_dashboard_state
    if [ "$quiet" != quiet ]; then print_dashboard_card "STOPPED" "not running" "—"; fi
}
status_dashboard() {
    if service_is_loaded; then
        if project_api_identity; then print_dashboard_card "RUNNING" "launchd · persistent" "$service_label"; return 0; fi
        print_dashboard_card "STARTING" "launchd service is loaded" "$service_label"; return 1
    fi
    if dashboard_is_tracked; then
        if dashboard_is_current; then print_dashboard_card "RUNNING" "current" "PID $(saved_pid)"; return 0; fi
        print_dashboard_card "STALE" "changed — run ./run_server.sh start" "PID $(saved_pid)"; return 1
    fi
    listener=$(listener_pid)
    if [ -n "$listener" ]; then
        if is_this_dashboard_process "$listener"; then print_dashboard_card "STALE" "previous server instance — run start to take over" "PID $listener"
        else print_dashboard_card "UNAVAILABLE" "port $dashboard_port is owned by another process" "PID $listener"; printf 'Owner: %s\n' "$(process_command "$listener")"; fi
        return 1
    fi
    print_dashboard_card "STOPPED" "not running" "—"; return 1
}
case "$command" in
    start) start_dashboard ;;
    foreground) foreground_dashboard ;;
    stop) stop_dashboard ;;
    restart) stop_dashboard quiet; start_dashboard ;;
    status) status_dashboard ;;
    install-service) install_service ;;
    uninstall-service) uninstall_service ;;
    logs)
        if [ -f "$log_file" ]; then
            log_pid=$(saved_pid); [ -n "$log_pid" ] && log_pid="PID $log_pid" || log_pid='—'
            print_dashboard_card "LOGS" "last 100 lines" "$log_pid"; tail -n 100 "$log_file"
        else print_dashboard_card "NO LOG" "the dashboard has not been started on this port" "—"; fi
        ;;
    *) print_usage_card >&2; exit 2 ;;
esac
