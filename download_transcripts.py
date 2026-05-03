#!/usr/bin/env python3
"""Download YouTube transcripts from a playlist.

Usage:
    python download_transcripts.py <playlist_url> [output_dir]

Requires:
    pip install youtube-transcript-api yt-dlp
"""
import os
import sys
import subprocess
from youtube_transcript_api import YouTubeTranscriptApi


def get_playlist_videos(playlist_url):
    """Get video IDs and titles from a YouTube playlist."""
    result = subprocess.run(
        [
            "yt-dlp",
            "--flat-playlist",
            "--print", "%(id)s\t%(title)s\t%(duration)s",
            playlist_url,
        ],
        capture_output=True, text=True, timeout=120,
    )
    videos = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            vid_id = parts[0]
            title = parts[1]
            duration = parts[2] if len(parts) > 2 else "NA"
            videos.append((vid_id, title, duration))
    return videos


def download_transcript(api, vid_id, title, out_dir):
    """Download transcript for a single video."""
    safe = "".join(
        c if c.isalnum() or c in " -_" else ""
        for c in title
    )[:60]
    outfile = os.path.join(out_dir, f"{vid_id}_{safe}.txt")

    if os.path.exists(outfile):
        return "SKIP", outfile

    try:
        transcript = api.fetch(vid_id)
        text = "\n".join(s.text for s in transcript.snippets)
        with open(outfile, "w") as f:
            f.write(f"# {title}\n")
            f.write(f"# Video ID: {vid_id}\n\n")
            f.write(text)
        return "OK", outfile
    except Exception as e:
        err_type = type(e).__name__
        return "FAIL", f"[{err_type}] {e}"


def main():
    if len(sys.argv) < 2:
        print("Usage: python download_transcripts.py "
              "<playlist_url> [output_dir]")
        sys.exit(1)

    playlist_url = sys.argv[1]
    out_dir = (
        sys.argv[2] if len(sys.argv) > 2
        else "transcripts"
    )
    os.makedirs(out_dir, exist_ok=True)

    print(f"Fetching playlist: {playlist_url}")
    videos = get_playlist_videos(playlist_url)
    print(f"Found {len(videos)} videos.\n")

    api = YouTubeTranscriptApi()
    ok, fail, skip = 0, 0, 0

    for vid_id, title, duration in videos:
        status, detail = download_transcript(
            api, vid_id, title, out_dir
        )
        if status == "OK":
            ok += 1
            print(f"  OK: {title[:55]}")
        elif status == "SKIP":
            skip += 1
            print(f"  SKIP: {title[:55]}")
        else:
            fail += 1
            print(f"  FAIL: {title[:45]}\n        {detail}")

    print(f"\nDone: {ok} downloaded, {skip} skipped, "
          f"{fail} failed")


if __name__ == "__main__":
    main()
