#!/bin/bash
# Renders plate scenes one after another on one GPU and assembles each GIF.
#   src/render-scenes.sh <gpu index> <first GIF number> <scene>...
cd "$(dirname "$0")/.."
gpu=$1 k=$2
shift 2
for n in "$@"; do
  rm -rf wip/frames-$n
  CUDA_VISIBLE_DEVICES=$gpu ~/.local/opt/blender-4.5.9-linux-x64/blender -b -P src/scenes.py -- $n > wip/logs/render-$n.log 2>&1
  python3 src/assemble.py wip/frames-$n out/$(printf %02d $k)-$n.gif
  k=$((k+1))
done
echo SCENES_DONE
