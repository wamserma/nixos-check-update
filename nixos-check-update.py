#!/usr/bin/env python3

import requests
import subprocess

maxcommits = b'100'
nixpkgapiurl = b'https://api.github.com/repos/nixos/nixpkgs/commits'

# get current Nixos Version, may break on unstable
nv = subprocess.run(["nixos-version"],
                    capture_output=True).stdout.split()[0].split(b".")
ntag = b'nixos-'+nv[0]+b'.'+nv[1]
ncommit = subprocess.run(["nixos-version", "--hash"],
                         capture_output=True).stdout

print('Searching commits since: '+str(ncommit))
try:
    response = requests.get(nixpkgapiurl,
                            params=[('per_page', maxcommits),
                                    ('sha', ntag)]
                            )
except HTTPError as http_err:
    print(f'HTTP error occurred: {http_err}')
except Exception as err:
    print(f'Other error occurred: {err}')
else:
    if response.status_code == 200:
        commits = response.json()
        # now rifle through commits until we find ncommit
        updates = []
        # rewrite this with list comprehension?
        found = False
        for c in commits:
            if c['sha'] in str(ncommit):
                found = True
                break
            else:
                m = c['commit']['message'].split('\n', 2)[0]
                updates.append(m)
        updates.reverse()
        if not found:
            print(b'Either you searched on the wrong version ' +
                  b'or you lag more than '+maxcommits+b' updates.')
        else:
            if len(updates) == 0:
                print('Up to date.')
            else:
                for u in updates:
                    print(u)
                print(len(updates)+" Updates")
    else:
        print('Error looking up updates. Got HTTP Status' +
              response.status_code)
