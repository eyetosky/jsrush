with open('models.py', 'r') as f:
    lines = f.readlines()

for i in range(348, 375):
    line = lines[i]
    leading = len(line) - len(line.lstrip())
    print(f'{i+1}: indent={leading}, {repr(lines[i])}')