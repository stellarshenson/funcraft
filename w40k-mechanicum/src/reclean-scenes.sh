#!/bin/bash
# The clean plate's geometry again (flames out, depth), with the paint kept,
# then four test frames, for scenes one after another on one GPU.
#   src/reclean-scenes.sh <gpu index> <scene>...
cd "$(dirname "$0")/.."
gpu=$1
shift
for n in "$@"; do
  CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=$gpu .venv-moge/bin/python src/cleanplate.py $n depth > wip/logs/reclean-$n.log 2>&1
  CUDA_VISIBLE_DEVICES=$gpu ~/.local/opt/blender-4.5.9-linux-x64/blender -b -P src/scenes.py -- $n 0 20 40 60 > wip/logs/render-$n.log 2>&1
  echo "RECLEANED $n"
done
echo RECLEAN_DONE
