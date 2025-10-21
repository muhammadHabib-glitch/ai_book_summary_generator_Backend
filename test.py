import requests

url = "https://www.defence.lk/upload/ebooks/David%20Copperfield.pdf"
output_file = "downloaded.pdf"

with requests.get(url, stream=True) as r:
    r.raise_for_status()
    with open(output_file, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:  # skip keep-alive chunks
                f.write(chunk)

print(f"PDF downloaded successfully as {output_file}")
