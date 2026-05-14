import os
import re
from tqdm import tqdm

input_root = "smart_cleaned_output"
output_root = "split_new"
log_file = "split_log_new.txt"

# This regex is robust for #2, -02, etc. 
lecture_pattern = re.compile(
    r'(?im)^\s*lecture\s*(?:no\.?|number)?\s*[-–:]?\s*#?\s*(\d{1,3})\b'
)

def safe_write(path, text):
    base, ext = os.path.splitext(path)
    counter = 1
    new_path = path
    while os.path.exists(new_path):
        new_path = f"{base}_{counter}{ext}"
        counter += 1
    with open(new_path, "w", encoding="utf-8") as f:
        f.write(text.strip())

log_lines = []
global_txt_count = 0
global_lecture_count = 0
global_course_count = 0
files_with_no_lecture = []

# Collect course folders (original files remain untouched)
course_folders = []
for root, dirs, files in os.walk(input_root):
    if any(f.lower().endswith(".txt") for f in files):
        course_folders.append((root, files))

for root, files in tqdm(course_folders, desc="Processing course folders"):
    txt_files = [f for f in files if f.lower().endswith(".txt")]
    if not txt_files: continue

    global_course_count += 1
    rel_path = os.path.relpath(root, input_root)
    course_output_dir = os.path.join(output_root, rel_path)

    for file in tqdm(txt_files, desc=f"   Splitting {rel_path}", leave=False):
        global_txt_count += 1
        file_path = os.path.join(root, file)
        txt_name = os.path.splitext(file)[0]
        file_output_dir = os.path.join(course_output_dir, txt_name)
        os.makedirs(file_output_dir, exist_ok=True)

        # Read original content (read-only mode)
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            original_text = f.read()

        all_matches = list(lecture_pattern.finditer(original_text))

        if not all_matches:
            files_with_no_lecture.append(file_path)
            continue

        # --- SMART FILTERING ---
        seen_lectures = set()
        filtered_matches = []

        for m in all_matches:
            # Normalize variations (#2, -02, 2) to an integer
            lec_num = int(m.group(1))

            # EXCEPTION: Always allow '1'. For everything else, only the first occurrence.
            if lec_num == 1 or lec_num not in seen_lectures:
                filtered_matches.append(m)
                seen_lectures.add(lec_num)
        
        # --- SPLITTING PROCESS ---
        # 1. Handle Index (everything before the first valid lecture)
        index_text = original_text[:filtered_matches[0].start()].strip()
        if index_text:
            safe_write(os.path.join(file_output_dir, "index.txt"), index_text)

        # 2. Slice the original text based on filtered positions
        lecture_count = 0
        for i, match in enumerate(filtered_matches):
            start_pos = match.start()
            
            # The split ends at the START of the next VALID lecture marker
            if i + 1 < len(filtered_matches):
                end_pos = filtered_matches[i + 1].start()
            else:
                end_pos = len(original_text)

            # Extract the raw chunk from the original text (preserving all duplicate 'Lecture 2' mentions inside)
            lecture_chunk = original_text[start_pos:end_pos].strip()
            
            # Format filename (e.g., "lecture - 02.txt")
            lec_num_str = str(int(match.group(1))).zfill(2)
            out_path = os.path.join(file_output_dir, f"lecture - {lec_num_str}.txt")

            safe_write(out_path, lecture_chunk)
            lecture_count += 1

        global_lecture_count += lecture_count
        log_lines.append(f"   ✅ {file} → {lecture_count} lectures")

# Save the log
os.makedirs("mfa", exist_ok=True)
with open(log_file, "w", encoding="utf-8") as log:
    log.write("\n".join(log_lines))