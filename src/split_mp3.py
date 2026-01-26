import logging
from pydub import AudioSegment
from pydub.silence import split_on_silence, detect_silence
import statistics
import os
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, APIC, COMM

import common as cm


def copy_metadata(source_file, target_file, part_num=None):
    """Copy metadata tags from source MP3 to target MP3.
    
    If part_num is provided, appends " (Part X)" to the title.
    Preserves artist, album, date, and other ID3 tags.
    """
    try:
        # Try to read source tags using EasyID3 (simpler interface)
        try:
            source_tags = EasyID3(source_file)
        except Exception:
            # If EasyID3 fails, try regular ID3
            source_tags = ID3(source_file)
        
        # Create target tags
        target_tags = ID3()
        
        # Copy common tags
        if 'TIT2' in source_tags or 'title' in source_tags:
            title = source_tags.get('title', source_tags.get('TIT2', ['']))[0]
            if title and part_num is not None:
                title = f"{title} (Part {part_num})"
            if title:
                target_tags.add(TIT2(encoding=3, text=[title]))
        
        if 'TPE1' in source_tags or 'artist' in source_tags:
            artist = source_tags.get('artist', source_tags.get('TPE1', ['']))[0]
            if artist:
                target_tags.add(TPE1(encoding=3, text=[artist]))
        
        if 'TALB' in source_tags or 'album' in source_tags:
            album = source_tags.get('album', source_tags.get('TALB', ['']))[0]
            if album:
                target_tags.add(TALB(encoding=3, text=[album]))
        
        if 'TDRC' in source_tags or 'date' in source_tags:
            date = source_tags.get('date', source_tags.get('TDRC', ['']))[0]
            if date:
                target_tags.add(TDRC(encoding=3, text=[date]))
        
        # Save tags to target file
        target_tags.save(target_file, v2_version=3)
    except Exception as e:
        # Log error but don't fail the split operation
        logging.getLogger("split_mp3_cli").debug(f"Could not copy metadata: {e}")


def split_mp3_on_silence(mp3_path, out_dir, min_silence_len=1000, silence_thresh=None, 
                         keep_silence=500, silence_offset=-16, bitrate_kbps=192, 
                         vbr_quality=None, silence_padding_ms=3000, sc=None):
    """Split an MP3 by silence.

    - If `silence_thresh` is None, compute it relative to the file's overall dBFS using `silence_offset`.
    - `sc` is an optional scriptClass instance used for GUI logging; if None, logging is skipped.
    """
    if sc:
        cm.log("split_mp3_on_silence: creating AudioSegment from file...", sc)

    audio = AudioSegment.from_file(mp3_path)

    # If silence threshold not provided, make it relative to the audio's dBFS
    if silence_thresh is None:
        silence_thresh = audio.dBFS + silence_offset

    if sc:
        cm.log("split_mp3_on_silence: creating chunks...", sc)

    chunks = split_on_silence(
        audio,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh,
        keep_silence=keep_silence,
    )

    if sc:
        cm.log(f"split_mp3_on_silence: created {len(chunks)} chunks", sc)

    os.makedirs(out_dir, exist_ok=True)
    files = []
    base = os.path.splitext(os.path.basename(mp3_path))[0]
    for i, chunk in enumerate(chunks):
        # add silence padding to start and end to avoid abrupt cuts
        if silence_padding_ms and silence_padding_ms > 0:
            pad = AudioSegment.silent(duration=silence_padding_ms)
            chunk = pad + chunk + pad

        out_file = os.path.join(out_dir, f"{base}_part{i+1}.mp3")
        if sc:
            cm.log(f"split_mp3_on_silence: exporting {out_file}", sc)
        else:
            logging.getLogger("split_mp3_cli").info(f"split_mp3_on_silence: exporting {out_file}")
        export_kwargs = {}
        if vbr_quality is not None and str(vbr_quality).strip() != "":
            # use ffmpeg VBR quality flag
            export_kwargs['parameters'] = ['-q:a', str(vbr_quality)]
            if sc:
                cm.log(f"split_mp3_on_silence: using VBR quality={vbr_quality} for {out_file}", sc)
            else:
                logging.getLogger("split_mp3_cli").info(f"split_mp3_on_silence: using VBR quality={vbr_quality} for {out_file}")
        else:
            export_kwargs['bitrate'] = f"{bitrate_kbps}k"
            if sc:
                cm.log(f"split_mp3_on_silence: using bitrate={bitrate_kbps}k for {out_file}", sc)
            else:
                logging.getLogger("split_mp3_cli").info(f"split_mp3_on_silence: using bitrate={bitrate_kbps}k for {out_file}")

        chunk.export(out_file, format="mp3", **export_kwargs)
        # Copy metadata from source to target
        try:
            copy_metadata(mp3_path, out_file, part_num=i+1)
        except Exception as e:
            if sc:
                cm.log(f"split_mp3_on_silence: warning - could not copy metadata: {e}", sc)
        files.append(out_file)

    if sc:
        cm.log(f"split_mp3_on_silence: returning {len(files)} files", sc)
    return files


