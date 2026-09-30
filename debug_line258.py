with open('auth/routes.py', 'r') as f:
    lines = f.readlines()

old_line = lines[257]
print("Old line:", repr(old_line))

# Check each character around the problematic area
for i, c in enumerate(old_line):
    if c in '\\\'\"':
        print(f"Pos {i}: char={c!r} ord={ord(c)}")