#!/usr/bin/env python3
"""
Intelligence Code Extractor
===========================
Extracts all Python code from the intelligence folder and subdirectories
into a single text file for analysis.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

def extract_intelligence_code():
    """Extract all code from intelligence folder into a single text file"""
    
    # Define paths using absolute paths to handle spaces
    current_dir = Path.cwd()
    intelligence_dir = current_dir / "intelligence"
    output_file = current_dir / "intelligence_code_extracted.txt"
    
    # Check if intelligence directory exists
    if not intelligence_dir.exists():
        print(f"❌ Error: {intelligence_dir} directory not found!")
        return False
    
    # File extensions to include
    code_extensions = {'.py', '.pyx', '.pyi'}
    
    # Files to exclude
    exclude_files = {'__pycache__', '.pyc', '.pyo', '.DS_Store'}
    exclude_dirs = {'__pycache__', '.git', '.pytest_cache', 'node_modules'}
    
    extracted_files = []
    total_lines = 0
    
    print(f"🔍 Scanning {intelligence_dir} for Python code files...")
    
    # Open output file for writing
    with open(output_file, 'w', encoding='utf-8') as out_f:
        # Write header
        out_f.write("=" * 80 + "\n")
        out_f.write("INTELLIGENCE FOLDER CODE EXTRACTION\n")
        out_f.write("=" * 80 + "\n")
        out_f.write(f"Extracted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        out_f.write(f"Source directory: {intelligence_dir}\n")
        out_f.write("=" * 80 + "\n\n")
        
        # Recursively walk through intelligence directory
        for root, dirs, files in os.walk(intelligence_dir):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            root_path = Path(root)
            
            # Sort files for consistent output
            files.sort()
            
            for file in files:
                file_path = root_path / file
                
                # Skip excluded files
                if file in exclude_files:
                    continue
                
                # Only process code files
                if file_path.suffix.lower() not in code_extensions:
                    continue
                
                # Get relative path for display (relative to intelligence folder)
                try:
                    rel_path = file_path.relative_to(intelligence_dir)
                    display_path = f"intelligence/{rel_path}"
                except ValueError:
                    # Fallback to absolute path if relative doesn't work
                    display_path = str(file_path)
                
                print(f"📄 Processing: {display_path}")
                
                try:
                    # Read and write file content
                    with open(file_path, 'r', encoding='utf-8') as in_f:
                        content = in_f.read()
                    
                    # Write file header
                    out_f.write("\n" + "=" * 80 + "\n")
                    out_f.write(f"FILE: {display_path}\n")
                    out_f.write(f"SIZE: {file_path.stat().st_size:,} bytes\n")
                    out_f.write(f"LINES: {len(content.splitlines()):,}\n")
                    out_f.write("=" * 80 + "\n\n")
                    
                    # Write content
                    out_f.write(content)
                    
                    # Ensure file ends with newline
                    if not content.endswith('\n'):
                        out_f.write('\n')
                    
                    # Update stats
                    extracted_files.append(display_path)
                    total_lines += len(content.splitlines())
                    
                except Exception as e:
                    print(f"❌ Error reading {display_path}: {e}")
                    out_f.write(f"\n# ERROR: Could not read {display_path}: {e}\n\n")
        
        # Write footer summary
        out_f.write("\n" + "=" * 80 + "\n")
        out_f.write("EXTRACTION SUMMARY\n")
        out_f.write("=" * 80 + "\n")
        out_f.write(f"Total files extracted: {len(extracted_files)}\n")
        out_f.write(f"Total lines of code: {total_lines:,}\n")
        out_f.write(f"Output file: {output_file}\n")
        out_f.write("\nFiles included:\n")
        for i, file_path in enumerate(extracted_files, 1):
            out_f.write(f"{i:3d}. {file_path}\n")
        out_f.write("=" * 80 + "\n")
    
    # Print completion message
    print(f"\n✅ Extraction completed!")
    print(f"📁 Files processed: {len(extracted_files)}")
    print(f"📊 Total lines: {total_lines:,}")
    print(f"💾 Output file: {output_file}")
    print(f"📏 File size: {output_file.stat().st_size:,} bytes")
    
    return True

def main():
    """Main function"""
    print("🧠 Intelligence Code Extractor")
    print("=" * 40)
    
    try:
        success = extract_intelligence_code()
        if success:
            print("\n🎉 Code extraction successful!")
            return 0
        else:
            print("\n❌ Code extraction failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Extraction cancelled by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 