def split_mp3_by_time(mp3_path, out_dir, chunk_length_ms=60000, bitrate_kbps=192, 
                      vbr_quality=None, silence_padding_ms=3000, sc=None):
    """Split an MP3 into fixed-length chunks."""
    if sc:
        cm.log("split_mp3_by_time: creating AudioSegment from file...", sc)

    audio = AudioSegment.from_file(mp3_path)
    os.makedirs(out_dir, exist_ok=True)
    files = []
    base = os.path.splitext(os.path.basename(mp3_path))[0]
    for i, start in enumerate(range(0, len(audio), chunk_length_ms)):
        chunk = audio[start:start + chunk_length_ms]
        # add padding silence
        if silence_padding_ms and silence_padding_ms > 0:
            pad = AudioSegment.silent(duration=silence_padding_ms)
            chunk = pad + chunk + pad

        out_file = os.path.join(out_dir, f"{base}_part{i+1}.mp3")
        if sc:
            cm.log(f"split_mp3_by_time: exporting {out_file}", sc)
        export_kwargs = {}
        if vbr_quality is not None and str(vbr_quality).strip() != "":
            export_kwargs['parameters'] = ['-q:a', str(vbr_quality)]
            if sc:
                cm.log(f"split_mp3_by_time: using VBR quality={vbr_quality} for {out_file}", sc)
            else:
                logging.getLogger("split_mp3_cli").info(f"split_mp3_by_time: using VBR quality={vbr_quality} for {out_file}")
        else:
            export_kwargs['bitrate'] = f"{bitrate_kbps}k"
            if sc:
                cm.log(f"split_mp3_by_time: using bitrate={bitrate_kbps}k for {out_file}", sc)
            else:
                logging.getLogger("split_mp3_cli").info(f"split_mp3_by_time: using bitrate={bitrate_kbps}k for {out_file}")

        chunk.export(out_file, format="mp3", **export_kwargs)
        # Copy metadata from source to target
        try:
            copy_metadata(mp3_path, out_file, part_num=i+1)
        except Exception as e:
            if sc:
                cm.log(f"split_mp3_by_time: warning - could not copy metadata: {e}", sc)
        files.append(out_file)
    return files


