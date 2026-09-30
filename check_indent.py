with open('models.py', 'rb') as f:
    content = f.read()

lines = content.split(b'\n')
for i, line in enumerate(lines):
    if b'@staticmethod' in line and i > 700:
        print(f"Line {i}: {repr(line)}")
        if i + 1 < len(content.split(b'\n')):
            print(f"Line {i+1}: {repr(lines[i+1].split(b'\n')[0])}")
        if i + 2 < len(content.split(b'\n')):
            print(f"Line {i+2}: {repr(lines[i+2])}")