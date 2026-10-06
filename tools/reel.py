"""Make a 9:16 branded reel with synthetic voiceover and no people.

Usage: python3 tools/reel.py spec.json out.mp4

spec.json:
{
  "tag": "LOUISVILLE · TRASH BIN PLAN",
  "scenes": [
    {"title": "Your bin is dirtier\nthan you think", "sub": "Tu cubo está más sucio\nde lo que crees",
     "say": "Your trash bin is dirtier than you think.", "lang": "en"},
    {"big": "$25", "title": "per visit", "sub": "por visita", "say": "...", "lang": "en"}
  ]
}
Each scene lasts as long as its voiceover plus a short pause. A closing card with the
"Text CLEAN / Escribe LIMPIO" call to action and a Spanish voice line is always appended.

Needs: ffmpeg, Pillow, kokoro-onnx, soundfile, and the Kokoro model files in $KOKORO_DIR
(default /tmp/claude-0/tts): kokoro-v1.0.onnx and voices-v1.0.bin from the
thewh1teagle/kokoro-onnx release model-files-v1.0.
"""
import json, os, subprocess, sys, tempfile

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
GREEN, DARK, LIME, ORANGE, WHITE = (21, 63, 41), (10, 32, 20), (139, 195, 74), (242, 140, 40), (255, 255, 255)
FONTS = "/usr/share/fonts/opentype/inter/"
HERE = os.path.dirname(os.path.abspath(__file__))
VOICES = {"en": ("af_heart", "en-us"), "es": ("ef_dora", "es")}
CTA_SAY = "Escribe LIMPIO al cinco cero dos, cuatro dos cuatro, cuatro cuatro nueve cinco."


def font(name, size):
    return ImageFont.truetype(FONTS + name, size)


def wrap_lines(text):
    return text.split("\n")


def card(scene, tag, closing=False):
    im = Image.new("RGB", (W, H), GREEN)
    d = ImageDraw.Draw(im)
    for y in range(H):  # vertical gradient to the footer colour
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(GREEN[i] * (1 - t) + DARK[i] * t) for i in range(3)))
    d.ellipse((760, -120, 1260, 380), fill=(31, 78, 50))
    d.ellipse((-160, 1250, 240, 1650), fill=(27, 72, 45))
    y = 420
    if tag:
        f = font("Inter-ExtraBold.otf", 40)
        tw = d.textlength(tag, font=f)
        d.rounded_rectangle((70, y, 70 + tw + 48, y + 72), 36, fill=LIME)
        d.text((94, y + 12), tag, font=f, fill=DARK)
        y += 150
    if scene.get("big"):
        f = font("Inter-Black.otf", 300)
        d.text((60, y), scene["big"], font=f, fill=ORANGE)
        y += 360
    f = font("Inter-ExtraBold.otf", 96 if not closing else 104)
    for line in wrap_lines(scene.get("title", "")):
        d.text((70, y), line, font=f, fill=WHITE)
        y += 116
    y += 30
    f = font("Inter-BoldItalic.otf", 62)
    for line in wrap_lines(scene.get("sub", "")):
        d.text((70, y), line, font=f, fill=LIME)
        y += 80
    # footer bar, kept above TikTok's caption overlay
    fy = 1440
    d.rectangle((0, fy, W, fy + 150), fill=DARK)
    logo = Image.open(os.path.join(HERE, "logo.png")).convert("RGBA")
    im.paste(logo, (40, fy + 23), logo)
    d.text((166, fy + 28), "Text CLEAN · 502-424-4495", font=font("Inter-ExtraBold.otf", 46), fill=WHITE)
    d.text((166, fy + 86), "Escribe LIMPIO · Louisville, KY", font=font("Inter-Bold.otf", 34), fill=LIME)
    return im


def main(spec_path, out):
    spec = json.load(open(spec_path))
    kdir = os.environ.get("KOKORO_DIR", "/tmp/claude-0/tts")
    tts = Kokoro(os.path.join(kdir, "kokoro-v1.0.onnx"), os.path.join(kdir, "voices-v1.0.bin"))
    scenes = list(spec["scenes"]) + [{
        "title": "Text CLEAN\n502-424-4495", "sub": "Escribe LIMPIO\nTe respondemos en 1 hora",
        "say": CTA_SAY, "lang": "es", "closing": True}]
    tmp = tempfile.mkdtemp()
    audio, segs, sr = [], [], 24000
    for i, s in enumerate(scenes):
        voice, lang = VOICES[s.get("lang", "en")]
        samples, sr = tts.create(s["say"], voice=voice, speed=1.05, lang=lang)
        pause = np.zeros(int(sr * 0.45), dtype=samples.dtype)
        clip = np.concatenate([samples, pause])
        audio.append(clip)
        img = os.path.join(tmp, f"s{i}.png")
        card(s, spec.get("tag", "") if i == 0 else "", s.get("closing", False)).save(img)
        segs.append((img, len(clip) / sr))
    wav = os.path.join(tmp, "vo.wav")
    sf.write(wav, np.concatenate(audio), sr)
    # one slow push-in per scene, joined with short crossfades
    parts, inputs = [], []
    for i, (img, dur) in enumerate(segs):
        inputs += ["-loop", "1", "-t", f"{dur + 0.3:.3f}", "-i", img]
        n = int((dur + 0.3) * FPS)
        parts.append(f"[{i}:v]scale=1188:2112,zoompan=z='1+0.06*on/{n}':x='iw/2-(iw/zoom/2)':"
                     f"y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS},setsar=1[v{i}]")
    chain, last, offset = [], "v0", 0.0
    for i in range(1, len(segs)):
        offset += segs[i - 1][1]
        chain.append(f"[{last}][v{i}]xfade=transition=fade:duration=0.3:offset={offset:.3f}[x{i}]")
        last = f"x{i}"
    graph = ";".join(parts + chain)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-i", wav, "-filter_complex", graph,
           "-map", f"[{last}]", "-map", f"{len(segs)}:a", "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "128k", "-shortest",
           "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
