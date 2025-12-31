import re
import time
import sys
import argparse

from sirsi_entry import SirsiParser

def remove_duplicate_headers(text: str) -> str:
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    
    # Split into lines
    lines = text.split("\n")
    
    result = []
    seen_header = False

    i = 0
    while i < len(lines):
        line = lines[i]

        if "HOLD PICKUP LIST" in line:
            if not seen_header:
                result.extend(lines[i:i+6])
                seen_header = True
            i += 6
            continue
        
        i += 1
        result.append(line)

    return "\n".join(result)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Sort Sirsi report entries by main location.")

    parser.add_argument(
        "input_file", help="Path to the input Sirsi report text file"
    )

    parser.add_argument(
        "-o", "--output_file", default="cleaned_report.txt",
        help="Path to write the cleaned and sorted report"
    )

    parser.add_argument(
        "--sort_order", nargs="+",
        help="List of main locations in desired order, e.g. FICTION NONFICTION GRAPHICNVL"
    )
    args = parser.parse_args()

    input_file = args.input_file
    output_file = args.output_file
    sort_order = args.sort_order or []  # default empty list if not provided
    
    with open(input_file, "r", encoding="utf-8") as f:
        text = f.read()

    cleaned = remove_duplicate_headers(text)

    parser = SirsiParser(cleaned)
    report = parser.parse()

    report.sort_by_location_and_author(sort_order)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(str(report))
