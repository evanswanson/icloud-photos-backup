#!/usr/bin/env python3
"""
Aggressive Video Cleanup Tool
- Remove large videos (>100MB) older than 2 years
- Remove short videos (<5 sec) older than 1 year
- Shows preview before moving to trash
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

BACKUP_DIR = Path("/Users/evanswanson/icloud-photo-backup")
REPORT_FILE = BACKUP_DIR / "video_cleanup_aggressive_report.json"

# Aggressive thresholds
LARGE_VIDEO_SIZE_MB = 100  # Videos larger than this
LARGE_VIDEO_AGE_YEARS = 2  # Delete large videos older than this

SHORT_VIDEO_DURATION = 5.0  # Videos shorter than this (seconds)
SHORT_VIDEO_AGE_YEARS = 1  # Delete short videos older than this

class AggressiveVideoAnalyzer:
    def __init__(self):
        self.old_large_videos = []
        self.old_short_videos = []
        self.errors = []
        self.total_scanned = 0
        self.total_video_size_gb = 0

    def is_video_file(self, filepath):
        """Check if file is a video"""
        ext = filepath.suffix.lower()
        return ext in ['.mov', '.mp4', '.m4v', '.avi', '.mkv', '.wmv']

    def get_file_age_years(self, filepath):
        """Get age of file in years based on file modification time"""
        mtime = filepath.stat().st_mtime
        file_date = datetime.fromtimestamp(mtime)
        age_days = (datetime.now() - file_date).days
        return age_days / 365.25

    def get_video_duration(self, filepath):
        """Get video duration using ffprobe"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                str(filepath)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                data = json.loads(result.stdout)
                return float(data.get('format', {}).get('duration', 0))
            return None

        except:
            return None

    def scan_videos(self):
        """Scan all videos and identify candidates for deletion"""
        print(f"Scanning directory: {BACKUP_DIR}")
        print("Looking for:")
        print(f"  - Large videos (>{LARGE_VIDEO_SIZE_MB}MB) older than {LARGE_VIDEO_AGE_YEARS} years")
        print(f"  - Short videos (<{SHORT_VIDEO_DURATION}s) older than {SHORT_VIDEO_AGE_YEARS} year")
        print()

        if not BACKUP_DIR.exists():
            print(f"❌ Backup directory not found: {BACKUP_DIR}")
            return

        # Find all video files
        video_files = []
        for root, dirs, files in os.walk(BACKUP_DIR):
            # Skip trash
            if 'trash' in root or 'logs-archive' in root:
                continue
            for file in files:
                filepath = Path(root) / file
                if self.is_video_file(filepath):
                    video_files.append(filepath)

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
            print("⚠️  ffprobe not found - will only use file size/age")
            print("   Install ffmpeg to analyze video duration:")
            print("   brew install ffmpeg")
        print()

        for idx, filepath in enumerate(video_files, 1):
            self.total_scanned += 1
            file_size = filepath.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            self.total_video_size_gb += file_size / (1024**3)

            if idx % 100 == 0:
                print(f"Progress: {idx}/{total} ({idx*100//total}%)")

            try:
                age_years = self.get_file_age_years(filepath)

                # Check for old large videos
                if file_size_mb > LARGE_VIDEO_SIZE_MB and age_years >= LARGE_VIDEO_AGE_YEARS:
                    video_info = {
                        'path': str(filepath),
                        'size_mb': round(file_size_mb, 2),
                        'age_years': round(age_years, 2),
                        'duration': None
                    }

                    # Try to get duration if ffprobe available
                    if has_ffprobe:
                        duration = self.get_video_duration(filepath)
                        if duration:
                            video_info['duration'] = round(duration, 2)

                    self.old_large_videos.append(video_info)

                # Check for old short videos (requires duration)
                if has_ffprobe and age_years >= SHORT_VIDEO_AGE_YEARS:
                    duration = self.get_video_duration(filepath)
                    if duration and duration < SHORT_VIDEO_DURATION:
                        video_info = {
                            'path': str(filepath),
                            'size_mb': round(file_size_mb, 2),
                            'age_years': round(age_years, 2),
                            'duration': round(duration, 2)
                        }
                        self.old_short_videos.append(video_info)

            except Exception as e:
                self.errors.append(f"Error processing {filepath.name}: {str(e)}")
                continue

        print(f"\n✓ Scan complete! Analyzed {self.total_scanned} videos")

    def generate_report(self):
        """Generate cleanup report"""
        large_video_size = sum(v['size_mb'] for v in self.old_large_videos)
        short_video_size = sum(v['size_mb'] for v in self.old_short_videos)
        total_savings_mb = large_video_size + short_video_size

        report = {
            'scan_date': datetime.now().isoformat(),
            'total_scanned': self.total_scanned,
            'total_size_gb': round(self.total_video_size_gb, 2),
            'criteria': {
                'large_video_size_mb': LARGE_VIDEO_SIZE_MB,
                'large_video_age_years': LARGE_VIDEO_AGE_YEARS,
                'short_video_duration': SHORT_VIDEO_DURATION,
                'short_video_age_years': SHORT_VIDEO_AGE_YEARS
            },
            'statistics': {
                'old_large_videos': len(self.old_large_videos),
                'old_short_videos': len(self.old_short_videos),
                'total_candidates': len(self.old_large_videos) + len(self.old_short_videos),
                'potential_savings_mb': round(total_savings_mb, 2),
                'potential_savings_gb': round(total_savings_mb / 1024, 2)
            },
            'old_large_videos': sorted(self.old_large_videos, key=lambda x: x['size_mb'], reverse=True),
            'old_short_videos': self.old_short_videos,
            'errors': self.errors
        }

        # Save report
        with open(REPORT_FILE, 'w') as f:
            json.dump(report, f, indent=2)

        print("\n" + "=" * 70)
        print("AGGRESSIVE VIDEO CLEANUP REPORT")
        print("=" * 70)
        print(f"Total videos scanned: {self.total_scanned}")
        print(f"Total video size: {round(self.total_video_size_gb, 2)} GB")
        print()
        print(f"📺 Old large videos (>{LARGE_VIDEO_SIZE_MB}MB, >{LARGE_VIDEO_AGE_YEARS}yr): {len(self.old_large_videos)}")
        print(f"   Space: {round(large_video_size / 1024, 2)} GB")
        print()
        print(f"⏱️  Old short videos (<{SHORT_VIDEO_DURATION}s, >{SHORT_VIDEO_AGE_YEARS}yr): {len(self.old_short_videos)}")
        print(f"   Space: {round(short_video_size, 2)} MB")
        print()
        print(f"💰 Total potential savings: {round(total_savings_mb / 1024, 2)} GB")
        print()
        print(f"⚠️  Errors encountered: {len(self.errors)}")
        print()
        print(f"Report saved to: {REPORT_FILE}")
        print()

        if len(self.old_large_videos) > 0 or len(self.old_short_videos) > 0:
            print("To review and delete these videos, run:")
            print(f"  python3 ~/scripts/icloud-photo-backup/video_cleanup_aggressive_review.py")

            # Show top 10 largest
            print()
            print("Top 10 largest old videos:")
            for idx, video in enumerate(report['old_large_videos'][:10], 1):
                filepath = Path(video['path'])
                print(f"  {idx}. {filepath.name} - {video['size_mb']:.1f}MB - {video['age_years']:.1f}yr old")
        else:
            print("✓ No videos match the aggressive cleanup criteria!")

def main():
    print("=" * 70)
    print("Aggressive Video Cleanup Tool")
    print("=" * 70)
    print()

    analyzer = AggressiveVideoAnalyzer()
    analyzer.scan_videos()
    analyzer.generate_report()

if __name__ == "__main__":
    main()
