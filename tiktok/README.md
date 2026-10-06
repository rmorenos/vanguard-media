# TikTok

TikTok version of the Instagram batch in `ig/`. Buffer publishes to the TikTok channel `vanguardgreensolutions` and fetches the files by their raw GitHub URL, same as Instagram.

## What maps to what

| Instagram | TikTok | Files |
| --- | --- | --- |
| Reels (9:16) | Videos, reused as is | `ig/reels/*.mp4` |
| Carousels (4:5) | Photo mode posts, re-framed to 9:16 | `tiktok/fotos/*.jpg` |
| Stories | Not used (no stories through Buffer on TikTok) | |

`tiktok/fotos` is generated from `ig/carruseles`: each slide is placed 200 px from the top of a 1080x1920 canvas and the top row and footer are stretched to fill, so the CTA bar sits above TikTok's caption overlay.

## Conventions

- Bilingual caption: hook in English first, then a 🇪🇸 line in Spanish.
- CTA: "Text CLEAN / Escribe LIMPIO al 502-424-4495". No links (TikTok captions do not link).
- 4 to 5 hashtags: `#louisville #louisvilleky #502` plus one or two topic tags (`#trashcancleaning`, `#pressurewashing`, `#cleantok`).
- Post at 7:00 pm ET, on days with no Instagram post at the same hour.

## Calendar (America/New_York)

| Date | Type | Asset | Hook |
| --- | --- | --- | --- |
| Thu Oct 8, 7:00 pm | Video | `ig/reels/r01-cubos-25.mp4` | Your trash bin is dirtier than you think |
| Sun Oct 11, 7:00 pm | Video | `ig/reels/r02-driveway-100.mp4` | How much to pressure wash a driveway in Louisville? |
| Wed Oct 14, 7:00 pm | Video | `ig/reels/r03-moscas.mp4` | Why flies love your trash bin |
| Fri Oct 16, 7:00 pm | Photos | `tiktok/fotos/01-*` | 2 bins. Every pickup. $25 |
| Mon Oct 19, 7:00 pm | Photos | `tiktok/fotos/02-*` | Your quote in 3 steps, no forms |
| Thu Oct 22, 7:00 pm | Photos | `tiktok/fotos/03-*` | Driveways from $100. What changes the price? |
| Mon Oct 26, 7:00 pm | Photos | `tiktok/fotos/04-*` | Bring a neighbor, you both win |
| Thu Oct 29, 7:00 pm | Photos | `tiktok/fotos/05-*` | Why your bins attract flies |

## New reels

`tools/reel.py` builds a 9:16 reel with no people: branded cards, a synthetic voiceover (Kokoro TTS, English scenes and a Spanish closing line) and the "Text CLEAN" end card. Write a spec in `tiktok/specs/`, render it to `tiktok/videos/`, and set `isAiGenerated` on the Buffer post.

```
python3 -m pip install kokoro-onnx soundfile
# model files from github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0 into /tmp/claude-0/tts
python3 tools/reel.py tiktok/specs/t01-hojas-otono.json tiktok/videos/t01-hojas-otono.mp4
```
