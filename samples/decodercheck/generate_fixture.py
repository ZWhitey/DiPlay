"""Generate a public synthetic AVC fixture; no user video or credentials needed."""
import json
from pathlib import Path
import subprocess

path = Path(__file__).parent / 'src/main/assets/pattern.mp4'
path.parent.mkdir(parents=True, exist_ok=True)
subprocess.run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-f', 'lavfi', '-i',
    'testsrc2=size=800x480:rate=30', '-t', '3.2', '-an', '-c:v', 'libx264', '-profile:v', 'baseline',
    '-level', '3.1', '-pix_fmt', 'yuv420p', '-bf', '0', '-g', '30', '-preset', 'ultrafast',
    '-movflags', '+faststart', str(path)], check=True)
metadata = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(path)]))
stream = metadata['streams'][0]
assert stream['codec_name'] == 'h264' and stream['width'] == 800 and stream['height'] == 480
assert int(stream['nb_frames']) == 96
print('Generated 90-core + 6-tail frame 800x480 AVC baseline test pattern')
