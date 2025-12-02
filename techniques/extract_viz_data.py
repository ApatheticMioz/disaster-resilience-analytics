"""
Extract bibliographic data from viz.txt BibTeX file
Extracts all useful columns: ID, Citation Key, Type, Authors, Title, Year, 
Journal/Booktitle, Abstract, DOI, URL
"""

import re
import csv
from pathlib import Path

def clean_latex(text):
    """Clean LaTeX commands and formatting from text."""
    if not text:
        return ""
    # Remove LaTeX commands like \texttt{x}, \emph{x}, etc.
    text = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)
    # Remove curly braces used for grouping
    text = re.sub(r'\{([^}]*)\}', r'\1', text)
    # Remove backslashes
    text = text.replace('\\', '')
    # Normalize whitespace
    text = ' '.join(text.split())
    return text.strip()


def extract_field(fields_text, field_name):
    """Extract a single field from BibTeX entry."""
    # Handle multi-line fields with nested braces
    pattern = rf'{field_name}\s*=\s*\{{([^{{}}]*(?:\{{[^{{}}]*\}}[^{{}}]*)*)\}}'
    match = re.search(pattern, fields_text, re.IGNORECASE | re.DOTALL)
    if match:
        return clean_latex(match.group(1))
    return ""


def parse_bibtex_file(filepath):
    """Parse BibTeX file and extract entries."""
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Pattern to match BibTeX entries
    entry_pattern = r'@(\w+)\{([^,]+),([^@]*?)(?=\n@|\Z)'
    
    entries = []
    matches = re.findall(entry_pattern, content, re.DOTALL)
    
    for match in matches:
        entry_type = match[0].upper()  # ARTICLE, INPROCEEDINGS, PATENT, etc.
        citation_key = match[1].strip()  # e.g., Aborisade2010
        fields_text = match[2]
        
        # Extract all useful fields
        author = extract_field(fields_text, 'author')
        title = extract_field(fields_text, 'title')
        year = extract_field(fields_text, 'year')
        abstract = extract_field(fields_text, 'abstract')
        doi = extract_field(fields_text, 'doi')
        url = extract_field(fields_text, 'url')
        
        # Journal for articles, booktitle for proceedings
        journal = extract_field(fields_text, 'journal')
        booktitle = extract_field(fields_text, 'booktitle')
        venue = journal if journal else booktitle  # Use whichever is available
        
        # Pages (can be useful for citations)
        pages = extract_field(fields_text, 'pages')
        
        entries.append({
            'citation_key': citation_key,
            'entry_type': entry_type,
            'author': author,
            'title': title,
            'year': year,
            'venue': venue,
            'pages': pages,
            'abstract': abstract,
            'doi': doi,
            'url': url
        })
    
    return entries


def save_to_csv(entries, output_path):
    """Save extracted entries to CSV file."""
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        # Write header - 4 columns as requested
        writer.writerow([
            'ID',           # Auto-incrementing number
            'Title',        # Paper title
            'Abstract'      # Paper abstract
        ])
        
        # Write data rows
        for idx, entry in enumerate(entries, start=1):
            writer.writerow([
                idx,
                entry['title'],
                entry['abstract']
            ])
    
    print(f"Saved {len(entries)} entries to {output_path}")


def save_to_txt(entries, output_path):
    """Save extracted entries to a formatted text file."""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 100 + "\n")
        f.write("EXTRACTED VISUALIZATION BIBLIOGRAPHY\n")
        f.write("=" * 100 + "\n\n")
        f.write(f"Total Entries: {len(entries)}\n")
        f.write("=" * 100 + "\n\n")
        
        for idx, entry in enumerate(entries, start=1):
            f.write(f"{'='*100}\n")
            f.write(f"ID: {idx}\n")
            f.write(f"{'='*100}\n")
            f.write(f"Author:   {entry['author']}\n")
            f.write(f"Title:    {entry['title']}\n")
            f.write(f"\nAbstract:\n{entry['abstract']}\n")
            f.write("\n")
    
    print(f"Saved {len(entries)} entries to {output_path}")


def print_statistics(entries):
    """Print statistics about the extracted data."""
    
    # Count entry types
    type_counts = {}
    for entry in entries:
        t = entry['entry_type']
        type_counts[t] = type_counts.get(t, 0) + 1
    
    # Count years
    year_counts = {}
    for entry in entries:
        y = entry['year']
        if y:
            year_counts[y] = year_counts.get(y, 0) + 1
    
    # Count fields with data
    fields_with_data = {
        'author': sum(1 for e in entries if e['author']),
        'title': sum(1 for e in entries if e['title']),
        'year': sum(1 for e in entries if e['year']),
        'venue': sum(1 for e in entries if e['venue']),
        'abstract': sum(1 for e in entries if e['abstract']),
        'doi': sum(1 for e in entries if e['doi']),
        'url': sum(1 for e in entries if e['url']),
    }
    
    print("\n" + "-" * 60)
    print("DATA STATISTICS:")
    print("-" * 60)
    
    print("\nEntry Types:")
    for t, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {count}")
    
    print("\nField Coverage:")
    for field, count in fields_with_data.items():
        pct = (count / len(entries)) * 100
        print(f"  {field}: {count}/{len(entries)} ({pct:.1f}%)")
    
    print("\nYear Range:")
    years = [int(y) for y in year_counts.keys() if y.isdigit()]
    if years:
        print(f"  Earliest: {min(years)}")
        print(f"  Latest: {max(years)}")


def main():
    # File paths
    script_dir = Path(__file__).parent
    input_file = script_dir / "viz.txt"
    output_csv = script_dir / "viz_extracted.csv"
    output_txt = script_dir / "viz_extracted.txt"
    
    print("=" * 60)
    print("VIZ.TXT BIBLIOGRAPHY EXTRACTOR (Full Extraction)")
    print("=" * 60)
    
    # Check if input file exists
    if not input_file.exists():
        print(f"ERROR: Input file not found: {input_file}")
        return
    
    print(f"\nReading: {input_file}")
    
    # Parse the BibTeX file
    entries = parse_bibtex_file(input_file)
    
    print(f"Found {len(entries)} bibliographic entries")
    
    # Save to CSV
    save_to_csv(entries, output_csv)
    
    # Save to formatted text file
    # save_to_txt(entries, output_txt)
    
    # Print statistics
    print_statistics(entries)
    
    # Print summary
    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE")
    print("=" * 60)
    print(f"\nColumns extracted:")
    print("  1. ID (auto-increment)")
    print("  2. Author")
    print("  3. Title")
    print("  4. Abstract")
    print(f"\nOutput files created:")
    print(f"  1. {output_csv}")
    print(f"  2. {output_txt}")
    
    # Print first few entries as preview
    print("\n" + "-" * 60)
    print("PREVIEW (First 3 entries):")
    print("-" * 60)
    for idx, entry in enumerate(entries[:3], start=1):
        print(f"\n{idx}. {entry['author'][:50]}..." if len(entry['author']) > 50 else f"\n{idx}. {entry['author']}")
        print(f"   Title: {entry['title'][:60]}..." if len(entry['title']) > 60 else f"   Title: {entry['title']}")


if __name__ == "__main__":
    main()
