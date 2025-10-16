#!/usr/bin/env python3
"""
Video Analysis and Cleanup Tool
Identifies low-quality or unwanted videos:
- Very short videos (< 3 seconds - likely accidental)
- Low resolution videos (< 720p)
- Old screen recordings
- Duplicate videos
- Very large videos (for review)
"""

import os
import json
from pathlib import Path
from datetime import datetime
import subprocess

BACKUP_DIR = Path("/Users/evanswanson/icloud-photo-backup")
REPORT_FILE = BACKUP_DIR / "video_cleanup_report.json"

# Configuration
MIN_DURATION = 3.0  # Videos shorter than this are flagged (seconds)
MIN_RESOLUTION = 720  # Videos with height < this are flagged (720p)
SCREEN_RECORDING_AGE_MONTHS = 3  # Screen recordings older than this flagged
LARGE_VIDEO_SIZE_MB = 100  # Videos larger than this flagged for review
DUPLICATE_SIZE_DIFF = 1024  # Files within this size difference checked for duplicates (bytes)

class VideoAnalyzer:
    def __init__(self):
        self.short_videos = []
        self.low_res_videos = []
        self.old_screen_recordings = []
        self.large_videos = []
        self.duplicate_videos = []
        self.errors = []
        self.total_scanned = 0
        self.total_video_size = 0

    def is_video_file(self, filepath):
        """Check if file is a video"""
        ext = filepath.suffix.lower()
        return ext in ['.mov', '.mp4', '.m4v', '.avi', '.mkv', '.wmv']

    def get_video_info(self, filepath):
        """Get video metadata using ffprobe"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(filepath)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                return json.loads(result.stdout)
            return None

        except subprocess.TimeoutExpired:
            self.errors.append(f"Timeout analyzing {filepath.name}")
            return None
        except FileNotFoundError:
            # ffprobe not installed
            return None
        except Exception as e:
            self.errors.append(f"Error analyzing {filepath.name}: {e}")
            return None

    def analyze_video(self, filepath):
        """Analyze a single video file"""
        file_size = filepath.stat().st_size
        file_size_mb = file_size / (1024 * 1024)

        info = self.get_video_info(filepath)

        if not info:
            # Fallback: just check file size and age
            return {
                'path': str(filepath),
                'size_mb': round(file_size_mb, 2),
                'duration': None,
                'resolution': None,
                'codec': None
            }

        # Extract metadata
        duration = float(info.get('format', {}).get('duration', 0))

        # Get video stream info
        video_stream = None
        for stream in info.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
                break

        if video_stream:
            width = video_stream.get('width', 0)
            height = video_stream.get('height', 0)
            codec = video_stream.get('codec_name', 'unknown')
        else:
            width = height = 0
            codec = 'unknown'

        return {
            'path': str(filepath),
            'size_mb': round(file_size_mb, 2),
            'duration': round(duration, 2) if duration else None,
            'resolution': f"{width}x{height}" if width and height else None,
            'height': height,
            'codec': codec
        }

    def is_screen_recording(self, filepath):
        """Detect if video is likely a screen recording"""
        filename_lower = filepath.name.lower()
        screen_recording_patterns = [
            'screen recording', 'screen_recording', 'screenrecording',
            'rp_', 'replay_'  # Common screen recorder prefixes
        ]

        return any(pattern in filename_lower for pattern in screen_recording_patterns)

    def get_file_age_months(self, filepath):
        """Get age of file in months"""
        mtime = filepath.stat().st_mtime
        file_date = datetime.fromtimestamp(mtime)
        age_days = (datetime.now() - file_date).days
        return age_days / 30

    def scan_videos(self):
        """Scan all videos in backup directory"""
        print(f"Scanning directory: {BACKUP_DIR}")
        print("This may take a while for large video files...")
        print()

        if not BACKUP_DIR.exists():
            print(f"❌ Backup directory not found: {BACKUP_DIR}")
            return

        video_files = list(BACKUP_DIR.rglob("*"))
        video_files = [f for f in video_files if f.is_file() and self.is_video_file(f)]

        total = len(video_files)
        print(f"Found {total} video files to analyze")
        print()

        # Check for ffprobe
        try:
            subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
            has_ffprobe = True
            print("✓ ffprobe detected - will analyze video metadata")
        except:
            has_ffprobe = False
            print("⚠️  ffprobe not found - analysis will be limited to file size and age")
            print("   Install ffmpeg to get detailed video analysis:")
            print("   brew install ffmpeg")
        print()

        # Track by size for duplicate detection
        size_map = {}

        for idx, filepath in enumerate(video_files, 1):
            self.total_scanned += 1
            file_size = filepath.stat().st_size
            self.total_video_size += file_size

            if idx % 10 == 0:
                print(f"Progress: {idx}/{total} ({idx*100//total}%)")

            try:
                # Get video info
                video_info = self.analyze_video(filepath) if has_ffprobe else {
                    'path': str(filepath),
                    'size_mb': round(file_size / (1024*1024), 2),
                    'duration': None,
                    'resolution': None,
                    'height': None,
                    'codec': None
                }

                # Check for short videos
                if video_info['duration'] and video_info['duration'] < MIN_DURATION:
                    self.short_videos.append(video_info)

                # Check for low resolution
                if video_info['height'] and video_info['height'] < MIN_RESOLUTION:
                    self.low_res_videos.append(video_info)

                # Check for old screen recordings
                if self.is_screen_recording(filepath):
                    age_months = self.get_file_age_months(filepath)
                    if age_months >= SCREEN_RECORDING_AGE_MONTHS:
                        video_info['age_months'] = round(age_months, 1)
                        self.old_screen_recordings.append(video_info)

                # Check for large videos
                if video_info['size_mb'] > LARGE_VIDEO_SIZE_MB:
                    self.large_videos.append(video_info)

                # Check for potential duplicates by size
                size_key = file_size // 1024  # Group by KB
                if size_key not in size_map:
                    size_map[size_key] = []
                size_map[size_key].append(video_info)

            except Exception as e:
                self.errors.append(f"Error processing {filepath.name}: {e}")
                continue

        # Find duplicates
        for size_group in size_map.values():
            if len(size_group) > 1:
                # Group with same approximate size
                for i, vid1 in enumerate(size_group):
                    for vid2 in size_group[i+1:]:
                        self.duplicate_videos.append({
                            'file1': vid1['path'],
                            'file2': vid2['path'],
                            'size_mb': vid1['size_mb']
                        })

        print(f"\n✓ Scan complete! Analyzed {self.total_scanned} videos")

    def generate_report(self):
        """Generate cleanup report"""
        total_size_gb = self.total_video_size / (1024**3)

        # Calculate potential space savings
        short_video_size = sum(v['size_mb'] for v in self.short_videos)
        low_res_size = sum(v['size_mb'] for v in self.low_res_videos)
        screen_rec_size = sum(v['size_mb'] for v in self.old_screen_recordings)

        report = {
            'scan_date': datetime.now().isoformat(),
            'total_scanned': self.total_scanned,
            'total_size_gb': round(total_size_gb, 2),
            'statistics': {
                'short_videos': len(self.short_videos),
                'low_res_videos': len(self.low_res_videos),
                'old_screen_recordings': len(self.old_screen_recordings),
                'large_videos': len(self.large_videos),
                'potential_duplicates': len(self.duplicate_videos)
            },
            'potential_savings_mb': round(short_video_size + low_res_size + screen_rec_size, 2),
            'short_videos': self.short_videos,
            'low_res_videos': self.low_res_videos,
            'old_screen_recordings': self.old_screen_recordings,
            'large_videos': self.large_videos,
            'duplicate_videos': self.duplicate_videos,
            'errors': self.errors
        }

        # Save report
        with open(REPORT_FILE, 'w') as f:
            json.dump(report, f, indent=2)

        print("\n" + "=" * 60)
        print("VIDEO CLEANUP REPORT")
        print("=" * 60)
        print(f"Total videos scanned: {self.total_scanned}")
        print(f"Total video size: {round(total_size_gb, 2)} GB")
        print()
        print(f"⏱️  Short videos (< {MIN_DURATION}s): {len(self.short_videos)}")
        print(f"   Space: {round(short_video_size, 2)} MB")
        print()
        print(f"📺 Low resolution (< {MIN_RESOLUTION}p): {len(self.low_res_videos)}")
        print(f"   Space: {round(low_res_size, 2)} MB")
        print()
        print(f"📱 Old screen recordings (> {SCREEN_RECORDING_AGE_MONTHS} months): {len(self.old_screen_recordings)}")
        print(f"   Space: {round(screen_rec_size, 2)} MB")
        print()
        print(f"💾 Large videos (> {LARGE_VIDEO_SIZE_MB} MB): {len(self.large_videos)}")
        total_large = sum(v['size_mb'] for v in self.large_videos)
        print(f"   Total size: {round(total_large, 2)} MB ({round(total_large/1024, 2)} GB)")
        print()
        print(f"📑 Potential duplicate pairs: {len(self.duplicate_videos)}")
        print()
        print(f"💰 Potential space savings: {round(short_video_size + low_res_size + screen_rec_size, 2)} MB")
        print()
        print(f"⚠️  Errors encountered: {len(self.errors)}")
        print()
        print(f"Report saved to: {REPORT_FILE}")
        print()

        if len(self.short_videos) > 0 or len(self.low_res_videos) > 0 or len(self.old_screen_recordings) > 0:
            print("To review and delete these videos, run:")
            print(f"  python3 ~/scripts/icloud-photo-backup/video_cleanup_review.py")
        else:
            print("✓ No problematic videos found!")

def main():
    print("=" * 60)
    print("Video Library Cleanup Tool")
    print("=" * 60)
    print()
    print("This tool will scan your video library for:")
    print(f"  - Short videos (< {MIN_DURATION} seconds - likely accidental)")
    print(f"  - Low resolution videos (< {MIN_RESOLUTION}p)")
    print(f"  - Old screen recordings (> {SCREEN_RECORDING_AGE_MONTHS} months)")
    print(f"  - Large videos (> {LARGE_VIDEO_SIZE_MB} MB - for review)")
    print(f"  - Potential duplicate videos")
    print()

    analyzer = VideoAnalyzer()
    analyzer.scan_videos()
    analyzer.generate_report()

if __name__ == "__main__":
    main()
