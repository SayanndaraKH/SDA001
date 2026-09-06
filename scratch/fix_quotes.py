# -*- coding: utf-8 -*-
with open('app/web/downloader.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the triple quote
text = text.replace("'''\n\n</script>", "\n</script>")
text = text.replace("'''\r\n\r\n</script>", "\n</script>")
text = text.replace("'''\n</script>", "\n</script>")
text = text.replace("'''\r\n</script>", "\n</script>")

with open('app/web/downloader.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Fix script completed.")
