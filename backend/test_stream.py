import requests

url = "http://localhost:5000/emails/stream"
with requests.get(url, stream=True) as resp:
    for line in resp.iter_lines():
        if line:
            print(line.decode('utf-8'))
