cd /home/lab/workspace/private/funcraft/w40k-mechanicum
CUDA_VISIBLE_DEVICES=1 LOOP_FRAMES=120 LOOP_WIDTH=2432 ~/.local/opt/blender-4.5.9-linux-x64/blender -b -P src/scenes.py -- saint > wip/logs/saint-candles-full.log 2>&1
echo FULL_DONE >> wip/logs/saint-candles-full.log
python3 src/muster.py assemble wip/frames-saint wip/preview/saint-titan.avif >> wip/logs/saint-candles-full.log 2>&1
python3 src/muster/flicker.py wip/frames-saint > wip/logs/saint-candles-flicker.log 2>&1
echo ALL_DONE >> wip/logs/saint-candles-full.log
