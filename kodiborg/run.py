import json
import subprocess
import os

class Run(object):
    """ RunBorg
        A class to wrap borg command lines
    """
    def __init__(self, repo_location=None,
                 backup_name='{now:%Y-%m-%d %H:%M:%S}',
                 args=[], excludes=[], locs=[]):

        self.args = args
        self.repo_location = repo_location
        self.backup_name = backup_name
        self.excludes = excludes
        self.locs = locs

    def _build_cmd(self, args):
        """ Used to build the borg command line to spawn """
        if 'prune' in args or 'info' in args:
            repo = f"'{self.repo_location}'"
        else:
            repo = f"'{self.repo_location}::{self.backup_name}'"
        return (f"{' '.join(args)} "
                f"{' '.join(self.excludes)} "
                f"{repo} "
                f"{' '.join(self.locs)}")

    def run(self, dry_run=False, show_output=False,
                 status_update_count=1000, show_cmd=False):
        """ Spawn a borg process. Output will be sent
            line by line to the calling script. Most lines are
            untouched, but some will have additional info added
            to what borg sent
        """
        if dry_run:
            additional_args = ['--dry-run', '--list']
            count = 0
            estimate_status = {'type': 'estimating',
                               'finished': False,
                               'nfile': 0}
        elif self.args[1] != 'info':
            additional_args = ['--stats']
        else:
            additional_args = []
        cmd = self._build_cmd(self.args + additional_args)
        if show_cmd:
            print(f"Running: {cmd}")
        proc = subprocess.Popen(cmd,
                                shell=True,
                                encoding='utf-8',
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        for j in self._get_json(proc):
            if show_output:
                print(j)
            if j['type'] == 'file_status':
                if j['status'] == '-' and os.path.isfile(j['path']): # A file
                    count += 1
                    if count % status_update_count == 0:
                        estimate_status['nfiles'] = count
                        yield estimate_status
            elif j['type'] == 'archive_progress':
                yield j
            elif j['type'] == 'progress_message':
                yield j
            elif j['type'] == 'progress_percent':
                yield j
            elif j['type'] == 'log_message':
                if j['name'] == 'borg.output.list':
                    message_parts = j['message'].split(' archive: ')
                    prune_stat = message_parts[0]
                    archive_parts = message_parts[1].split('     ')
                    archive_name = archive_parts[0]
                    archive_date, archive_id = archive_parts[-1].strip().split(' [')
                    archive_id = '[' + archive_id
                    yield {'type': 'prune_message',
                           'stat': prune_stat,
                           'name': archive_name,
                           'date': archive_date,
                           'id': archive_id}
                else:
                    yield j
            else:
                print('other', j)
        try:
            json_results = json.loads(proc.stdout.read())
        except json.decoder.JSONDecodeError:
            json_results = None

        if dry_run:
            estimate_status['nfiles'] = count
            estimate_status['finished'] = True
            yield estimate_status
        else:
            yield {'type': 'backup_done', 'results': json_results}

    def _get_json(self, proc):
        """ Read the json returned from borg, line by line until
            a complete json line was received. Then decode the json
            to a python dict
        """
        line = ''
        while True:
            out = proc.stderr.read(1)
            if proc.poll() is not None:
                break
            if out == '\n':
                try:
                    yield json.loads(line)
                except json.decoder.JSONDecodeError:
                    yield line
                line = ""
            else:
                line += out
                
    def format_bytes(self, size):
        """ Instead of requiring humanize to be installed
            use this simple bytes converter.
        """
        power = 2**10
        n = 0
        labels = {0: '',
                  1: 'K',
                  2: 'M',
                  3: 'G',
                  4: 'T'}
        while size > power:
            size /= power
            n += 1
        return f"{size:0.3f}{labels[n]}B"
