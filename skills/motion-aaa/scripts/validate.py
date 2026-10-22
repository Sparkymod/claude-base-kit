"""Validate delivered motion files ON THE FILE ITSELF (motion-aaa skill).

    python validate.py path/to/piece-v1.mp4 [more.mp4 | anim.gif ...]

For each file: full decode (0 errors), probe (size, fps, duration), loudness and true peak for files with audio
(|LUFS + 16| <= 0.5, true peak <= -1.5 dBTP), 12 frames (< 60 s) or 24 frames extracted from the file into
<folder>/qa/<stem>/ and a contact sheet <folder>/qa-<stem>-contacto.png that the model must open and inspect.
Writes <folder>/validacion-<stem>.json and exits 1 if any file fails.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import motion_core as mc  # noqa: E402


def probe(path: Path):
    out = json.loads(subprocess.check_output(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=codec_type,codec_name,width,height,r_frame_rate',
         '-of', 'json', str(path)], text=True))
    v = next(s for s in out['streams'] if s['codec_type'] == 'video')
    num, den = v['r_frame_rate'].split('/')
    return {'duration': float(out['format']['duration']), 'width': v['width'], 'height': v['height'],
            'fps': round(int(num) / int(den), 3), 'video_codec': v['codec_name'],
            'has_audio': any(s['codec_type'] == 'audio' for s in out['streams'])}


def validate(path: Path, lufs_target=-16.0, lufs_tol=.5, peak_max=-1.5):
    path = Path(path)
    dec = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'null', '-'], capture_output=True, text=True)
    errors = [ln for ln in dec.stderr.splitlines() if ln.strip()]
    info = probe(path)
    res = {'file': path.name, 'decode_errors': len(errors), 'decode_error_sample': errors[:3], **info}
    ok = not errors
    if info['has_audio']:
        import audio_core as au
        lufs, peak = au.loudness_report(path)
        res.update({'lufs': lufs, 'true_peak_dbtp': peak})
        ok = ok and abs(lufs - lufs_target) <= lufs_tol and peak <= peak_max
    dur = info['duration']
    n = 12 if dur < 60 else 24
    times = [round(dur * (i + .5) / n, 2) for i in range(n)]
    out = path.parent / 'qa' / path.stem
    out.mkdir(parents=True, exist_ok=True)
    frames = []
    for t in times:
        f = out / f'file-{t:07.2f}.png'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', str(path), '-frames:v', '1', str(f)],
                       check=True)
        frames.append(f)
    sheet = mc.contact_sheet(frames, path.parent / f'qa-{path.stem}-contacto.png')
    res.update({'frames_from_file': len(frames), 'contact_sheet': sheet.name, 'ok': ok,
                'note': 'open the contact sheet and inspect it; record what was and was not inspected'})
    (path.parent / f'validacion-{path.stem}.json').write_text(json.dumps(res, indent=2, ensure_ascii=False),
                                                              encoding='utf-8')
    print(json.dumps(res, ensure_ascii=False))
    return res


if __name__ == '__main__':
    bad = [p for p in sys.argv[1:] if not validate(Path(p))['ok']]
    sys.exit(1 if bad or len(sys.argv) < 2 else 0)
