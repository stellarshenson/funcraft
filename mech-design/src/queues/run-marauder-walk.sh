#!/bin/bash
# on GPU 1, after the queue of run-marauder-walk-and-10.sh: the Marauder's walking loop again, with the final missile rack
cd /home/lab/workspace/funcraft/mech-design
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1
until grep -q "=== ALL DONE\|FAILED" wip/logs/procession-make-marauder-walk-10.log; do sleep 5; done
echo "=== walk start $(date +%H:%M:%S)"
/home/lab/.local/opt/blender-4.5.9-linux-x64/blender -b -P src/procession/scene.py -- livery=livery hips=3 cloth=1 solo=marauder out=frames-procession-marauder || { echo "=== walk FAILED"; exit 1; }
/opt/conda/bin/python3.14 src/assemble.py wip/frames-procession-marauder wip/preview/procession/marauder-walk.avif || { echo "=== walk FAILED"; exit 1; }
echo "=== WALK DONE $(date +%H:%M:%S)"
