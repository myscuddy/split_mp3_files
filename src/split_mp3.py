from pydub import AudioSegment
from pydub.silence import split_on_silence
import os

import common as cm

def split_mp3_on_silence(sc:cm.scriptClass, mp3_path, out_dir, min_silence_len=1000, silence_thresh=-40, keep_silence=500):
    cm.log("split_mp3_on_silence::    , creating audio from AudioSegment as mp3 ...", sc)
    audio = AudioSegment.from_mp3(mp3_path)
    cm.log("split_mp3_on_silence::      creating chunks ...", sc)
    chunks = split_on_silence(
        audio,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh,
        keep_silence=keep_silence
    )
    cm.log(f"split_mp3_on_silence::        created [{len(chunks)}] chunks ...", sc)
    cm.log(f"split_mp3_on_silence::      creating [{out_dir}] folder if it does not exist ...", sc)
    os.makedirs(out_dir, exist_ok=True)
    files = []
    for i, chunk in enumerate(chunks):
        out_file = os.path.join(out_dir, f"{os.path.splitext(os.path.basename(mp3_path))[0]}_part{i+1}.mp3")
        cm.log(f"split_mp3_on_silence::          creating [{out_file}] ...", sc)
        chunk.export(out_file, format="mp3")
        files.append(out_file)

    cm.log(f"split_mp3_on_silence::    returning after creating [{len(files)}] files ...", sc)
    return files

def split_mp3_by_time(mp3_path, out_dir, chunk_length_ms=60000):
    audio = AudioSegment.from_mp3(mp3_path)
    os.makedirs(out_dir, exist_ok=True)
    files = []
    for i, start in enumerate(range(0, len(audio), chunk_length_ms)):
        chunk = audio[start:start+chunk_length_ms]
        out_file = os.path.join(out_dir, f"{os.path.splitext(os.path.basename(mp3_path))[0]}_part{i+1}.mp3")
        chunk.export(out_file, format="mp3")
        files.append(out_file)
    return files
