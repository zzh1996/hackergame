import markdown.treeprocessors
import pathlib
import shutil
import traceback
import uuid
import yaml

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.transaction import atomic

from server.challenge.interface import Challenge
from server.context import Context

UUID_NAMESPACE = uuid.uuid5(
    namespace=uuid.UUID('dcd82ef8-ab13-4942-829c-41aa47f1708b'),
    name=settings.SECRET_KEY,
)

INDEX_LOW_PART = 10000

class ReplaceLinks(markdown.extensions.Extension):
    class Processor(markdown.treeprocessors.Treeprocessor):
        def __init__(self, md, files_url):
            super().__init__(md)
            self.files_url = files_url

        def run(self, root):
            for node in root.iter('a'):
                if node.attrib['href'].startswith('files/'):
                    node.attrib['href'] = str(self.files_url
                                              / node.attrib['href'][6:])
            for node in root.iter('img'):
                if node.attrib['src'].startswith('files/'):
                    node.attrib['src'] = str(self.files_url
                                             / node.attrib['src'][6:])
            for node in root.iter('a'):
                if node.attrib['href'].startswith(('http://', 'https://')):
                    node.attrib['target'] = '_blank'
                    node.attrib['rel'] = 'noopener'

    def __init__(self, files_url):
        super().__init__()
        self.files_url = files_url

    def extendMarkdown(self, md):
        processor = self.Processor(self, self.files_url)
        md.treeprocessors.register(processor, 'replacelinks', 0)


class Command(BaseCommand):
    help = '从题目仓库导入数据'

    def add_arguments(self, parser):
        parser.add_argument('challenges_dir', type=pathlib.Path)
        parser.add_argument('--dry-run', action='store_true')

    # noinspection PyAttributeOutsideInit
    @atomic
    def handle(self, challenges_dir, dry_run=False, **options):
        self.challenges_dir = challenges_dir
        self.media_dir = pathlib.Path(settings.MEDIA_ROOT)
        self.dry_run = dry_run
        context = Context(elevated=True)
        old_challenges = {i.index % INDEX_LOW_PART: i for i in Challenge.get_all(context)}
        new_challenges = {}
        for path in challenges_dir.iterdir():
            if not path.is_dir() or path.name.startswith('.'):
                continue
            # noinspection PyBroadException
            try:
                challenge = self.parse_challenge(path)
            except Exception as e:
                msg = traceback.format_exception_only(type(e), e)[0].strip()
                self.stdout.write(self.style.ERROR(f'{path.name}: {msg}'))
            else:
                if challenge['enabled']:
                    new_challenges[challenge['index'] % INDEX_LOW_PART] = challenge
        self.stdout.write(f'Parsed {len(new_challenges)} challenges')
        for id in sorted(new_challenges):
            if id in old_challenges:
                if not dry_run:
                    old_challenges[id].update(**new_challenges[id])
                self.stdout.write(f'{id}_{new_challenges[id]["name"]}: ' + self.style.WARNING('updated'))
            else:
                if not dry_run:
                    Challenge.create(context, **new_challenges[id])
                self.stdout.write(f'{id}_{new_challenges[id]["name"]}: ' + self.style.SUCCESS('created'))
        for id in sorted(old_challenges):
            if id not in new_challenges:
                if not dry_run:
                    old_challenges[id].delete()
                self.stdout.write(f'{id}_{old_challenges[id]["name"]}: ' + self.style.NOTICE('deleted'))

    def parse_challenge(self, path):
        # default values
        challenge = {
            'enabled': True,
            'name': path.name,
            'category': None,
            'url': None,
            'prompt': 'flag{...}',
            'index': 0,
            'flags': [],
        }
        readme = path / 'README.md'
        with readme.open() as f:
            dic = next(yaml.safe_load_all(f))
            dic['index'] = dic['index'] * INDEX_LOW_PART + dic['id']
            del dic['id']
            challenge.update(dic)
        lines = readme.read_text().splitlines(keepends=True)
        lines = lines[lines.index('---\n', 1) + 1:]
        files_uuid = str(uuid.uuid5(UUID_NAMESPACE, challenge['name']))
        files_path = self.media_dir / files_uuid
        files_url = pathlib.Path('/media') / files_uuid
        files = path / 'files'
        if files.is_dir():
            if not self.dry_run:
                shutil.rmtree(files_path, ignore_errors=True)
                shutil.copytree(files, files_path)
        if challenge['url'] and challenge['url'].startswith('files/'):
            challenge['url'] = str(files_url / challenge['url'][6:])
        challenge['detail'] = markdown.markdown(
            ''.join(lines),
            extensions=['codehilite', ReplaceLinks(files_url)],
        )
        return challenge
