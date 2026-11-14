#!/bin/bash
# the Marauder's stills on GPU 2: full view with the cloth banner, then the close view
cd /home/lab/workspace/funcraft/mech-design
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=2
B=/home/lab/.local/opt/blender-4.5.9-linux-x64/blender
$B -b -P src/procession/livery.py -- marauder full cloth > wip/logs/procession-livery-marauder-full-cloth.log 2>&1
$B -b -P src/procession/livery.py -- marauder full > wip/logs/procession-livery-marauder-full.log 2>&1
$B -b -P src/procession/livery.py -- marauder close > wip/logs/procession-livery-marauder-close.log 2>&1
$B -b -P src/procession/livery.py -- madcat full cloth > wip/logs/procession-livery-madcat-full-cloth.log 2>&1
echo "=== STILLS DONE $(date +%H:%M:%S)"
