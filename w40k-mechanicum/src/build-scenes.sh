#!/bin/bash
# Builds plate scenes one after another on one GPU and renders four test
# frames of each (0, 20, 40, 60), for a look before the full render.
#   src/build-scenes.sh <gpu index> <scene>...
cd "$(dirname "$0")/.."
gpu=$1
shift
for n in "$@"; do
  src/build-scene.sh $gpu $n > wip/logs/build-$n.log 2>&1
  CUDA_VISIBLE_DEVICES=$gpu ~/.local/opt/blender-4.5.9-linux-x64/blender -b -P src/scenes.py -- $n 0 20 40 60 > wip/logs/render-$n.log 2>&1
  echo "BUILT $n"
done
echo BUILDS_DONE
