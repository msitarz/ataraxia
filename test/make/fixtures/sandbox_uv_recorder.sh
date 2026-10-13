#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
set -eu
[ "$1" = "run" ]
shift
[ "$1" = "--no-sync" ]
shift
[ "$1" = "python" ]
shift
exec "$UV_TEST_PYTHON" "$@"
