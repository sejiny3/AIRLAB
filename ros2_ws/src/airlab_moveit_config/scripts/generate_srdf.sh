#!/bin/bash
# Regenerate config/airlab.srdf = config/airlab.srdf.base + self-collision matrix.
# Run from a sourced workspace: bash src/airlab_moveit_config/scripts/generate_srdf.sh [samples]
# (moveit_setup_assistant's collisions_updater hangs on this robot, so the matrix is
#  computed with MuJoCo by generate_collision_matrix.py.)
set -e
PKG_SRC="$(cd "$(dirname "$0")/.." && pwd)"
AIRLAB_ROOT="${AIRLAB_ROOT:-$(cd "$PKG_SRC/../../.." && pwd)}"
TMP="$(mktemp -d)"
xacro "$(ros2 pkg prefix airlab_description)/share/airlab_description/urdf/airlab.urdf.xacro" > "$TMP/airlab.urdf"
python3 "$PKG_SRC/scripts/generate_collision_matrix.py" "$TMP/airlab.urdf" "$AIRLAB_ROOT/models/scene.xml" \
  "$PKG_SRC/config/airlab.srdf.base" "$PKG_SRC/config/airlab.srdf" "${1:-3000}"
echo "wrote $PKG_SRC/config/airlab.srdf ($(grep -c disable_collisions "$PKG_SRC/config/airlab.srdf") disabled pairs)"
