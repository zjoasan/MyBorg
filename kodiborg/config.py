import xml.etree.ElementTree as ET
import platform

class ReadConfig(object):
    def __init__(self, config_file='borg-backup.xml'):
        self.config_file = config_file
        self.config = None
        self.prune_keep = None
        self.backup_locs = None
        self.exclude_locs = None
        self.borg_args = None
        self.repo_location = None
        self.estimate_files = False


    def _default_args(self):
        """ Default args for prune and create """
        self._prune_args = ['prune',
                           '--stats',
                           '--list',
                           '--log-json']
        self._create_args = ['create',
                            '--one-file-system',
                            '--json',
                            '--log-json',
                            '--progress']
        self._info_args = ['info',
                           '--json']

    def readconfig(self):
        self._default_args()
        self.config = ET.parse(self.config_file).getroot()
        bt = self.config.find('backup')
        self.program = self.config.find('program').text
        prune = self.config.find('prune')
        hostname = platform.node().title()
        self.repo_location = self.config.find('repo').text.format(hostname=hostname)
        self.create_args = [self.program] + self._create_args
        self.prune_args = [self.program] + self._prune_args
        self.info_args = [self.program] + self._info_args
        
        self.backup_locs = [f"{l.text}" for l in bt.findall('location')]
        self.exclude_locs = [f"--exclude {e.text}" for e in bt.findall('exclude')]
        self.prune_keep = [f"--keep-{l.tag} {l.text}" for l in prune]

        self.estimate_files = self.config.find('estimate_files')
