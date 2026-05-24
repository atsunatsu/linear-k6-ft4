#!/usr/bin/env python3
"""
Parse 324 DFACS references from two Chinese Journal of Aeronautics review papers
and create Obsidian note files for each unique reference.
"""
import re, os, json, hashlib
from pypdf import PdfReader

VAULT = "/mnt/c/Users/3301/Documents/Obsidian Vault"
LIB_DIR = os.path.join(VAULT, "DFACS 文献库")
TOPICS_DIR = os.path.join(LIB_DIR, "Topics")
AUTHORS_DIR = os.path.join(LIB_DIR, "Authors")
os.makedirs(LIB_DIR, exist_ok=True)
os.makedirs(TOPICS_DIR, exist_ok=True)
os.makedirs(AUTHORS_DIR, exist_ok=True)

def extract_all_text(reader):
    return "\n".join(p.extract_text() for p in reader.pages)

def extract_refs(text):
    match = re.search(r'(?:References|REFERENCES)\s*\n', text)
    if not match:
        return ""
    refs = text[match.end():]
    refs = re.sub(r'\nA review on DFACS.*$', '', refs)
    return refs.strip()

def split_refs(text):
    lines = text.split('\n')
    refs = []
    current = ""
    for line in lines:
        if re.match(r'^\d+\.\s', line):
            if current:
                refs.append(current.strip())
            current = line
        else:
            current += " " + line.strip()
    if current:
        refs.append(current.strip())
    return refs

# ─── Parse individual reference ───

def parse_ref(raw):
    """Parse a single reference string into structured fields."""
    text = re.sub(r'^\d+\.\s+', '', raw)
    
    # Try to extract DOI at the end
    doi = ""
    doi_match = re.search(r'(doi|DOI):\s*(10\.\S+)', text)
    if doi_match:
        doi = doi_match.group(2).rstrip('.')
    
    # Detect [Chinese] tag
    is_chinese = False
    if re.search(r'\[Chinese\]', text, re.IGNORECASE):
        is_chinese = True
    
    # The format is: Authors. Title. Journal Year;Vol(Issue):Pages.
    # Or: Authors. Title. Conference/Report details.
    
    # Try to find title split point: first period after a capital letter author list
    # The pattern is: Author names. Title. Journal info...
    # Authors end with a period followed by space and Title
    
    # Split on ". " but be careful with initials like "Lange B."
    # Strategy: find the transition from "Author. Title" 
    # Authors typically end with a period before the title starts
    
    # Better approach: title is between the first period and the second-to-last period group
    parts = re.split(r'\.\s+', text)
    
    authors = ""
    title_parts = []
    journal_info = ""
    
    if len(parts) >= 2:
        authors = parts[0].strip()
        
        # Title is everything until we hit a journal-like pattern or end
        # Journal patterns: "JournalName Year;", "JournalName Vol", "Report No.:", etc.
        title_end = -1
        for i in range(1, len(parts)):
            combined = " ".join(parts[i:i+2])
            if re.search(r'\b(19|20)\d{2}\b', parts[i]):  # year detected
                title_end = i
                break
            if re.search(r'(Report No|Conf|Proc|Presented)', parts[i], re.IGNORECASE):
                title_end = i
                break
        
        if title_end > 1:
            title_parts = parts[1:title_end]
            journal_parts = parts[title_end:]
            journal_info = ". ".join(journal_parts).strip()
        else:
            title_parts = parts[1:]
    
    title = ". ".join(title_parts).strip().rstrip('.')
    journal_info = journal_info.rstrip('.')
    
    # Extract year, volume, issue, pages from journal_info
    year = ""
    vol = ""
    issue = ""
    pages = ""
    
    yr_match = re.search(r'\b(19|20)\d{2}\b', journal_info)
    if yr_match:
        year = yr_match.group(0)
    
    vol_match = re.search(r'(?:^|[\s;])(\d+)\((\d+)\)', journal_info)
    if vol_match:
        vol = vol_match.group(1)
        issue = vol_match.group(2)
    else:
        vol_match = re.search(r'(?:^|[\s;])(\d+)[:;]', journal_info)
        if vol_match:
            vol = vol_match.group(1)
    
    pages_match = re.search(r'(?::|\.\s+)(\d+[-–]\d+)', journal_info)
    if pages_match:
        pages = pages_match.group(1)
    
    # Extract journal name
    journal = ""
    j_match = re.match(r'^([^0-9;]+?)\s*(?:19|20)\d{2}', journal_info)
    if j_match:
        journal = j_match.group(1).strip().rstrip(',').strip()
    
    # Generate unique ID
    first_author = authors.split(',')[0].strip() if authors else "Unknown"
    first_author_last = first_author.split()[-1] if first_author.split() else "Unknown"
    uid = f"{first_author_last}{year}"
    
    # Clean up
    title = re.sub(r'\s+', ' ', title).strip()
    authors = re.sub(r'\s+', ' ', authors).strip()
    
    return {
        'uid': uid,
        'authors': authors,
        'title': title,
        'journal': journal,
        'year': year,
        'volume': vol,
        'issue': issue,
        'pages': pages,
        'doi': doi,
        'is_chinese': is_chinese,
        'journal_info': journal_info,
        'raw': text[:200],
    }

