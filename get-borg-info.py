#!/usr/bin/python3

from kodiborg.run import Run
from kodiborg.config import ReadBorgConfig

RB = ReadBorgConfig()
RB.read_config()

# Get info on the last nlast backups
nlast = 5
info = Run(repo_location=RB.repo_location,
               args=RB.info_args + [f"--last {nlast}"])

for i in info.run(show_cmd=True, show_output=True):
    #print(i['results']['repository'].keys())
    repo = i['results']['repository']
    print("Repository Information")
    print(f"    Location: {repo['location']}")
    print(f"    ID: {repo['id']}")
    print(f"    Modified: {repo['last_modified']}")
    print()
    print(f"Stats for the last {nlast} backups")
    for a in i['results']['archives']:
        #print(a)
        stats = a['stats']
        print(f"Name: {a['name']} "
              f"Duration: {a['duration']} "
              f"Files: {stats['nfiles']}")
        print(f" Original size: {info.format_bytes(stats['original_size'])} "
              f"Compressed size: {info.format_bytes(stats['compressed_size'])} "
              f"Deduplicated size: {info.format_bytes(stats['deduplicated_size'])}")