def split_mp3_by_silence_intervals(mp3_path, out_dir, min_silence_len=1000, 
                                   silence_thresh=None, keep_silence=500, 
                                   silence_offset=-16, bitrate_kbps=192, 
                                   vbr_quality=None, silence_padding_ms=3000, 
                                   sc=None):
    """Split an MP3 into tracks by detecting long silence intervals between songs.

    Returns list of exported file paths. The function first detects silences using
    `detect_silence` and then exports audio segments between those silence ranges.
    """
    if sc:
        cm.log("split_mp3_by_silence_intervals: loading audio...", sc)

    audio = AudioSegment.from_file(mp3_path)

    if silence_thresh is None:
        silence_thresh = audio.dBFS + silence_offset

    if sc:
        cm.log("split_mp3_by_silence_intervals: detecting silence ranges...", sc)

    silences = detect_silence(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
    # detect_silence returns list of [start_ms, end_ms]
    if sc:
        cm.log(f"split_mp3_by_silence_intervals: found {len(silences)} silence ranges", sc)

    # Build segments between silences
    segments = []
    last_end = 0
    for start_s, end_s in silences:
        # segment is audio between last_end and start_s
        seg_start = max(0, last_end)
        seg_end = max(seg_start, start_s)
        if seg_end - seg_start > 0:
            # optionally include a little silence around the track
            seg_a = max(0, seg_start - keep_silence)
            seg_b = min(len(audio), seg_end + keep_silence)
            segments.append((seg_a, seg_b))
        last_end = end_s

    # final segment after last silence
    if last_end < len(audio):
        seg_start = last_end
        seg_end = len(audio)
        if seg_end - seg_start > 0:
            seg_a = max(0, seg_start - keep_silence)
            seg_b = min(len(audio), seg_end + keep_silence)
            segments.append((seg_a, seg_b))

    if sc:
        cm.log(f"split_mp3_by_silence_intervals: will create {len(segments)} segments", sc)

    os.makedirs(out_dir, exist_ok=True)
    files = []
    base = os.path.splitext(os.path.basename(mp3_path))[0]
    for i, (a, b) in enumerate(segments):
        chunk = audio[a:b]
        # add padding silence at start and end
        if silence_padding_ms and silence_padding_ms > 0:
            pad = AudioSegment.silent(duration=silence_padding_ms)
            chunk = pad + chunk + pad

        out_file = os.path.join(out_dir, f"{base}_part{i+1}.mp3")
        if sc:
            cm.log(f"split_mp3_by_silence_intervals: exporting {out_file}", sc)
        export_kwargs = {}
        if vbr_quality is not None and str(vbr_quality).strip() != "":
            export_kwargs['parameters'] = ['-q:a', str(vbr_quality)]
            if sc:
                cm.log(f"split_mp3_by_silence_intervals: using VBR quality={vbr_quality} for {out_file}", sc)
            else:
                logging.getLogger("split_mp3_cli").info(f"split_mp3_by_silence_intervals: using VBR quality={vbr_quality} for {out_file}")
        else:
            export_kwargs['bitrate'] = f"{bitrate_kbps}k"
            if sc:
                cm.log(f"split_mp3_by_silence_intervals: using bitrate={bitrate_kbps}k for {out_file}", sc)
            else:
                logging.getLogger("split_mp3_cli").info(f"split_mp3_by_silence_intervals: using bitrate={bitrate_kbps}k for {out_file}")

        chunk.export(out_file, format="mp3", **export_kwargs)
        # Copy metadata from source to target
        try:
            copy_metadata(mp3_path, out_file, part_num=i+1)
        except Exception as e:
            if sc:
                cm.log(f"split_mp3_by_silence_intervals: warning - could not copy metadata: {e}", sc)
        files.append(out_file)

    if sc:
        cm.log(f"split_mp3_by_silence_intervals: exported {len(files)} files", sc)
    return files


def analyze_silence(mp3_path, min_silence_search_ms=200, silence_offset=-16, sc=None):
    """Analyze silence durations in the file and suggest sensible split parameters.

    Returns a dict with keys: `audio_dBFS`, `suggested_silence_thresh`, `count_silences`,
    `median_silence_ms`, `p75_silence_ms`, and `suggested_min_silence_ms`.
    """
    if sc:
        cm.log("analyze_silence: loading audio...", sc)
    audio = AudioSegment.from_file(mp3_path)
    audio_dbfs = audio.dBFS

    suggested_silence_thresh = int(round(audio_dbfs + silence_offset))

    if sc:
        cm.log(f"analyze_silence: detecting silences (min_len={min_silence_search_ms} ms, thresh={suggested_silence_thresh} dBFS)...", sc)

    silences = detect_silence(audio, min_silence_len=min_silence_search_ms, silence_thresh=suggested_silence_thresh)
    durations = [end - start for start, end in silences]

    result = {
        "audio_dBFS": audio_dbfs,
        "suggested_silence_thresh": suggested_silence_thresh,
        "count_silences": len(durations),
        "durations_ms": durations,
    }

    if durations:
        median = int(statistics.median(durations))
        # 75th percentile via quantiles if available
        try:
            p75 = int(statistics.quantiles(durations, n=4)[2])
        except Exception:
            p75 = int(sorted(durations)[max(0, int(0.75 * len(durations)) - 1)])

        # Suggest a min silence length based on the distribution: use p75 but clamp
        suggested_min = max(300, min(5000, p75))
        result.update({
            "median_silence_ms": median,
            "p75_silence_ms": p75,
            "suggested_min_silence_ms": suggested_min,
        })
    else:
        result.update({
            "median_silence_ms": 0,
            "p75_silence_ms": 0,
            "suggested_min_silence_ms": 1000,
        })

    if sc:
        cm.log(f"analyze_silence: found {result['count_silences']} silences; suggested min_silence={result['suggested_min_silence_ms']} ms, suggested_thresh={result['suggested_silence_thresh']} dBFS", sc)

    return result
