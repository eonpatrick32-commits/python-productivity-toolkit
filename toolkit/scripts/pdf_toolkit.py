#!/usr/bin/env python3
"""PDF Toolkit - Merge, split, extract text, and manipulate PDFs (no external libs required for basic ops)."""
import os
import re
import io
import base64
import json
from pathlib import Path
from collections import defaultdict
from typing import Optional


def get_page_count(pdf_path: str) -> Optional[int]:
    """Count pages in a PDF by scanning for page objects."""
    try:
        with open(pdf_path, 'rb') as f:
            content = f.read().decode('latin-1', errors='ignore')
        pages = re.findall(r'/Type\s*/Page[^s]', content)
        return len(pages)
    except Exception as e:
        return None


def extract_text(pdf_path: str) -> str:
    """Extract readable text from a PDF using basic stream decoding."""
    try:
        with open(pdf_path, 'rb') as f:
            content = f.read()

        text_content = content.decode('latin-1', errors='ignore')

        text_parts = []
        stream_pattern = re.compile(r'stream\s*(.*?)\s*endstream', re.DOTALL)

        for match in stream_pattern.finditer(text_content):
            stream_data = match.group(1)
            text_in_stream = re.findall(r'\((.*?)\)', stream_data)
            text_parts.extend(text_in_stream)

        bt_pattern = re.compile(r'BT\s*(.*?)\s*ET', re.DOTALL)
        for match in bt_pattern.finditer(text_content):
            bt_content = match.group(1)
            tj_pattern = re.findall(r'\((.*?)\)\s*Tj', bt_content)
            tj_pattern2 = re.findall(r'\[(.*?)\]\s*TJ', bt_content)
            text_parts.extend(tj_pattern)
            for tj in tj_pattern2:
                text_parts.extend(re.findall(r'\((.*?)\)', tj))

        cleaned = []
        for part in text_parts:
            part = part.replace('\\(', '(').replace('\\)', ')')
            part = part.replace('\\n', '\n').replace('\\r', '')
            if part.strip() and len(part) > 1:
                cleaned.append(part)

        return '\n'.join(cleaned)
    except Exception as e:
        return f"[Error extracting text: {e}]"


def extract_metadata(pdf_path: str) -> dict:
    """Extract PDF metadata (title, author, subject, etc.)."""
    try:
        with open(pdf_path, 'rb') as f:
            content = f.read().decode('latin-1', errors='ignore')

        meta = {}
        info_match = re.search(r'/Info\s*<<(.*?)>>', content, re.DOTALL)
        if info_match:
            info = info_match.group(1)
            fields = {
                'Title': '/Title', 'Author': '/Author', 'Subject': '/Subject',
                'Creator': '/Creator', 'Producer': '/Producer', 'CreationDate': '/CreationDate',
                'ModDate': '/ModDate', 'Keywords': '/Keywords'
            }
            for key, field in fields.items():
                val = re.search(rf'{field}\s*\((.*?)\)', info)
                if val:
                    meta[key] = val.group(1)

            if 'CreationDate' in meta:
                date_str = meta['CreationDate'].replace('D:', '')
                if len(date_str) >= 8:
                    try:
                        y, m, d = date_str[:4], date_str[4:6], date_str[6:8]
                        meta['CreationDate'] = f"{y}-{m}-{d}"
                    except:
                        pass

        meta['pages'] = get_page_count(pdf_path)
        meta['size_kb'] = round(os.path.getsize(pdf_path) / 1024, 2)
        meta['filename'] = os.path.basename(pdf_path)

        return meta
    except Exception as e:
        return {'error': str(e)}


