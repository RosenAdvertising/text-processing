# Content Processor - WordPress XML Processor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)

A tool that processes WordPress XML export files and extracts content into a structured CSV format for further processing and tagging.

## Overview

The XML processor script (`xml_to_csv.py`) parses WordPress export XML files and extracts the following information for each post:

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
npl-content-ai/
├── LICENSE           # MIT License
├── README.md         # This documentation file
├── Raw_XML/          # Directory for WordPress XML export files
├── requirements.txt  # Project dependencies (none required)
├── xml_to_csv.py     # Main processing script
└── .gitignore        # Git ignore file
```

## Requirements

- Python 3.6+
- Standard library modules (no external dependencies required)

## Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/npl-content-ai.git
cd npl-content-ai
```

No additional installation steps are required as the script only uses Python standard library modules.

## Usage

1. Place your WordPress XML export files in the `Raw_XML` directory
2. Run the script:

```bash
python xml_to_csv.py
```

By default, the script will:
- Look for XML files in the `Raw_XML` directory
- Output the processed data to `processed_content.csv`

### Custom Paths

You can specify custom input and output paths:

```bash
python xml_to_csv.py --input-dir /path/to/xml/files --output-file /path/to/output.csv
```

## Output Format

The script generates a CSV file with the following columns:

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

- The script only processes items with `post_type` set to "post"
- HTML tags are removed from the content
- Categories and tags are extracted and presented as comma-separated lists

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
