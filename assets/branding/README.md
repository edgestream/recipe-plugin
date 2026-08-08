# Recipe Plugin icon

The marketplace icon combines a recipe scroll with a mushroom, leaf, and
watermelon wedge on a dark charcoal tile. It is intentionally free of text and
facial features so it remains legible in compact plugin-directory views.

## Files

- `recipe-plugin-icon.png` — 1024×1024 RGBA PNG master and plugin-directory logo.
- `exports/recipe-plugin-icon-512.png` — common large marketplace export.
- `exports/recipe-plugin-icon-256.png` — ChatGPT/Codex composer icon.
- `exports/recipe-plugin-icon-128.png` — compact marketplace export.
- `exports/recipe-plugin-icon-64.png` — small UI export.
- `exports/recipe-plugin-icon-48.png` — minimum-size validation and fallback export.

All files are square, use lossless PNG compression, have transparent outer
corners, and stay below the 5 MiB plugin submission limit.

## OpenAI requirements

OpenAI's [plugin submission image requirements](https://developers.openai.com/plugins/deploy/submission-errors#image-errors)
require both `interface.logo` and `interface.composerIcon` to reference square
images. Supported filenames end in `.png`, `.jpg`, `.jpeg`, `.webp`, or `.svg`.
Raster images must be between 48×48 and 4096×4096 pixels and no image may exceed
5 MiB.

The Codex manifest uses the 1024 px master for `logo` and `logoDark`, and the
256 px export for `composerIcon`.

## Generation brief

Generated with the built-in OpenAI image generation tool from two visual
references: the ChatGPT dark plugin-directory context and an ingredient-plus-
recipe-scroll composition. The final brief specified an original, flat,
vector-like mark; a charcoal rounded-square tile; cream parchment; orange,
sage-green, and coral ingredients; bold rounded near-black outlines; no text;
and no face, smiley, chef hat, cutlery, watermark, photorealism, or 3D effects.
