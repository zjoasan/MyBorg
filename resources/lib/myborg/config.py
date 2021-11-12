import xml.etree.ElementTree as ET
import platform
import os

# Read the config info from the XML, and help make the command line
# options for borg

class ReadConfig(object):
    def __init__(self, config_file='borg-backup.xml'):
        self.config_file = config_file
        self.config = None
        self.prune_keep = None
        self.prune_details = None
        self.backup_locs = None
        self.exclude_locs = None
        self.borg_args = None
        self.repo_location = None
        self.estimate_files = False
        self.encryption = False
        self.encryption_passphrase = None
        self._default_args()
        self.__readconfig()


    def _default_args(self):
        """ Default args for prune and create """
        self.default_args = {'info': ['--json'],
                             'init': ['--log-json'],
                             'create': ['--one-file-system',
                                        '--json',
                                        '--log-json',
                                        '--progress'],
                             'prune': ['--stats',
                                       '--list',
                                       '--log-json']}

    def __readconfig(self):
        self.config = ET.parse(self.config_file).getroot()
        bt = self.config.find('backup')
        try:
            self.program = self.config.find('program').text
        except AttributeError:
            self.program = "borg"
        try:
            init = self.config.find('init')
        except AttributeError:
            init = None
        try:
            prune = self.config.find('prune')
        except AttributeError:
            prune = None
        self.repo_dir = self.config.find('repo-path').text
        try:
            self.repo_name = self.config.find('repo-name').text
        except AttributeError:
            self.repo_name = platform.node().title()
        self.repo_path = os.path.join(self.repo_dir, self.repo_name)
        try:
            self.backup_name = self.config.find('backup-name').text
        except AttributeError:
            self.backup_name = "{now:%Y-%m-%d %H:%M:%S}"
        self.repo = "::".join([self.repo_path, f"'{self.backup_name}'"])
        try:
            self.encryption = self.config.find('encryption').text
        except AttributeError:
            self.encryption = 'none'
        try:
            self.encryption_passphrase = self.config.find('encryption-passphrase').text
        except AttributeError:
            self.encryption_passphrase = None
        self.backup_locs = [f"{l.text}" for l in bt.findall('location')]
        try:
            self.exclude_locs = [f"--exclude '{e.text}'" for e in bt.findall('exclude')]
        except AttributeError:
            self.exclude_locs = None

        if init is not None:
            try:
                self.storage_quota = init.find('storage-quota').text
            except AttributeError:
                self.storage_quota = None
            try:
                self.make_parent_dirs = init.find('make-parent-dirs').text
                if self.make_parent_dirs.lower() == 'true':
                    self.make_parent_dirs = True
            except AttributeError:
                self.make_parent_dirs = False

        if prune is not None:
            self.prune_keep = [f"--keep-{l.tag} {l.text}" for l in prune]
            self.prune_details = {l.tag:l.text for l in prune}
        else:
            self.prune_keep = None

        try:
            self.estimate_files = self.config.find('estimate-files').text.lower()
        except AttributeError:
            self.estimate_files = 'none'
