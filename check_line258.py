with open('auth/routes.py', 'rb') as f:
    content = f.read()
idx = content.find(b'url_for("auth.verify_email')
print('Found at:', idx)
if idx >= 0:
    print(repr(content[idx:idx+100]))