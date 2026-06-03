#!/usr/bin/env python3
"""
CLI Tool - Command-line interface for the entire Productivity Toolkit.
Usage: python toolkit.py <command> [options]
"""
import sys
import os
import json
import argparse
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from file_organizer import organize_by_type, organize_by_date, find_duplicates, clean_empty_dirs, bulk_rename, directory_tree
from data_processor import csv_to_json, json_to_csv, merge_csv, filter_csv, csv_stats, deduplicate_csv, split_csv
from web_toolkit import url_parser, url_builder, extract_emails, extract_urls, extract_phones, slugify, extract_html_text, html_table_to_json, json_web_request, markdown_to_text, detect_tech_stack
from pdf_toolkit import get_page_count, extract_text as pdf_extract_text, extract_metadata, merge_pdfs, split_pdf, compress_pdf, extract_images, rotate_pages, pdf_to_images_info


def main():
    parser = argparse.ArgumentParser(
        description='Productivity Toolkit - Automate file mgmt, data processing, web tasks, PDFs & more',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python toolkit.py files organize --dir ./downloads
  python toolkit.py files duplicates --dir ./documents
  python toolkit.py data csv2json --input data.csv --output data.json
  python toolkit.py data stats --input sales.csv
  python toolkit.py web emails --text "Contact us at hello@example.com"
  python toolkit.py web url-parse --url "https://example.com/path?key=val"
  python toolkit.py pdf info --input document.pdf
  python toolkit.py pdf merge --inputs a.pdf b.pdf --output merged.pdf
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command categories')

    file_parser = subparsers.add_parser('files', help='File management operations')
    file_subs = file_parser.add_subparsers(dest='subcommand')

    org_parser = file_subs.add_parser('organize', help='Organize files by type')
    org_parser.add_argument('--dir', required=True)
    org_parser.add_argument('--dry-run', action='store_true')

    dup_parser = file_subs.add_parser('duplicates', help='Find duplicate files')
    dup_parser.add_argument('--dir', required=True)

    clean_parser = file_subs.add_parser('clean', help='Remove empty directories')
    clean_parser.add_argument('--dir', required=True)
    clean_parser.add_argument('--dry-run', action='store_true')

    tree_parser = file_subs.add_parser('tree', help='Show directory tree')
    tree_parser.add_argument('--dir', required=True)
    tree_parser.add_argument('--depth', type=int, default=3)

    rename_parser = file_subs.add_parser('rename', help='Bulk rename files')
    rename_parser.add_argument('--dir', required=True)
    rename_parser.add_argument('--pattern', required=True)
    rename_parser.add_argument('--start', type=int, default=1)
    rename_parser.add_argument('--padding', type=int, default=3)
    rename_parser.add_argument('--dry-run', action='store_true')

    data_parser = subparsers.add_parser('data', help='Data processing operations')
    data_subs = data_parser.add_subparsers(dest='subcommand')

    c2j = data_subs.add_parser('csv2json', help='Convert CSV to JSON')
    c2j.add_argument('--input', required=True)
    c2j.add_argument('--output')

    j2c = data_subs.add_parser('json2csv', help='Convert JSON to CSV')
    j2c.add_argument('--input', required=True)
    j2c.add_argument('--output')

    stats_p = data_subs.add_parser('stats', help='CSV statistics')
    stats_p.add_argument('--input', required=True)
    stats_p.add_argument('--columns', nargs='*')

    merge_p = data_subs.add_parser('merge', help='Merge CSV files')
    merge_p.add_argument('--inputs', nargs='+', required=True)
    merge_p.add_argument('--output')
    merge_p.add_argument('--on')

    filter_p = data_subs.add_parser('filter', help='Filter CSV rows')
    filter_p.add_argument('--input', required=True)
    filter_p.add_argument('--column', required=True)
    filter_p.add_argument('--value', required=True)
    filter_p.add_argument('--operator', default='eq')
    filter_p.add_argument('--output')

    dedup_p = data_subs.add_parser('dedup', help='Remove duplicate CSV rows')
    dedup_p.add_argument('--input', required=True)
    dedup_p.add_argument('--output')
    dedup_p.add_argument('--by', nargs='*')

    split_p = data_subs.add_parser('split', help='Split large CSV into parts')
    split_p.add_argument('--input', required=True)
    split_p.add_argument('--output-dir', required=True)
    split_p.add_argument('--rows', type=int, default=1000)

    web_parser = subparsers.add_parser('web', help='Web toolkit operations')
    web_subs = web_parser.add_subparsers(dest='subcommand')

    up = web_subs.add_parser('url-parse', help='Parse URL components')
    up.add_argument('--url', required=True)

    em = web_subs.add_parser('emails', help='Extract emails from text')
    em.add_argument('--text', required=True)

    urls = web_subs.add_parser('urls', help='Extract URLs from text')
    urls.add_argument('--text', required=True)

    sl = web_subs.add_parser('slugify', help='Convert text to URL slug')
    sl.add_argument('--text', required=True)

    pdf_parser = subparsers.add_parser('pdf', help='PDF operations')
    pdf_subs = pdf_parser.add_subparsers(dest='subcommand')

    pi = pdf_subs.add_parser('info', help='PDF info and metadata')
    pi.add_argument('--input', required=True)

    pe = pdf_subs.add_parser('text', help='Extract text from PDF')
    pe.add_argument('--input', required=True)

    pm = pdf_subs.add_parser('merge', help='Merge PDFs')
    pm.add_argument('--inputs', nargs='+', required=True)
    pm.add_argument('--output', required=True)

    ps = pdf_subs.add_parser('split', help='Split PDF')
    ps.add_argument('--input', required=True)
    ps.add_argument('--output-dir', required=True)
    ps.add_argument('--pages-per-file', type=int, default=1)

    pc = pdf_subs.add_parser('compress', help='Compress PDF')
    pc.add_argument('--input', required=True)
    pc.add_argument('--output', required=True)
    pc.add_argument('--quality', default='medium', choices=['low', 'medium', 'high'])

    pei = pdf_subs.add_parser('images', help='Extract images from PDF')
    pei.add_argument('--input', required=True)
    pei.add_argument('--output-dir', required=True)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    result = {'error': 'Unknown command'}

    if args.command == 'files':
        if args.subcommand == 'organize':
            result = organize_by_type(args.dir, args.dry_run)
        elif args.subcommand == 'duplicates':
            result = find_duplicates(args.dir)
        elif args.subcommand == 'clean':
            result = clean_empty_dirs(args.dir, args.dry_run)
        elif args.subcommand == 'tree':
            result = directory_tree(args.dir, args.depth)
            print(result)
            return
        elif args.subcommand == 'rename':
            result = bulk_rename(args.dir, args.pattern, args.start, args.padding, args.dry_run)

    elif args.command == 'data':
        if args.subcommand == 'csv2json':
            result = csv_to_json(args.input, args.output)
        elif args.subcommand == 'json2csv':
            result = json_to_csv(args.input, args.output)
        elif args.subcommand == 'stats':
            result = csv_stats(args.input, args.columns)
        elif args.subcommand == 'merge':
            result = merge_csv(args.inputs, args.output, args.on)
        elif args.subcommand == 'filter':
            result = filter_csv(args.input, args.column, args.value, args.operator, args.output)
        elif args.subcommand == 'dedup':
            result = deduplicate_csv(args.input, args.output, args.by)
        elif args.subcommand == 'split':
            result = split_csv(args.input, args.output_dir, args.rows)

    elif args.command == 'web':
        if args.subcommand == 'url-parse':
            result = url_parser(args.url)
        elif args.subcommand == 'emails':
            result = extract_emails(args.text)
        elif args.subcommand == 'urls':
            result = extract_urls(args.text)
        elif args.subcommand == 'slugify':
            result = slugify(args.text)

    elif args.command == 'pdf':
        if args.subcommand == 'info':
            result = extract_metadata(args.input)
        elif args.subcommand == 'text':
            result = pdf_extract_text(args.input)
            print(result)
            return
        elif args.subcommand == 'merge':
            result = merge_pdfs(args.inputs, args.output)
        elif args.subcommand == 'split':
            result = split_pdf(args.input, args.output_dir, args.pages_per_file)
        elif args.subcommand == 'compress':
            result = compress_pdf(args.input, args.output, args.quality)
        elif args.subcommand == 'images':
            result = extract_images(args.input, args.output_dir)

    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == '__main__':
    main()
