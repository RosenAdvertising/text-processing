#!/usr/bin/env python3
"""
XML Content Processor

This script processes WordPress XML export files and extracts content into a CSV file
with the following columns: Title, Slug, Content, Date, URL, Status, Category, Tags
"""

import os
import csv
import xml.etree.ElementTree as ET
import re
from html import unescape
import argparse
from datetime import datetime

def clean_content(content):
    """Clean HTML content by removing tags and normalizing whitespace"""
    # Remove HTML tags
    content = re.sub(r'<[^>]+>', ' ', content)
    # Replace HTML entities
    content = unescape(content)
    # Normalize whitespace
    content = re.sub(r'\s+', ' ', content).strip()
    return content

def process_xml_file(xml_file, writer):
    """Process a single XML file and write entries to the CSV writer"""
    print(f"Processing {xml_file}...")
    
    # Parse the XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Find the channel element
    channel = root.find('channel')
    if channel is None:
        print(f"Warning: No channel element found in {xml_file}")
        return
    
    # Define namespaces
    namespaces = {
        'content': 'http://purl.org/rss/1.0/modules/content/',
        'wp': 'http://wordpress.org/export/1.2/',
        'excerpt': 'http://wordpress.org/export/1.2/excerpt/',
        'dc': 'http://purl.org/dc/elements/1.1/'
    }
    
    # Process each item
    for item in channel.findall('item'):
        # Skip attachments and other non-post types
        post_type = item.find('.//wp:post_type', namespaces)
        if post_type is None or post_type.text != 'post':
            continue
        
        # Extract post data
        title_elem = item.find('title')
        title = title_elem.text if title_elem is not None and title_elem.text else ""
        
        # Remove CDATA wrapper if present
        if title.startswith('<![CDATA[') and title.endswith(']]>'):
            title = title[9:-3]
        
        link_elem = item.find('link')
        url = link_elem.text if link_elem is not None else ""
        
        post_name = item.find('.//wp:post_name', namespaces)
        slug = post_name.text if post_name is not None else ""
        
        content_elem = item.find('.//content:encoded', namespaces)
        content = content_elem.text if content_elem is not None and content_elem.text else ""
        
        # Remove CDATA wrapper if present
        if content.startswith('<![CDATA[') and content.endswith(']]>'):
            content = content[9:-3]
        
        # Clean the content
        content = clean_content(content)
        
        # Get post date
        post_date = item.find('.//wp:post_date', namespaces)
        date = post_date.text if post_date is not None else ""
        
        # Format date if it exists
        if date:
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                date = date_obj.strftime('%Y-%m-%d')
            except ValueError:
                pass
        
        # Get post status
        status_elem = item.find('.//wp:status', namespaces)
        status = status_elem.text if status_elem is not None else ""
        
        # Get categories
        categories = []
        tags = []
        
        for cat in item.findall('category'):
            domain = cat.get('domain')
            if domain == 'category':
                cat_name = cat.text
                if cat_name:
                    categories.append(cat_name)
            elif domain == 'post_tag':
                tag_name = cat.text
                if tag_name:
                    tags.append(tag_name)
        
        # Join categories and tags with commas
        categories_str = ', '.join(categories)
        tags_str = ', '.join(tags)
        
        # Write to CSV
        writer.writerow({
            'Title': title,
            'Slug': slug,
            'Content': content,
            'Date': date,
            'URL': url,
            'Status': status,
            'Category': categories_str,
            'Tags': tags_str
        })

def main():
    """Main function to process all XML files and generate CSV"""
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Default paths relative to the script location
    default_input_dir = os.path.join(script_dir, 'Raw_XML')
    default_output_file = os.path.join(script_dir, 'processed_content.csv')
    
    parser = argparse.ArgumentParser(description='Process WordPress XML export files into CSV')
    parser.add_argument('--input-dir', default=default_input_dir,
                        help='Directory containing XML files (default: ./Raw_XML)')
    parser.add_argument('--output-file', default=default_output_file,
                        help='Output CSV file path (default: ./processed_content.csv)')
    args = parser.parse_args()
    
    # Ensure input directory exists
    if not os.path.isdir(args.input_dir):
        print(f"Error: Input directory {args.input_dir} does not exist")
        return
    
    # Open output CSV file
    with open(args.output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Title', 'Slug', 'Content', 'Date', 'URL', 'Status', 'Category', 'Tags']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Process each XML file in the directory
        for filename in os.listdir(args.input_dir):
            if filename.endswith('.xml'):
                xml_file = os.path.join(args.input_dir, filename)
                process_xml_file(xml_file, writer)
    
    print(f"Processing complete. Output saved to {args.output_file}")

if __name__ == "__main__":
    main()
