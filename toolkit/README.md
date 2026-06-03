# Python Productivity Toolkit

50+ production-ready Python scripts to automate your workflow. File management, data processing, PDF tools, web scraping, image automation — all from your terminal.

## Quick Start

```bash
# Clone or extract the toolkit
cd toolkit

# Run the unified CLI
python scripts/toolkit.py --help

# Example: organize files by type
python scripts/toolkit.py files organize --dir ./downloads

# Example: convert CSV to JSON
python scripts/toolkit.py data csv2json --input data.csv --output data.json

# Example: extract text from PDF
python scripts/toolkit.py pdf text --input document.pdf

# Example: parse a URL
python scripts/toolkit.py web url-parse --url "https://example.com/path?key=val"
```

## Modules

### File Organizer (`file_organizer.py`)
- `organize_by_type()` - Auto-sort files into category folders
- `organize_by_date()` - Group files by year/month
- `find_duplicates()` - Find duplicates by content hash (MD5)
- `clean_empty_dirs()` - Remove empty directories
- `bulk_rename()` - Bulk rename with patterns
- `directory_tree()` - Generate visual directory trees

### Data Processor (`data_processor.py`)
- `csv_to_json()` - Convert CSV to JSON
- `json_to_csv()` - Convert JSON arrays to CSV
- `merge_csv()` - Merge multiple CSV files (with optional joins)
- `filter_csv()` - Filter rows by column value (eq, neq, contains, gt, lt, gte, lte)
- `csv_stats()` - Compute statistics for numeric columns
- `deduplicate_csv()` - Remove duplicate rows
- `split_csv()` - Split large CSVs into smaller files

### Web Toolkit (`web_toolkit.py`)
- `url_parser()` - Parse URLs into components
- `url_builder()` - Build URLs from components
- `extract_emails()` - Extract email addresses from text
- `extract_urls()` - Extract URLs from text
- `extract_phones()` - Extract phone numbers from text
- `slugify()` - Convert text to URL-friendly slugs
- `extract_html_text()` - Strip HTML tags
- `html_table_to_json()` - Convert HTML tables to JSON
- `json_web_request()` - Make HTTP requests with JSON response
- `rate_limiter()` - Decorator for rate limiting
- `markdown_to_text()` - Convert Markdown to plain text
- `detect_tech_stack()` - Detect technologies used by websites

### PDF Toolkit (`pdf_toolkit.py`)
- `get_page_count()` - Count pages in a PDF
- `extract_text()` - Extract readable text
- `extract_metadata()` - Get PDF metadata (title, author, etc.)
- `merge_pdfs()` - Merge multiple PDFs into one
- `split_pdf()` - Split a PDF by page count
- `compress_pdf()` - Reduce PDF file size
- `extract_images()` - Extract embedded images
- `rotate_pages()` - Rotate PDF pages (0, 90, 180, 270)
- `add_watermark()` - Add text watermark to pages
- `pdf_to_images_info()` - Get image info from PDF

### Image Toolkit (`image_toolkit.py`) — requires Pillow
- `batch_resize()` - Resize all images in a directory
- `batch_convert()` - Convert between formats (PNG, JPEG, WebP, etc.)
- `optimize_image()` - Compress images for web
- `add_watermark_image()` - Add text watermarks to images
- `create_thumbnail()` - Generate square thumbnails
- `image_info()` - Get detailed image metadata
- `create_grid_collage()` - Make collages from multiple images
- `batch_filter()` - Apply filters (blur, sharpen, emboss, etc.)

## Requirements

- Python 3.8 or newer
- Optional: Pillow (`pip install Pillow`) for image toolkit

## License

Commercial use allowed. Modify freely. No attribution required.
