#!/usr/bin/env python3
"""
Photo Library Cleanup Tool
Detects and helps remove:
- Duplicate images
- Blurry/out-of-focus images
- Black/dark images
- Old screenshots
"""

import os
import sys
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta
import cv2
import numpy as np
from PIL import Image
import imagehash

BACKUP_DIR = Path("/Users/evanswanson/icloud-photo-backup")
REPORT_FILE = BACKUP_DIR / "cleanup_report.json"

# Configuration
BLUR_THRESHOLD = 100.0  # Lower = more blurry
BLACK_THRESHOLD = 30  # Average brightness below this is considered black
SCREENSHOT_AGE_MONTHS = 6  # Screenshots older than this will be flagged
DUPLICATE_HASH_DIFF = 5  # Perceptual hash difference threshold

class PhotoAnalyzer:
    def __init__(self):
        self.duplicates = defaultdict(list)
        self.blurry_images = []
        self.black_images = []
        self.old_screenshots = []
        self.errors = []
        self.total_scanned = 0

    def is_image_file(self, filepath):
        """Check if file is an image"""
        ext = filepath.suffix.lower()
        return ext in ['.jpg', '.jpeg', '.png', '.heic', '.heif', '.gif', '.bmp', '.tiff']

    def calculate_blur_score(self, image_path):
        """Calculate blur score using Laplacian variance"""
        try:
            img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
            if img is None:
                return None
            laplacian = cv2.Laplacian(img, cv2.CV_64F)
            variance = laplacian.var()
            return variance
        except Exception as e:
            self.errors.append(f"Blur check failed for {image_path}: {e}")
            return None

    def calculate_brightness(self, image_path):
        """Calculate average brightness of image"""
        try:
            img = cv2.imread(str(image_path))
            if img is None:
                return None
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            return np.mean(gray)
        except Exception as e:
            self.errors.append(f"Brightness check failed for {image_path}: {e}")
            return None

    def calculate_perceptual_hash(self, image_path):
        """Calculate perceptual hash for duplicate detection"""
        try:
            img = Image.open(image_path)
            return imagehash.phash(img)
        except Exception as e:
            self.errors.append(f"Hash calculation failed for {image_path}: {e}")
            return None

    def is_screenshot(self, filepath):
        """Detect if image is likely a screenshot"""
        # Check filename patterns
        filename_lower = filepath.name.lower()
        screenshot_patterns = [
            'screenshot', 'screen shot', 'screen_shot',
            'img_', 'image_', 'photo_'
        ]

        is_screenshot_name = any(pattern in filename_lower for pattern in screenshot_patterns)

        # Try to check EXIF data for additional clues
        try:
            img = Image.open(filepath)
            exif = img._getexif() if hasattr(img, '_getexif') else None
            if exif:
                # Screenshots typically don't have camera info
                camera_tags = [271, 272, 42035]  # Make, Model, LensMake
                has_camera_info = any(tag in exif for tag in camera_tags)
                if not has_camera_info and is_screenshot_name:
                    return True
        except:
            pass

        return is_screenshot_name

    def get_image_age(self, filepath):
        """Get age of image file"""
        try:
            # Try to get creation date from EXIF
            img = Image.open(filepath)
            exif = img._getexif() if hasattr(img, '_getexif') else None
            if exif and 36867 in exif:  # DateTimeOriginal
                date_str = exif[36867]
                date = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                return (datetime.now() - date).days
        except:
            pass

        # Fallback to file modification time
        mtime = filepath.stat().st_mtime
        file_date = datetime.fromtimestamp(mtime)
        return (datetime.now() - file_date).days

    def scan_directory(self):
        """Scan directory for all images"""
        print(f"Scanning directory: {BACKUP_DIR}")
        print("This may take a while...")
        print()

        if not BACKUP_DIR.exists():
            print(f"❌ Backup directory not found: {BACKUP_DIR}")
            return

        image_files = list(BACKUP_DIR.rglob("*"))
        image_files = [f for f in image_files if f.is_file() and self.is_image_file(f)]

        total = len(image_files)
        print(f"Found {total} image files to analyze")
        print()

        hash_map = {}

        for idx, filepath in enumerate(image_files, 1):
            self.total_scanned += 1

            if idx % 100 == 0:
                print(f"Progress: {idx}/{total} ({idx*100//total}%)")

            try:
                # Calculate perceptual hash for duplicates
                img_hash = self.calculate_perceptual_hash(filepath)
                if img_hash:
                    # Check for duplicates
                    for existing_hash, existing_path in hash_map.items():
                        diff = img_hash - existing_hash
                        if diff <= DUPLICATE_HASH_DIFF:
                            self.duplicates[str(existing_path)].append(str(filepath))
                            break
                    else:
                        hash_map[img_hash] = filepath

                # Check for blurry images
                blur_score = self.calculate_blur_score(filepath)
                if blur_score is not None and blur_score < BLUR_THRESHOLD:
                    self.blurry_images.append({
                        'path': str(filepath),
                        'blur_score': float(blur_score)
                    })

                # Check for black/dark images
                brightness = self.calculate_brightness(filepath)
                if brightness is not None and brightness < BLACK_THRESHOLD:
                    self.black_images.append({
                        'path': str(filepath),
                        'brightness': float(brightness)
                    })

                # Check for old screenshots
                if self.is_screenshot(filepath):
                    age_days = self.get_image_age(filepath)
                    age_months = age_days / 30
                    if age_months >= SCREENSHOT_AGE_MONTHS:
                        self.old_screenshots.append({
                            'path': str(filepath),
                            'age_months': round(age_months, 1)
                        })

            except Exception as e:
                self.errors.append(f"Error processing {filepath}: {e}")
                continue

        print(f"\n✓ Scan complete! Analyzed {self.total_scanned} images")

    def generate_report(self):
        """Generate cleanup report"""
        # Calculate statistics
        total_duplicates = sum(len(dupes) for dupes in self.duplicates.values())

        report = {
            'scan_date': datetime.now().isoformat(),
            'total_scanned': self.total_scanned,
            'statistics': {
                'duplicate_groups': len(self.duplicates),
                'total_duplicates': total_duplicates,
                'blurry_images': len(self.blurry_images),
                'black_images': len(self.black_images),
                'old_screenshots': len(self.old_screenshots)
            },
            'duplicates': dict(self.duplicates),
            'blurry_images': self.blurry_images,
            'black_images': self.black_images,
            'old_screenshots': self.old_screenshots,
            'errors': self.errors
        }

        # Save report
        with open(REPORT_FILE, 'w') as f:
            json.dump(report, f, indent=2)

        print("\n" + "=" * 60)
        print("CLEANUP REPORT")
        print("=" * 60)
        print(f"Total images scanned: {self.total_scanned}")
        print()
        print(f"📑 Duplicate groups found: {len(self.duplicates)}")
        print(f"   Total duplicate images: {total_duplicates}")
        print()
        print(f"🌫️  Blurry images found: {len(self.blurry_images)}")
        print()
        print(f"⬛ Black/dark images found: {len(self.black_images)}")
        print()
        print(f"📱 Old screenshots found: {len(self.old_screenshots)}")
        print()
        print(f"⚠️  Errors encountered: {len(self.errors)}")
        print()
        print(f"Report saved to: {REPORT_FILE}")
        print()

        # Calculate potential space savings
        if total_duplicates > 0 or len(self.blurry_images) > 0 or len(self.black_images) > 0 or len(self.old_screenshots) > 0:
            print("To review and delete these images, run:")
            print(f"  python3 photo_cleanup_review.py")
        else:
            print("✓ No problematic images found!")

def main():
    print("=" * 60)
    print("Photo Library Cleanup Tool")
    print("=" * 60)
    print()
    print("This tool will scan your photo library for:")
    print("  - Duplicate images")
    print("  - Blurry/out-of-focus images")
    print(f"  - Black/dark images (brightness < {BLACK_THRESHOLD})")
    print(f"  - Screenshots older than {SCREENSHOT_AGE_MONTHS} months")
    print()

    analyzer = PhotoAnalyzer()
    analyzer.scan_directory()
    analyzer.generate_report()

if __name__ == "__main__":
    main()
