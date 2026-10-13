#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
set -eu
for argument do
  if [ "$argument" = "clone" ] && [ "${SANDBOX_GIT_FAIL:-}" = "clone" ]; then
    printf '%s\n' 'simulated clone failure' >&2
    exit 23
  fi
done
for argument do
  if [ "$argument" = "clone" ] && [ -n "${SANDBOX_ADVANCE_SOURCE:-}" ]; then
    printf '%s\n' 'advanced after base selection' > "$SANDBOX_ADVANCE_SOURCE/.advanced"
    "$REAL_GIT_PATH" -C "$SANDBOX_ADVANCE_SOURCE" add .advanced
    "$REAL_GIT_PATH" -C "$SANDBOX_ADVANCE_SOURCE" \
      -c user.name=Fixture \
      -c user.email=fixture@example.com \
      -c commit.gpgsign=false \
      commit -m 'advance master after selection'
  fi
done
exec "$REAL_GIT_PATH" "$@"
