#!/bin/bash
# Waits until a log file holds a marker, then runs a command. For queueing
# work behind a running GPU queue without stopping it.
#   src/after.sh <log file> <marker> <command> [args...]
cd "$(dirname "$0")/.."
log=$1 marker=$2
shift 2
until grep -q "$marker" "$log" 2>/dev/null; do sleep 10; done
exec "$@"
