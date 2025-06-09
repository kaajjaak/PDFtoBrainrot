# PDF to TikTok Video Converter

A Python tool that converts educational PDFs into TikTok-style videos with voiceover and background gameplay footage.

## Work in Progress

This project is currently under development. The following features/fixes are still pending:

- [ ] Opening title card animation and voiceover
- [ ] Text and font styling improvements
- [ ] Requirements.txt file needs to be created
- [ ] Windows-specific dependencies need to be made cross-platform compatible

## Installation guide:

1. Run `pip install -r requirements.txt` in the console
2. Download and install ImageMagick at https://imagemagick.org/script/download.php
3. Put a mp4 of a long enough video in `preparation/downloads`
4. Run `preparation/edit_videos.py`
5. Put PDF(s) in the `input` folder
6. Rename `.env.template` to `.env` and fill in the values
7. Run `main.py`

## Basic Usage

1. Place PDF files in the `input` folder
2. Run the main script
3. Find processed videos in the `output` folder

## Directory Structure
```
project/
├── input/          # Place PDF files here
├── output/         # Final videos
├── scripts/        # Generated scripts
├── audio/          # Generated audio and subtitles
├── videos/         # Background videos
└── prompts/        # Script generation prompts
```