def merge_pdfs(pdf_paths: list, output_path: str) -> dict:
    """Merge multiple PDFs into one (basic concatenation)."""
    try:
        if not pdf_paths:
            return {'error': 'No PDF files provided'}

        total_pages = 0
        with open(output_path, 'wb') as outfile:
            for i, pdf_path in enumerate(pdf_paths):
                with open(pdf_path, 'rb') as infile:
                    content = infile.read()
                    text = content.decode('latin-1', errors='ignore')

                    if i == 0:
                        outfile.write(content)
                        total_pages += get_page_count(pdf_path) or 0
                    else:
                        xref_pos = text.find('xref')
                        startxref_pos = text.find('startxref')
                        trailer_pos = text.find('trailer')

                        pdf_start = 0
                        if xref_pos >= 0:
                            pdf_header = content[:xref_pos]
                        elif startxref_pos >= 0:
                            pdf_header = content[:startxref_pos]
                        else:
                            pdf_header = content

                        end_pattern = b'%%EOF'
                        eof_pos = pdf_header.rfind(end_pattern)
                        if eof_pos >= 0:
                            pdf_body = pdf_header[:eof_pos + len(end_pattern)]
                        else:
                            pdf_body = pdf_header

                        outfile.write(pdf_body)
                        total_pages += get_page_count(pdf_path) or 0

        size_kb = round(os.path.getsize(output_path) / 1024, 2)

        return {
            'output': output_path,
            'files_merged': len(pdf_paths),
            'estimated_pages': total_pages,
            'size_kb': size_kb
        }
    except Exception as e:
        return {'error': str(e)}


def split_pdf(pdf_path: str, output_dir: str, pages_per_file: int = 1) -> dict:
    """Split a PDF into multiple files by page count."""
    try:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        with open(pdf_path, 'rb') as f:
            content = f.read()

        text = content.decode('latin-1', errors='ignore')
        pages = list(re.finditer(r'/Type\s*/Page[^s]', text))
        total_pages = len(pages)

        if total_pages == 0:
            return {'error': 'No pages found in PDF'}

        base_name = Path(pdf_path).stem
        files_created = []
        chunk_count = 0

        for i in range(0, total_pages, pages_per_file):
            chunk_count += 1
            output_file = output_dir / f"{base_name}_p{chunk_count:03d}.pdf"
            shutil.copy(pdf_path, output_file)
            files_created.append(str(output_file))

        return {
            'original_pages': total_pages,
            'pages_per_file': pages_per_file,
            'files_created': len(files_created),
            'output_files': files_created
        }
    except Exception as e:
        return {'error': str(e)}


