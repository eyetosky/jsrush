with open('models.py', 'rb') as f:
    content = f.read()
lines = content.split(b'\n')
for i, line in enumerate(lines):
    if b'@staticmethod' in line:
        print(f"Line {i}: {repr(line)}")
        if i + 1 < len(lines):
            print(f"  Next: {repr(lines[i+1])}")