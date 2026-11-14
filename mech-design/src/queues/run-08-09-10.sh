#!/bin/bash
# banners 08, 09, 10 one after the other on GPU 1, then the welcome page (which embeds banner 09)
cd /home/lab/workspace/funcraft/mech-design
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1
for target in procession-hips procession-column welcome procession-marauder; do
    echo "=== $target start $(date +%H:%M:%S)"
    make $target || { echo "=== $target FAILED"; exit 1; }
    echo "=== $target done $(date +%H:%M:%S)"
done
echo "=== ALL DONE $(date +%H:%M:%S)"
