#!/usr/bin/env python3
"""Image Toolkit - Batch process, resize, convert, and optimize images."""
import os
import sys
from pathlib import Path
from collections import defaultdict

try:
    from PIL import Image, ImageFilter, ImageEnhance, ImageOps, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def check_pil():
    if not HAS_PIL:
        return {'error': 'Pillow (PIL) is required. Install with: pip install Pillow'}
    return None


def batch_resize(input_dir: str, output_dir: str, width: int = None,
                 height: int = None, scale: float = None,
                 keep_aspect: bool = True, format: str = None) -> dict:
    """Resize all images in a directory."""
    err = check_pil()
    if err:
        return err

    inp = Path(input_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    supported = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.ico'}
    results = []
    errors = []

    for img_path in inp.iterdir():
        if img_path.suffix.lower() not in supported:
            continue
        try:
            img = Image.open(img_path)
            orig_w, orig_h = img.size

            if scale:
                new_w = int(orig_w * scale)
                new_h = int(orig_h * scale)
            elif width and height:
                if keep_aspect:
                    img.thumbnail((width, height), Image.LANCZOS)
                    new_w, new_h = img.size
                else:
                    new_w, new_h = width, height
            elif width:
                ratio = width / orig_w
                new_w = width
                new_h = int(orig_h * ratio)
            elif height:
                ratio = height / orig_h
                new_h = height
                new_w = int(orig_w * ratio)
            else:
                new_w, new_h = orig_w, orig_h

            if keep_aspect and not (width and height and not (width and height)):
                img = img.resize((new_w, new_h), Image.LANCZOS)

            out_format = format or img_path.suffix.lstrip('.')
            if out_format.lower() == 'jpg':
                out_format = 'jpeg'
            out_name = img_path.stem + '.' + (out_format.lower() if out_format != 'jpeg' else 'jpg')
            out_path = out / out_name
            img.save(out_path, format=out_format.upper() if out_format != 'jpeg' else 'JPEG')
            results.append({'from': img_path.name, 'to': out_name, 'size': f"{orig_w}x{orig_h} -> {new_w}x{new_h}"})
        except Exception as e:
            errors.append({'file': img_path.name, 'error': str(e)})

    return {'resized': len(results), 'errors': len(errors), 'files': results}


def batch_convert(input_dir: str, output_dir: str, to_format: str = 'png',
                  quality: int = 85) -> dict:
    """Convert all images to a different format."""
    err = check_pil()
    if err:
        return err

    inp = Path(input_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    supported = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
    converted = []

    for img_path in inp.iterdir():
        if img_path.suffix.lower() not in supported:
            continue
        try:
            img = Image.open(img_path)
            new_ext = to_format.lower()
            if new_ext == 'jpg':
                new_ext = 'jpg'
                save_format = 'JPEG'
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
            elif new_ext == 'jpeg':
                new_ext = 'jpg'
                save_format = 'JPEG'
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
            else:
                save_format = to_format.upper()

            out_name = img_path.stem + '.' + new_ext
            out_path = out / out_name

            if to_format.lower() in ('jpg', 'jpeg'):
                img.save(out_path, save_format, quality=quality, optimize=True)
            else:
                img.save(out_path, save_format)

            converted.append({'from': img_path.name, 'to': out_name})
        except Exception as e:
            continue

    return {'converted': len(converted), 'to_format': to_format, 'files': converted}


def optimize_image(input_path: str, output_path: str = None,
                   quality: int = 75, max_width: int = None) -> dict:
    """Optimize a single image for web (reduce file size)."""
    err = check_pil()
    if err:
        return err

    try:
        img = Image.open(input_path)
        orig_size = os.path.getsize(input_path)

        if max_width and img.width > max_width:
            ratio = max_width / img.width
            new_h = int(img.height * ratio)
            img = img.resize((max_width, new_h), Image.LANCZOS)

        if output_path is None:
            stem = Path(input_path).stem
            output_path = str(Path(input_path).parent / f"{stem}_optimized{Path(input_path).suffix}")

        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGBA')
            img.save(output_path, optimize=True, quality=quality)
        else:
            img = img.convert('RGB')
            img.save(output_path, 'JPEG', optimize=True, quality=quality)

        new_size = os.path.getsize(output_path)
        reduction = round((1 - new_size / orig_size) * 100, 1)

        return {
            'output': output_path,
            'original_size_kb': round(orig_size / 1024, 2),
            'optimized_size_kb': round(new_size / 1024, 2),
            'reduction_pct': reduction
        }
    except Exception as e:
        return {'error': str(e)}


def add_watermark_image(input_path: str, output_path: str,
                        watermark_text: str, position: str = 'bottom-right',
                        opacity: int = 128, font_size: int = 36) -> dict:
    """Add a text watermark to an image."""
    err = check_pil()
    if err:
        return err

    try:
        img = Image.open(input_path).convert('RGBA')
        overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)

        try:
            font = ImageFont.truetype('arial.ttf', font_size)
        except:
            try:
                font = ImageFont.truetype('C:\\Windows\\Fonts\\Arial.ttf', font_size)
            except:
                font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        positions = {
            'top-left': (20, 20),
            'top-right': (img.width - text_w - 20, 20),
            'bottom-left': (20, img.height - text_h - 20),
            'bottom-right': (img.width - text_w - 20, img.height - text_h - 20),
            'center': ((img.width - text_w) // 2, (img.height - text_h) // 2),
        }
        pos = positions.get(position, positions['bottom-right'])

        draw.text(pos, watermark_text, font=font, fill=(255, 255, 255, opacity))
        img = Image.alpha_composite(img, overlay)
        img = img.convert('RGB')
        img.save(output_path, 'PNG')

        return {'output': output_path, 'watermark': watermark_text, 'position': position}
    except Exception as e:
        return {'error': str(e)}


def create_thumbnail(input_path: str, output_path: str = None,
                     size: tuple = (300, 300)) -> dict:
    """Create a square thumbnail from an image."""
    err = check_pil()
    if err:
        return err

    try:
        img = Image.open(input_path)

        img = ImageOps.fit(img, size, Image.LANCZOS, centering=(0.5, 0.5))

        if output_path is None:
            stem = Path(input_path).stem
            output_path = str(Path(input_path).parent / f"{stem}_thumb.jpg")

        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        img.save(output_path, 'JPEG', quality=85)

        return {'output': output_path, 'size': f"{size[0]}x{size[1]}"}
    except Exception as e:
        return {'error': str(e)}


def image_info(input_path: str) -> dict:
    """Get detailed information about an image."""
    err = check_pil()
    if err:
        return err

    try:
        img = Image.open(input_path)
        return {
            'filename': Path(input_path).name,
            'format': img.format,
            'mode': img.mode,
            'size': f"{img.width}x{img.height}",
            'width': img.width,
            'height': img.height,
            'aspect_ratio': round(img.width / img.height, 3) if img.height else 0,
            'file_size_kb': round(os.path.getsize(input_path) / 1024, 2),
            'is_animated': getattr(img, 'is_animated', False),
            'n_frames': getattr(img, 'n_frames', 1),
        }
    except Exception as e:
        return {'error': str(e)}


def create_grid_collage(input_dir: str, output_path: str,
                        cols: int = 3, cell_size: int = 300) -> dict:
    """Create a grid collage from multiple images."""
    err = check_pil()
    if err:
        return err

    inp = Path(input_dir)
    supported = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
    images = []

    for img_path in sorted(inp.iterdir()):
        if img_path.suffix.lower() in supported:
            try:
                img = Image.open(img_path)
                img = ImageOps.fit(img, (cell_size, cell_size), Image.LANCZOS)
                images.append(img)
            except:
                continue

    if not images:
        return {'error': 'No valid images found'}

    rows = (len(images) + cols - 1) // cols
    collage_w = cols * cell_size
    collage_h = rows * cell_size

    collage = Image.new('RGB', (collage_w, collage_h), (240, 240, 240))

    for i, img in enumerate(images):
        row = i // cols
        col = i % cols
        x = col * cell_size
        y = row * cell_size
        collage.paste(img, (x, y))

    collage.save(output_path, 'JPEG', quality=90)

    return {
        'output': output_path,
        'images_used': len(images),
        'grid': f"{cols}x{rows}",
        'cell_size': cell_size,
        'total_size': f"{collage_w}x{collage_h}"
    }


def batch_filter(input_dir: str, output_dir: str,
                 filter_type: str = 'sharpen') -> dict:
    """Apply filters to all images in a directory."""
    err = check_pil()
    if err:
        return err

    inp = Path(input_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    filters = {
        'blur': ImageFilter.BLUR,
        'sharpen': ImageFilter.SHARPEN,
        'edge_enhance': ImageFilter.EDGE_ENHANCE,
        'emboss': ImageFilter.EMBOSS,
        'contour': ImageFilter.CONTOUR,
        'smooth': ImageFilter.SMOOTH,
        'detail': ImageFilter.DETAIL,
    }

    if filter_type not in filters:
        return {'error': f'Unknown filter. Available: {list(filters.keys())}'}

    filt = filters[filter_type]
    supported = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
    results = []

    for img_path in inp.iterdir():
        if img_path.suffix.lower() not in supported:
            continue
        try:
            img = Image.open(img_path)
            filtered = img.filter(filt)
            out_path = out / f"{img_path.stem}_{filter_type}{img_path.suffix}"
            filtered.save(out_path)
            results.append({'from': img_path.name, 'to': out_path.name})
        except Exception as e:
            continue

    return {'processed': len(results), 'filter': filter_type, 'files': results}