# ─── Read PDFs ───
reader1 = PdfReader("/home/lian/.hermes/cache/documents/doc_f88063e87b57_1.pdf")
reader2 = PdfReader("/home/lian/.hermes/cache/documents/doc_6c6beb16b430_2.pdf")

refs1 = split_refs(extract_refs(extract_all_text(reader1)))
refs2 = split_refs(extract_refs(extract_all_text(reader2)))

all_parsed = {}
for ref_list, source in [(refs1, "DFACS(I)"), (refs2, "DFACS(II)")]:
    for ref in ref_list:
        parsed = parse_ref(ref)
        key = parsed['uid'] + hashlib.md5(parsed['title'].encode()).hexdigest()[:6]
        if key not in all_parsed:
            all_parsed[key] = parsed
            all_parsed[key]['source'] = [source]
        else:
            if source not in all_parsed[key]['source']:
                all_parsed[key]['source'].append(source)

print(f"Total unique references: {len(all_parsed)}")

# ─── Generate safe filename ───
def safe_filename(parsed):
    first = parsed['authors'].split(',')[0].strip().split()[-1] if parsed['authors'] else "Unknown"
    first = re.sub(r'[\\/:*?"<>|]', '', first)
    yr = parsed['year'] if parsed['year'] else "n.d."
    # Take first 40 chars of title
    title_short = re.sub(r'[\\/:*?"<>|]', '', parsed['title'])
    title_short = title_short[:60]
    return f"{first}{yr}_{title_short}"

# ─── Create notes ───
created = 0
failed = 0
all_notes = []

for key, p in all_parsed.items():
    fname = safe_filename(p) + ".md"
    fpath = os.path.join(LIB_DIR, fname)
    
    # Build note content
    content = f"""---
tags: [DFACS/drag-free, {"Chinese" if p['is_chinese'] else "English"}, reference]
source: {"".join(p['source'])}
year: {p['year']}
first_author: {p['authors'].split(',')[0].strip() if p['authors'] else ''}
---

# {p['title']}

**作者：** {p['authors']}

**期刊：** {p['journal']}
**年份：** {p['year']}
{"**卷期：** " + p['volume'] + "(" + p['issue'] + ")" if p['volume'] and p['issue'] else ""}
{"**页码：** " + p['pages'] if p['pages'] else ""}
{"**DOI：** [" + p['doi'] + "](https://doi.org/" + p['doi'] + ")" if p['doi'] else ""}
{"**语言：** 中文" if p['is_chinese'] else "**语言：** 英文"}

**来源综述：** {"".join(p['source'])}

**原始引用：** {p['raw']}

---
*自动导入自 DFACS 综述文献库*
"""
    
    try:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content.lstrip('\n'))
        all_notes.append((fname, p))
        created += 1
    except Exception as e:
        failed += 1
        print(f"FAILED: {fname}: {e}")

print(f"\nCreated: {created}, Failed: {failed}")

# ─── Create Master Index ───
index_path = os.path.join(LIB_DIR, "README.md")
index_content = """# DFACS 无拖曳控制文献库

> 自动从两篇综述中提取的参考文献，共 **{total} 条**。

## 来源综述

| 编号 | 标题 | 期刊 | 年份 |
|------|------|------|------|
| I | A review on DFACS (I): System design and dynamics modeling | Chinese Journal of Aeronautics | 2024 |
| II | A review on DFACS (II): Modeling and analysis of disturbances and noises | Chinese Journal of Aeronautics | 2024 |

## 按年份分布

{years_dist}

## 全部文献列表（{total} 条）

按首字母排序：

{ref_list}

---
*自动生成于 {date}*
"""

# Year distribution
years = [p['year'] for p in all_parsed.values() if p['year']]
from collections import Counter
year_counts = Counter(years)
years_dist = "\n".join(f"- **{y}**: {c}篇" for y, c in sorted(year_counts.items(), reverse=True))

# Reference list sorted by first author
sorted_notes = sorted(all_notes, key=lambda x: x[1]['authors'].lower())
ref_list = "\n".join(
    f"{i+1}. [[{fname.replace('.md','')}]] — {p['authors']} ({p['year']}) \"{p['title']}\""
    for i, (fname, p) in enumerate(sorted_notes)
)

from datetime import date
index_content = index_content.format(
    total=len(all_parsed),
    years_dist=years_dist,
    ref_list=ref_list,
    date=date.today().isoformat()
)

with open(index_path, 'w', encoding='utf-8') as f:
    f.write(index_content.lstrip('\n'))

print(f"Index created at: {index_path}")
print(f"\nDone! {created} reference notes + 1 index in {LIB_DIR}")
