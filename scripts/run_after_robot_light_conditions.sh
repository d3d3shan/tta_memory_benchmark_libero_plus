#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OPENTAU_DIR="${OPENTAU_DIR:-$ROOT/OpenTau}"
cd "$OPENTAU_DIR"

LOG="note4/after_robot_light_conditions.log"
mkdir -p note4

printf '[%s] Waiting for robot_initial queue to finish\n' "$(date '+%F %T')" | tee -a "$LOG"
while ps -ef | grep -F 'run_robot_initial_queue.sh' | grep -v grep >/dev/null; do
  sleep 300
done

printf '[%s] robot_initial queue no longer running; starting light_conditions\n' "$(date '+%F %T')" | tee -a "$LOG"
exec "$SCRIPT_DIR/run_light_conditions_queue.sh"
