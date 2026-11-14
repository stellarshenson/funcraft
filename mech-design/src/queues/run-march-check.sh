#!/bin/bash
# on GPU 1: four frames of the three front mechs with the march of the Atlas and the BattleMaster (src/procession/gait.py)
cd /home/lab/workspace/funcraft/mech-design
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1
/home/lab/.local/opt/blender-4.5.9-linux-x64/blender -b -P src/procession/scene.py -- livery=livery hips=4.5 out=frames-check tag=march 28 30 6 13 20
echo "=== check done $(date +%H:%M:%S)"
