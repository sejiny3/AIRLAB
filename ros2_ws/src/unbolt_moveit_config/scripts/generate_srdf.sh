#!/bin/bash
# Regenerate config/unbolt.srdf = config/unbolt.srdf.base + self-collision matrix.
# Run from a sourced workspace: bash src/unbolt_moveit_config/scripts/generate_srdf.sh [samples]
# (moveit_setup_assistant's collisions_updater hangs on this robot, so the matrix is
#  computed with MuJoCo by generate_collision_matrix.py.)
set -e
PKG_SRC="$(cd "$(dirname "$0")/.." && pwd)"
UNBOLT_ROOT="${UNBOLT_ROOT:-$(cd "$PKG_SRC/../../.." && pwd)}"
TMP="$(mktemp -d)"
xacro "$(ros2 pkg prefix unbolt_description)/share/unbolt_description/urdf/unbolt.urdf.xacro" > "$TMP/unbolt.urdf"
python3 "$PKG_SRC/scripts/generate_collision_matrix.py" "$TMP/unbolt.urdf" "$UNBOLT_ROOT/models/scene.xml" \
  "$PKG_SRC/config/unbolt.srdf.base" "$PKG_SRC/config/unbolt.srdf" "${1:-3000}"
echo "wrote $PKG_SRC/config/unbolt.srdf ($(grep -c disable_collisions "$PKG_SRC/config/unbolt.srdf") disabled pairs)"
