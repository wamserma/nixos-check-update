#!/usr/bin/env python3

import requests
import subprocess

# configurable

printupdates = False  # TODO: make this an cmd-line arg
maxcommits = 500
nixpkgapiurl = b'https://api.github.com/repos/nixos/nixpkgs-channels/commits'
# nixpkgapiurl = b'https://api.github.com/repos/nixos/nixpkgs/commits'

# fixed by GH
maxresponsesfromgithub = 100

# get current Nixos Version, may break on unstable
nv = subprocess.run(["nixos-version"],
                    capture_output=True).stdout.split()[0].split(b".")
ntag = b'nixos-'+nv[0]+b'.'+nv[1]
ncommit = subprocess.run(["nixos-version", "--hash"],
                         capture_output=True).stdout

print('Searching commits since: '+ncommit.decode())


# load history

def loadChunkOfCommits(chunksize, ntag, page):
    try:
        response = requests.get(nixpkgapiurl,
                                params=[('per_page', chunksize),
                                        ('sha', ntag),
                                        ('page', page)]
                                )
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as err:
        print(f'Other error occurred: {err}')
    else:
        if response.status_code == 200:
            commits = response.json()
        else:
            print('Error looking up updates. Got HTTP Status' +
                  response.status_code)
            commits = []
    return commits


page = 0
commits = []
while page * maxresponsesfromgithub < maxcommits:
    page = page + 1
    commits = commits + loadChunkOfCommits(min(maxresponsesfromgithub,
                                               maxcommits),
                                           ntag,
                                           page)


# check for updates

def getNewCommits(basecommit, commits):
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
        print('Either you searched on the wrong version ' +
              'or you lag more than '+str(maxcommits)+' changes.')
    else:
        if len(updates) == 0:
            print('Up to date.')
        else:
            secupdates = 0
            for u in updates:
                if (printupdates):
                    print(u)
                if 'CVE' in u:
                    secupdates = secupdates + 1
                elif 'security' in u:
                    secupdates = secupdates + 1
            nupstr = str(len(updates))
            if len(updates) == 1:
                print(nupstr + ' new commit since your last rebuild.')
            else:
                print(nupstr + ' new commits since your last rebuild.')
            if secupdates > 0:
                print('At least ' + str(secupdates) +
                      ' of these are security related.')
            print("Run 'sudo nixos-rebuild dry-build --upgrade | more'" +
                  " to see how your system is affected.")


getNewCommits(ncommit, commits)
