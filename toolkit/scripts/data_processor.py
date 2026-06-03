#!/usr/bin/env python3
"""Data Processor - Parse, transform, and analyze CSV, JSON, and Excel data."""
import csv
import json
import io
import sys
from pathlib import Path
from collections import defaultdict
from typing import Any


def csv_to_json(csv_path: str, output_path: str = None, delimiter: str = ',') -> dict:
    """Convert CSV to JSON. Returns dict with data or writes to file."""
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            data = [row for row in reader]

        result = {'count': len(data), 'columns': reader.fieldnames, 'data': data}

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            result['output'] = output_path

        return result
    except Exception as e:
        return {'error': str(e)}


def json_to_csv(json_path: str, output_path: str = None) -> dict:
    """Convert JSON array to CSV."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            data = [data]

        if not data:
            return {'error': 'Empty JSON data'}

        columns = list(data[0].keys())

        if output_path:
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()
                writer.writerows(data)
            return {'count': len(data), 'columns': columns, 'output': output_path}

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(data)
        return {'count': len(data), 'columns': columns, 'csv': output.getvalue()}
    except Exception as e:
        return {'error': str(e)}


def merge_csv(files: list, output_path: str = None, on_column: str = None) -> dict:
    """Merge multiple CSV files. If on_column is set, performs a join."""
    try:
        all_data = []
        columns = set()

        for filepath in files:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                cols = set(reader.fieldnames)
                file_data = list(reader)
                all_data.append({'file': filepath, 'columns': list(reader.fieldnames), 'rows': len(file_data), 'data': file_data})
                columns.update(cols)

        if on_column:
            merged = {}
            for fd in all_data:
                for row in fd['data']:
                    key = row.get(on_column)
                    if key:
                        if key not in merged:
                            merged[key] = row
                        else:
                            merged[key].update({k: v for k, v in row.items() if k != on_column})
            merged_data = list(merged.values())
        else:
            merged_data = []
            for fd in all_data:
                merged_data.extend(fd['data'])
            for i, row in enumerate(merged_data):
                for col in columns:
                    if col not in row:
                        row[col] = ''

        if output_path:
            fieldnames = list(columns)
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(merged_data)
            return {'total_rows': len(merged_data), 'columns': fieldnames, 'output': output_path}

        return {'total_rows': len(merged_data), 'columns': list(columns),
                'data': merged_data}
    except Exception as e:
        return {'error': str(e)}


def filter_csv(csv_path: str, column: str, value: str, operator: str = 'eq',
               output_path: str = None) -> dict:
    """Filter CSV rows by column value. Operators: eq, neq, contains, gt, lt, gte, lte."""
    operators = {
        'eq': lambda a, b: str(a).strip().lower() == str(b).strip().lower(),
        'neq': lambda a, b: str(a).strip().lower() != str(b).strip().lower(),
        'contains': lambda a, b: str(b).strip().lower() in str(a).strip().lower(),
        'gt': lambda a, b: float(a) > float(b),
        'lt': lambda a, b: float(a) < float(b),
        'gte': lambda a, b: float(a) >= float(b),
        'lte': lambda a, b: float(a) <= float(b),
    }

    if operator not in operators:
        return {'error': f'Unknown operator: {operator}. Use: {list(operators.keys())}'}

    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            filtered = [row for row in reader if operators[operator](row.get(column, ''), value)]

        result = {'total': len(filtered), 'filtered': len(filtered)}

        if output_path:
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(filtered)
            result['output'] = output_path

        return result
    except Exception as e:
        return {'error': str(e)}


def csv_stats(csv_path: str, columns: list = None) -> dict:
    """Compute statistics for numeric columns in a CSV."""
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            data = list(reader)

        if columns is None:
            columns = reader.fieldnames

        numeric_columns = []
        for col in columns:
            if col in reader.fieldnames:
                try:
                    float(data[0][col])
                    numeric_columns.append(col)
                except (ValueError, TypeError, IndexError):
                    continue

        stats = {}
        for col in numeric_columns:
            values = []
            for row in data:
                try:
                    values.append(float(row[col]))
                except (ValueError, TypeError):
                    continue
            if values:
                values.sort()
                n = len(values)
                stats[col] = {
                    'count': n,
                    'min': min(values),
                    'max': max(values),
                    'sum': sum(values),
                    'mean': sum(values) / n,
                    'median': values[n // 2] if n % 2 else (values[n // 2 - 1] + values[n // 2]) / 2,
                }

        return {'row_count': len(data), 'numeric_columns': numeric_columns, 'stats': stats}
    except Exception as e:
        return {'error': str(e)}


def deduplicate_csv(csv_path: str, output_path: str = None, by_columns: list = None) -> dict:
    """Remove duplicate rows from CSV."""
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            data = list(reader)

        seen = set()
        unique = []
        duplicates = 0

        for row in data:
            if by_columns:
                key = tuple(str(row.get(c, '')) for c in by_columns)
            else:
                key = json.dumps(row, sort_keys=True)
            if key not in seen:
                seen.add(key)
                unique.append(row)
            else:
                duplicates += 1

        result = {'original': len(data), 'unique': len(unique), 'duplicates_removed': duplicates}

        if output_path:
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(unique)
            result['output'] = output_path

        return result
    except Exception as e:
        return {'error': str(e)}


def split_csv(csv_path: str, output_dir: str, rows_per_file: int = 1000) -> dict:
    """Split a large CSV into smaller files."""
    try:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            data = list(reader)

        files_created = []
        for i in range(0, len(data), rows_per_file):
            chunk = data[i:i + rows_per_file]
            chunk_num = i // rows_per_file + 1
            output_path = output_dir / f"{Path(csv_path).stem}_part{chunk_num}.csv"
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(chunk)
            files_created.append(str(output_path))

        return {'total_rows': len(data), 'files_created': len(files_created),
                'rows_per_file': rows_per_file, 'output_files': files_created}
    except Exception as e:
        return {'error': str(e)}
