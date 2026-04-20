# WordPress XML to CSV Processor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)

A tool that processes WordPress XML export files and extracts content into a structured CSV format for further processing, tagging, or AI ingestion.

## Overview

The processor script (`xml_to_csv.py`) parses WordPress export XML files and extracts the following information for each post:

- **Title**: The post title
- **Slug**: The URL-friendly slug of the post
- **Content**: The main content of the post (cleaned of HTML tags)
- **Date**: The publication date
- **URL**: The full URL of the post
- **Status**: Publication status (published, draft, etc.)
- **Category**: Categories assigned to the post
- **Tags**: Tags assigned to the post

## Project Structure

```
text-processing/
├── LICENSE           # MIT License
├── README.md         # This documentation file
├── Raw_XML/          # Directory for WordPress XML export files (not included)
├── requirements.txt  # Project dependencies (none required)
└── xml_to_csv.py     # Main processing script
```

## Requirements

- Python 3.6+
- Standard library modules only (no external dependencies required)

## Installation

Clone the repository:

```bash
git clone https://github.com/rosenadvertising/text-processing.git
cd text-processing
```

No additional installation steps required.

## Usage

1. Create a `Raw_XML/` directory and place your WordPress XML export files inside it
2. Run the script:

```bash
python xml_to_csv.py
```

By default, the script will:
- Look for XML files in the `Raw_XML/` directory
- Output the processed data to `processed_content.csv`

### Custom Paths

```bash
python xml_to_csv.py --input-dir /path/to/xml/files --output-file /path/to/output.csv
```

## Output Format

| Column   | Description                                    |
|----------|------------------------------------------------|
| Title    | Post title                                     |
| Slug     | URL-friendly post name                         |
| Content  | Cleaned post content (HTML tags removed)       |
| Date     | Publication date (YYYY-MM-DD format)           |
| URL      | Full post URL                                  |
| Status   | Publication status (published, draft, etc.)    |
| Category | Comma-separated list of post categories        |
| Tags     | Comma-separated list of post tags              |

## Notes

- Only processes items with `post_type` set to `post` (skips pages, attachments, etc.)
- HTML tags are stripped from content; HTML entities are decoded
- Categories and tags are extracted as comma-separated lists

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

