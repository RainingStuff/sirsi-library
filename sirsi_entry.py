from typing import Optional
from typing import List
import re

class AuthorLine:
    def __init__(self, text: str):
        # Parse "Last, First, YYYY-" or "Last, First"
        parts = [p.strip() for p in text.split(",")]
        self.last_name = parts[0]
        self.first_name = parts[1] if len(parts) > 1 else ""
        self.birth_year = parts[2][:-1] if len(parts) > 2 else None  # remove trailing '-'

    def __str__(self):
        if self.birth_year is not None:
            return f"  {self.last_name}, {self.first_name}, {self.birth_year}-"
        else:
            return f"  {self.last_name}, {self.first_name}"

class TitleStatement:
    def __init__(self, text: str):
        # Parse "Title / Author"
        if "/" in text:
            title, author = text.split("/", 1)
            self.title = title.strip()
            self.author = author.strip()
        else:
            self.title = text.strip()
            self.author = ""

    def __str__(self):
        return f"  {self.title} / {self.author}"

class CopyLine:
    COPY_LINE_FMT = (
        "{indent}"
        "copy:{copies:<5}"
        "item ID:{item_id:<18}"
        "type:{type:<12}"
        "location:{location:<12}"
    )

    def __init__(self, line: str):
        # parse the line
        match = re.search(
            r"copy:(\d+)\s+item ID:(\S+)\s+type:(\S+)\s+location:(\S+)",
            line
        )
        if not match:
            raise ValueError(f"Cannot parse copy line: {line}")

        # assign fields
        self.copies = int(match.group(1))
        self.item_id = match.group(2)
        self.type = match.group(3)
        self.location = match.group(4)

        if "-" in self.location:
            self.main_location, self.sub_location = self.location.split("-", 1)
        else:
            self.main_location = self.location
            self.sub_location = None
        
    def __str__(self):
        return self.COPY_LINE_FMT.format(
            indent="     ",
            copies=self.copies,
            item_id=self.item_id,
            type=self.type,
            location=self.location,
        )


class PickupLine:
    def __init__(self, line: str):
        """
        Parse a Pickup line from Sirsi report text.
        Example line:
        '  Pickup library:"LIBRARY LOCATION CODE"                        Date of discharge:MM/DD/YYYY'
        """
        m = re.search(r'Pickup library:"([^"]+)"\s+Date of discharge:(\S+)', line)
        if not m:
            raise ValueError(f"Cannot parse pickup line: {line}")

        self.pickup_library = m.group(1)
        self.discharge_date = m.group(2)

    def __str__(self):
        left = f'Pickup library:"{self.pickup_library}"'
        right = f'Date of discharge:{self.discharge_date}'
        TOTAL_WIDTH = 80
        indent = "  "
        padding = max(1, TOTAL_WIDTH - len(indent) - len(left) - len(right))
        return f"{indent}{left}{' ' * padding}{right}"

class SirsiEntry:
    def __init__(self, raw_block: str):
        # Parse a raw Sirsi block
        lines = raw_block.strip().splitlines()
        if len(lines) < 5:
            raise ValueError("Block does not have enough lines to parse")
        self.alpha_key = lines[0].strip()
        self.author_line = AuthorLine(lines[1].strip())
        self.title_statement = TitleStatement(lines[2].strip())
        self.copy_line = CopyLine(lines[3])
        self.pickup_line = PickupLine(lines[4])

    def __str__(self):
        return f"{self.alpha_key}\n{self.author_line}\n{self.title_statement}\n{self.copy_line}\n{self.pickup_line}"

class SirsiReport:
    def __init__(self, header: str, entries: List[SirsiEntry] = None):
        self.entries = entries or []
        self.header = header

    def add_entry(self, entry: SirsiEntry):
        self.entries.append(entry)

    def __str__(self):
        entries = "\n\n".join(str(entry) for entry in self.entries)
        return self.header + entries
    
    def sort_by_location(self, sort_order):
        """
        Sort entries in place by the main location according to sort_order.
        Entries not in sort_order are placed at the end.
        """
        def location_sort_key(entry: SirsiEntry):
            loc = entry.copy_line.main_location
            return sort_order.index(loc) if loc in sort_order else len(sort_order)

        self.entries.sort(key=location_sort_key)

    def sort_by_location_and_author(self, sort_order):
        def key(entry: SirsiEntry):
            loc = entry.copy_line.main_location
            loc_index = sort_order.index(loc) if loc in sort_order else len(sort_order)
            last = entry.author_line.last_name
            first = entry.author_line.first_name
            return (loc_index, last, first)
        
        self.entries.sort(key=key)
    
class SirsiParser:
    def __init__(self, text: str):
        self.text = text

    def parse(self) -> SirsiReport:

        HEADER_PATTERN = re.compile(
            r"""
            \s*HOLD\ PICKUP\ LIST\s*\n       # "HOLD PICKUP LIST" line with optional spaces
            \s*\n?                           # optional blank line
            \s*Produced\s+"[^"]+"\s*\n       # Produced "DAY NAME ..." line
            \s*\n?                           # optional blank line
            \s*Library:\s+"[^"]+"\s*         # Library: "..." line
            """,
            re.VERBOSE
        )

        # Extract the first header
        match = HEADER_PATTERN.search(self.text)
        header = match.group(0) if match else ""
    
        entries = []
        # Split by double newline between blocks
        blocks = [b for b in self.text.split("\n\n") if b.strip()]
        for block in blocks:
            try:
                entry = SirsiEntry(block)
                entries.append(entry)
            except ValueError:
                continue
        return SirsiReport(header, entries)