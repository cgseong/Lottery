
try:
    with open('install_log.txt', 'r', encoding='utf-16') as f:
        lines = f.readlines()
except UnicodeError:
    try:
        with open('install_log.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except:
        with open('install_log.txt', 'r', encoding='cp949') as f: # Fallback to common Korean encoding
             lines = f.readlines()

print(f"Total lines: {len(lines)}")
print("--- LAST 30 LINES ---")
for line in lines[-30:]:
    print(line.strip())

print("\n--- ERROR LINES ---")
for line in lines:
    if "error" in line.lower() or "fail" in line.lower() or "exception" in line.lower():
        print(line.strip())
