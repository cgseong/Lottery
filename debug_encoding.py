
import csv
import os

data_file = '로또당첨번호.csv'
encodings = ['utf-8', 'cp949', 'euc-kr']

print(f"File exists: {os.path.exists(data_file)}")
print(f"File size: {os.path.getsize(data_file)} bytes")

for enc in encodings:
    print(f"\nTrying encoding: {enc}")
    try:
        with open(data_file, 'r', encoding=enc) as f:
            reader = csv.DictReader(f)
            try:
                # Read first row to get keys and data
                row = next(reader)
                keys = list(row.keys())
                print(f"  Success! Keys: {keys}")
                print(f"  First row: {row}")
                
                if any('번호1' in str(k) for k in keys):
                    print("  MATCH FOUND: '번호1' is in keys")
                else:
                    print("  NO MATCH: '번호1' not found in keys")
                    
            except StopIteration:
                print("  File is empty (no data rows)")
            except Exception as e:
                print(f"  Error reading CSV content: {e}")
                
    except Exception as e:
        print(f"  Error opening file: {e}")
