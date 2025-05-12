with open('requirements.txt', 'rb') as f:
    content = f.read()

# Remove null bytes
clean_content = content.replace(b'\x00', b'')

with open('requirements.txt', 'wb') as f:
    f.write(clean_content)
