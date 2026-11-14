#!/bin/bash
# on GPU 1, with the two walks of src/procession/gait.py (march and bird): the Marauder's walking loop, banner 09, banner 08
cd /home/lab/workspace/funcraft/mech-design
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1
B=/home/lab/.local/opt/blender-4.5.9-linux-x64/blender
echo "=== walk start $(date +%H:%M:%S)"
rm -rf wip/frames-procession-marauder
$B -b -P src/procession/scene.py -- livery=livery hips=4.5 cloth=1 solo=marauder out=frames-procession-marauder || { echo "=== walk FAILED"; exit 1; }
/opt/conda/bin/python3.14 src/assemble.py wip/frames-procession-marauder wip/preview/procession/marauder-walk.avif || { echo "=== walk FAILED"; exit 1; }
echo "=== walk done $(date +%H:%M:%S)"
make procession-column || { echo "=== procession-column FAILED"; exit 1; }
echo "=== procession-column done $(date +%H:%M:%S)"
make procession-hips || { echo "=== procession-hips FAILED"; exit 1; }
echo "=== procession-hips done $(date +%H:%M:%S)"
echo "=== ALL DONE $(date +%H:%M:%S)"