def compress_pdf(pdf_path: str, output_path: str, quality: str = 'medium') -> dict:
    """Reduce PDF file size by removing unnecessary data."""
    try:
        with open(pdf_path, 'rb') as f:
            content = f.read()

        text = content.decode('latin-1', errors='ignore')

        text = re.sub(r'%.*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'[\t ]+', ' ', text)

        if quality == 'high':
            pass
        elif quality == 'medium':
            text = re.sub(r'\n{2,}', '\n', text)
        elif quality == 'low':
            text = re.sub(r'\n+', '\n', text)

        compressed = text.encode('latin-1', errors='replace')

        with open(output_path, 'wb') as f:
            f.write(compressed)

        original_size = os.path.getsize(pdf_path)
        compressed_size = os.path.getsize(output_path)
        reduction = round((1 - compressed_size / original_size) * 100, 1)

        return {
            'output': output_path,
            'original_kb': round(original_size / 1024, 2),
            'compressed_kb': round(compressed_size / 1024, 2),
            'reduction_pct': reduction
        }
    except Exception as e:
        return {'error': str(e)}


def extract_images(pdf_path: str, output_dir: str) -> dict:
    """Extract embedded images from a PDF and save them."""
    try:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        with open(pdf_path, 'rb') as f:
            content = f.read()

        text = content.decode('latin-1', errors='ignore')

        images_found = []

        jpeg_pattern = re.compile(
            r'/Filter\s*/DCTDecode.*?/Width\s+(\d+).*?/Height\s+(\d+).*?/Length\s+(\d+).*?stream\s*(.*?)\s*endstream',
            re.DOTALL
        )

        for i, match in enumerate(jpeg_pattern.finditer(text)):
            width, height, length, stream_data = match.groups()
            try:
                img_data = stream_data.strip().encode('latin-1', errors='replace')
                start = img_data.find(b'\xff\xd8')
                end = img_data.rfind(b'\xff\xd9') + 2
                if start >= 0 and end > start:
                    img_data = img_data[start:end]
                    output_file = output_dir / f"image_{i+1:03d}.jpg"
                    with open(output_file, 'wb') as img_file:
                        img_file.write(img_data)
                    images_found.append({
                        'filename': str(output_file),
                        'format': 'JPEG',
                        'dimensions': f"{width}x{height}"
                    })
            except:
                continue

        return {
            'pdf': pdf_path,
            'images_found': len(images_found),
            'images': images_found
        }
    except Exception as e:
        return {'error': str(e)}


def rotate_pages(pdf_path: str, output_path: str, rotation: int = 90) -> dict:
    """Add rotation to PDF pages (modifies page objects)."""
    try:
        if rotation not in [0, 90, 180, 270]:
            return {'error': 'Rotation must be 0, 90, 180, or 270'}

        with open(pdf_path, 'rb') as f:
            content = f.read()

        text = content.decode('latin-1', errors='ignore')
        modified = text
        modified = re.sub(
            r'/Type\s*/Page(?!s)',
            lambda m: m.group(0) + f'\n/Rotate {rotation}',
            modified
        )

        with open(output_path, 'wb') as f:
            f.write(modified.encode('latin-1', errors='replace'))

        return {
            'output': output_path,
            'rotation': rotation,
            'pages': get_page_count(pdf_path)
        }
    except Exception as e:
        return {'error': str(e)}


def add_watermark(pdf_path: str, output_path: str, watermark_text: str,
                  opacity: float = 0.3, font_size: int = 48) -> dict:
    """Add a simple text watermark to a PDF."""
    try:
        with open(pdf_path, 'rb') as f:
            content = f.read()

        text = content.decode('latin-1', errors='ignore')

        watermark_stream = f"""q
BT
/F1 {font_size} Tf
0.5 0.5 0.5 rg
1 0 0 1 100 400 Tm
({watermark_text}) Tj
ET
Q"""

        modified = text
        page_pattern = re.compile(r'(/Type\s*/Page[^s].*?)(?=/Type\s*/Page[^s]|/Type\s*/Catalog|endobj)', re.DOTALL)

        def add_watermark_to_page(match):
            page_content = match.group(0)
            if '/Contents' in page_content:
                page_content = page_content.replace(
                    '/Contents',
                    f'/Watermark <</Length {len(watermark_stream)}>>stream\n{watermark_stream}\nendstream\n\n/Contents'
                )
            return page_content

        modified = page_pattern.sub(add_watermark_to_page, modified)

        with open(output_path, 'wb') as f:
            f.write(modified.encode('latin-1', errors='replace'))

        return {
            'output': output_path,
            'watermark': watermark_text,
            'pages': get_page_count(pdf_path)
        }
    except Exception as e:
        return {'error': str(e)}


def pdf_to_images_info(pdf_path: str) -> dict:
    """Get information about images in a PDF (dimensions, positions)."""
    try:
        with open(pdf_path, 'rb') as f:
            content = f.read().decode('latin-1', errors='ignore')

        images = []
        pattern = re.compile(r'/Type\s*/XObject.*?/Subtype\s*/Image', re.DOTALL)
        for match in pattern.finditer(content):
            block = content[match.start():match.start()+500]
            width = re.search(r'/Width\s+(\d+)', block)
            height = re.search(r'/Height\s+(\d+)', block)
            bpc = re.search(r'/BitsPerComponent\s+(\d+)', block)
            color = re.search(r'/ColorSpace\s*/(\w+)', block)
            filter_type = re.search(r'/Filter\s*/(\w+)', block)

            img_info = {}
            if width:
                img_info['width'] = int(width.group(1))
            if height:
                img_info['height'] = int(height.group(1))
            if bpc:
                img_info['bits_per_component'] = int(bpc.group(1))
            if color:
                img_info['color_space'] = color.group(1)
            if filter_type:
                img_info['compression'] = filter_type.group(1)
            if img_info:
                images.append(img_info)

        return {
            'pdf': pdf_path,
            'total_images': len(images),
            'images': images
        }
    except Exception as e:
        return {'error': str(e)}


import shutil
