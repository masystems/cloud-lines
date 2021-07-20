import requests
import sys

print(f"Domain: {sys.argv[1]}") # https://demo.cloud-lines.com
print(f"Username: {sys.argv[2]}") # myusername
print(f"Password: {sys.argv[3]}") # supersecretpassword

## Get the token
token_res = requests.post(url=f'{sys.argv[1]}/api/api-token-auth', data={'username': sys.argv[2], 'password': sys.argv[3]})
print(token_res.json()['token'])

## create header
headers = {'Content-Type': 'application/json', 'Authorization': f"token {token_res.json()['token']}"}

## get pedigrees
post_res = requests.get(url=f'{sys.argv[1]}/api/pedigrees/?limit=0&offset=0&sale_or_hire=True', headers=headers)
print(post_res.json())