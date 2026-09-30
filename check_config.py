with open('config.py', 'r') as f:
    content = f.read()

idx = content.find("JS Rush")
if idx >= 0:
    print(repr(content[idx-50:idx+50]))