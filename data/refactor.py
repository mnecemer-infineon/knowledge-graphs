import json
import os
from typing import Optional
from pypinyin import lazy_pinyin

def convert_to_json_array(input_path: str, output_path: Optional[str] = None, translate_names: bool = True):
    """
    Converts a file with newline-separated JSON objects to a valid JSON array file.
    Optionally translates Chinese names to pinyin.
    Args:
        input_path: Path to the input file.
        output_path: Path to write the output file. If None, overwrites input file.
        translate_names: If True, convert Chinese names to pinyin.
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip() and not line.strip() in ['[', ']']]
    objs = []
    import re
    def is_chinese(text):
        if not isinstance(text, str) or not text.strip():
            return False
        # Count Chinese characters
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        # Consider as Chinese if >70% of non-space chars are Chinese
        return len(chinese_chars) / max(1, len(text.replace(' ',''))) > 0.7

    for line in lines:
        try:
            obj = json.loads(line.rstrip(','))
            if translate_names:
                for k, v in obj.items():
                    if isinstance(v, str) and is_chinese(v):
                        obj[k] = ' '.join([s.capitalize() for s in lazy_pinyin(v)])
            objs.append(obj)
        except Exception as e:
            print(f"Skipping line due to error: {e}\n{line}")
    out_path = output_path or input_path
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(objs, f, ensure_ascii=False, indent=2)
    print(f"Converted {input_path} to valid JSON array at {out_path}")

def convert_all_in_folder(folder: str, translate_names: bool = True):
    """
    Converts all .json files in a folder to valid JSON arrays.
    """
    for fname in os.listdir(folder):
        if fname.endswith('.json'):
            convert_to_json_array(os.path.join(folder, fname), translate_names=translate_names)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Convert newline JSON to array JSON.")
    parser.add_argument('file_or_folder', help='File or folder to process')
    parser.add_argument('--no-translate', action='store_true', help='Do not translate names to pinyin')
    args = parser.parse_args()
    if os.path.isdir(args.file_or_folder):
        convert_all_in_folder(args.file_or_folder, translate_names=not args.no_translate)
    else:
        convert_to_json_array(args.file_or_folder, translate_names=not args.no_translate)
