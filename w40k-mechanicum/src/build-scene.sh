#!/bin/bash
# Builds everything a plate scene needs before rendering, in order:
# masks, plate without painted smoke, flames, clean plate, actors, molten
# flow, smoke sources, smoke simulation, motion map.
#   src/build-scene.sh <gpu index> <scene> [clean-plate seed]     # default seed: motion.CLEAN_SEED
cd "$(dirname "$0")/.."
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=$1
n=$2
seed=${3:-$(python3 -c "import sys; sys.path.insert(0, 'src'); import motion; print(motion.CLEAN_SEED.get('$2', 1))")}
py=.venv-moge/bin/python
blender=~/.local/opt/blender-4.5.9-linux-x64/blender
set -e
$py src/segment.py cut $n
$py src/cleanplate.py $n desmoke
$py src/segment.py flames $n
$py src/cleanplate.py $n $seed
python3 src/actors.py $n
python3 src/motion.py flow $n
$blender -b -P src/scenes.py -- $n sources
$py src/smoke.py $n
python3 src/motion.py map $n
python3 src/motion.py plan $n
echo BUILD_DONE $n
