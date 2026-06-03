#!/usr/bin/env python3
"""
XML Content Processor

Processes WordPress XML export files and extracts post content into a CSV file
with columns: Title, Slug, Content, Date, URL, Status, Category, Tags
"""

import os
import csv
import sys
import tempfile
import xml.etree.ElementTree as ET
import re
from html import unescape
import argparse
from datetime import datetime


def clean_content(content):
    """Strip HTML tags, WordPress shortcodes, and normalize whitespace."""
    content = re.sub(
        r"<[a-zA-Z/][^>]*>", " ", content
    )  # strip tags before entity decode to preserve escaped HTML as text
    content = re.sub(
        r"\[/?[a-z_][^\]]*\]", " ", content
    )  # remove WP shortcodes (lowercase names only — avoids [Note], [Update], etc.)
    content = unescape(content)  # decode HTML entities after tag removal
    content = re.sub(r"\s+", " ", content).strip()
    return content


def process_xml_file(xml_file, writer):
    """Process a single XML file and write post entries to the CSV writer. Returns number of skipped items."""
    print(f"Processing {xml_file}...")

    tree = ET.parse(xml_file)
    root = tree.getroot()

    channel = root.find("channel")
    if channel is None:
        print(f"Warning: No channel element found in {xml_file}")
        return 0

    namespaces = {
        "content": "http://purl.org/rss/1.0/modules/content/",
        "wp": "http://wordpress.org/export/1.2/",
        "excerpt": "http://wordpress.org/export/1.2/excerpt/",
        "dc": "http://purl.org/dc/elements/1.1/",
    }

    skipped = 0
    for item in channel.findall("item"):
        try:
            post_type = item.find(".//wp:post_type", namespaces)
            if post_type is None or post_type.text != "post":
                continue

            title_elem = item.find("title")
            title = (
                title_elem.text if title_elem is not None and title_elem.text else ""
            )

            link_elem = item.find("link")
            url = link_elem.text if link_elem is not None else ""

            post_name = item.find(".//wp:post_name", namespaces)
            slug = post_name.text if post_name is not None else ""

            content_elem = item.find(".//content:encoded", namespaces)
            content = (
                content_elem.text
                if content_elem is not None and content_elem.text
                else ""
            )
            content = clean_content(content)

            post_date = item.find(".//wp:post_date", namespaces)
            date = post_date.text if post_date is not None else ""
            if date:
                try:
                    date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S").strftime(
                        "%Y-%m-%d"
                    )
                except ValueError:
                    pass

            status_elem = item.find(".//wp:status", namespaces)
            status = status_elem.text if status_elem is not None else ""

            categories, tags = [], []
            for cat in item.findall("category"):
                domain = cat.get("domain")
                if domain == "category" and cat.text:
                    categories.append(cat.text)
                elif domain == "post_tag" and cat.text:
                    tags.append(cat.text)

            writer.writerow(
                {
                    "Title": title,
                    "Slug": slug,
                    "Content": content,
                    "Date": date,
                    "URL": url,
                    "Status": status,
                    "Category": ", ".join(categories),
                    "Tags": ", ".join(tags),
                }
            )
        except Exception as e:
            print(
                f"Warning: skipping item '{item.findtext('title', '')}' in {xml_file}: {e}",
                file=sys.stderr,
            )
            skipped += 1

    return skipped


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_input_dir = os.path.join(script_dir, "Raw_XML")
    default_output_file = os.path.join(script_dir, "processed_content.csv")

    parser = argparse.ArgumentParser(
        description="Process WordPress XML export files into CSV"
    )
    parser.add_argument(
        "--input-dir",
        default=default_input_dir,
        help="Directory containing XML files (default: ./Raw_XML)",
    )
    parser.add_argument(
        "--output-file",
        default=default_output_file,
        help="Output CSV file path (default: ./processed_content.csv)",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.input_dir):
        print(
            f"Error: Input directory {args.input_dir} does not exist", file=sys.stderr
        )
        sys.exit(1)

    xml_files = sorted(
        f for f in os.listdir(args.input_dir) if f.lower().endswith(".xml")
    )
    if not xml_files:
        print(f"No XML files found in {args.input_dir}", file=sys.stderr)
        sys.exit(1)

    fieldnames = [
        "Title",
        "Slug",
        "Content",
        "Date",
        "URL",
        "Status",
        "Category",
        "Tags",
    ]
    output_dir = os.path.dirname(args.output_file) or "."
    tmp_fd, tmp_path = tempfile.mkstemp(dir=output_dir, suffix=".csv.tmp")
    total_errors = 0
    try:
        with os.fdopen(tmp_fd, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for filename in xml_files:
                try:
                    skipped = process_xml_file(
                        os.path.join(args.input_dir, filename), writer
                    )
                    total_errors += skipped
                except Exception as e:
                    print(f"Warning: skipping {filename}: {e}", file=sys.stderr)
                    total_errors += 1

        os.replace(tmp_path, args.output_file)
    except Exception:
        os.unlink(tmp_path)
        raise

    if total_errors:
        print(
            f"Processing complete with {total_errors} error(s). Output saved to {args.output_file}",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"Processing complete. Output saved to {args.output_file}")


if __name__ == "__main__":
    main()
