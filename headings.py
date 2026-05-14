import re
from pathlib import Path
from tqdm import tqdm
from collections import defaultdict

# ===== CONFIG =====
input_root = Path("split_new")
output_root = Path("output_folder")
log_file = Path("deleted_log.txt")
TAIL_CHECK = 7

punct_pattern = re.compile(r"[.!?।:;)\]\"']\s*$")
lowercase_word_pattern = re.compile(r"\b[a-z]+\b")

# ==================

txt_files = list(input_root.rglob("*.txt"))
deleted_entries = []

# folder-wise deletion counter
folder_deletion_counts = defaultdict(int)

for txt_path in tqdm(txt_files, desc="Processing files", unit="file"):

    relative_path = txt_path.relative_to(input_root)
    output_path = output_root / relative_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    # Split body and tail
    if len(lines) <= TAIL_CHECK:
        body = []
        tail = lines
    else:
        body = lines[:-TAIL_CHECK]
        tail = lines[-TAIL_CHECK:]

    new_tail = []

    for idx, line in enumerate(tail):
        stripped = line.strip()

        # Rule 1: keep if ends with punctuation
        if punct_pattern.search(stripped):
            new_tail.append(line)
            continue

        # Rule 2: keep if >5 lowercase words
        lowercase_words = lowercase_word_pattern.findall(stripped)
        if len(lowercase_words) > 5:
            new_tail.append(line)
            continue

        # Otherwise delete and log
        deleted_entries.append({
            "file": str(txt_path),
            "line_number_from_end": len(tail) - idx,
            "deleted_line": stripped
        })

        # count per folder (top-level under input_root)
        top_folder = relative_path.parts[0] if len(relative_path.parts) > 1 else "ROOT"
        folder_deletion_counts[top_folder] += 1

    cleaned_lines = body + new_tail

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(cleaned_lines)

# ===== Write Log =====
with open(log_file, "w", encoding="utf-8") as log:
    for entry in deleted_entries:
        log.write(
            f"{entry['file']} | tail_line_position={entry['line_number_from_end']} | {entry['deleted_line']}\n"
        )

# ===== Terminal Summary =====
print("\nDone!")
print(f"Files processed: {len(txt_files)}")
print(f"Total lines deleted: {len(deleted_entries)}\n")

print("📁 Per-folder deletion counts:")
for folder, count in sorted(folder_deletion_counts.items()):
    print(f"{folder} → {count} lines removed")

print(f"\nLog file: {log_file}")
print(f"Cleaned output folder: {output_root}")