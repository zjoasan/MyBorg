#!/usr/bin/python3

import os
from kodiborg.run import Run
from kodiborg.config import ReadConfig

def header(flen, fsize, ncsize, psize):
    print()
    print(f"{'Current':{flen}}   {'Total':{fsize}} | {'File':>{ncsize}} |")
    print(f"{'File':{flen}} | {'Size':{fsize}} | {'Count':>{ncsize}} | {'Progress':^{psize}}")

RB = ReadConfig()
RB.readconfig()

# wrapper to run borg create
borg = Run(repo_location=RB.repo_location,
               args=RB.create_args,
               locs=RB.backup_locs,
               excludes=RB.exclude_locs)

if RB.estimate_files is not None:
    print("Estimating file count", end="\r", flush=True)
    for est in borg.run(dry_run=True, show_cmd=False, show_output=False, status_update_count=1000):
        if est['type'] == 'log_message':
            print(est['message'])
            continue
        if est['finished']:
            print(f"Estimated files to check: {est['nfiles']}")
        else:
            print(f"Estimating file count: {est['nfiles']}", end="\r", flush=True)
    estimated = est['nfiles']
else:
    estimated = 0

progress_status = {}
flen="<40.40"
fsize=">9.9"
psize="8.8"
ncsize="6"
header_printed=False
saved_lines = []

for i in borg.run(show_output=False, show_cmd=False):
    if i['type'] == 'progress_percent':
        if i['msgid'] not in progress_status:
            print()
            progress_status[i['msgid']] = i['finished']
        if i['finished']:
            print(f"Completed: {i['msgid']}")
        else:
            print(f"{i['message']}")
    elif i['type'] == 'log_message':
        print(f"Unexpected log message: {i['message']}")
    elif i['type'] == 'progress_message':
        if i['msgid'] not in progress_status:
            progress_status[i['msgid']] = i['finished']
            if i['msgid'] == 'cache.begin_transaction':
                print(f"{i['message']}")
        else:
            if i['finished']:
                progress_status[i['msgid']] = True
                if i['msgid'] == 'cache.begin_transaction':
                    print(f"Cache initialized")
                    if not header_printed:
                        header(flen, fsize, ncsize, psize)
                        header_printed = True
                        for l in saved_lines:
                            print(l, end="\r", flush=True)
            else:
                print(f"{i['message']}")

    elif i['type'] == 'backup_done':
        results = i['results']
        if results is None:
            print("Backup failed")
            continue
        archive = results['archive']
        cache = results['cache']
        print(f"\nArchive name: {archive['name']}")
        print(f"Archive fingerprint: {archive['id']}")
        print(f"Time (start): {archive['start']}")
        print(f"Time (end):   {archive['end']}")
        print(f"Duration: {archive['duration']} seconds")
        print(f"Number of files: {archive['stats']['nfiles']}")
        print(f"Utilization of max. archive size: {archive['limits']['max_archive_size']:.0f}%")
        print()
        a_stats = archive['stats']
        c_stats = cache['stats']
        print(f"{'':13.13} "
              f"{'Original Size':13.13} "
              f"{'Compressed Size':15.15} "
              f"{'Deduplicated Size':17.17}")
        print(f"{'This archive:':13.13} "
              f"{borg.format_bytes(a_stats['original_size']):>13.13} "
              f"{borg.format_bytes(a_stats['compressed_size']):>15.15} "
              f"{borg.format_bytes(a_stats['deduplicated_size']):>17.17}")
        print(f"{'All archives:':13.13} "
              f"{borg.format_bytes(c_stats['total_size']):>13.13} "
              f"{borg.format_bytes(c_stats['total_csize']):>15.15} "
              f"{borg.format_bytes(c_stats['unique_size']):>17.17}")
        print()
        print(f"{'':13.13} "
              f"{'Unique chunks':13.13} "
              f"{'Total chunks':>15.15}")
        print(f"{'Chunk index:':13.13} "
              f"{c_stats['total_unique_chunks']:>13d} "
              f"{c_stats['total_chunks']:>15d}")
    else:
        if i['nfiles'] > estimated:
            estimated = i['nfiles']
        if i['path'] == '':
            # No path
            continue
        line = (f"{os.path.split(i['path'])[1]:{flen}} | "
              f"{borg.format_bytes(i['original_size']):{fsize}} | "
              f"{i['nfiles']:{ncsize}d} | ")
        if RB.estimate_files is not None:
            line += f"{i['nfiles'] / estimated:0.1%}"
        else:
            line += "UNKNOWN"
        if not header_printed:
            saved_lines.append(line)
        else:
            print(line, end="\r", flush=True)

if not RB.prune_keep:
    print("Will not prune")
    exit(0)

prune = Run(repo_location=RB.repo_location, args=RB.prune_args + RB.prune_keep)
print("\nPruning the repo")
for pline in prune.run(show_cmd=False, show_output=False):
    if pline['type'] == 'prune_message':
        print(f"{pline['stat']}: {pline['name']}")
    elif pline['type'] == 'log_message': # Final stats from prune
        print(pline['message'])

