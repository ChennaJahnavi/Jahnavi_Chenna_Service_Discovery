#!/usr/bin/env bash
set -euo pipefail

for i in {1..10}; do
  json="$(
    curl -sS --fail \
      --retry 15 --retry-connrefused --retry-delay 1 \
      "http://localhost:9000/call?service=echo-service&path=/hello"
  )"
  chosen="$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["chosen_instance_id"])' <<<"$json")"
  printf "%02d -> %s\n" "$i" "$chosen"
  sleep 0.3
done
