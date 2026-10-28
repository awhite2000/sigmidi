"""Resolve documentation links against the files included in a portable bundle."""
from pathlib import Path
import posixpath
import re
from urllib.parse import unquote,urlsplit

def portable_markdown(source, destination, entries):
    """Keep available local links relative to the ZIP; render unavailable references as text."""
    source=Path(source)
    mapped={Path(path).resolve():name for path,name in entries}
    # Shared guides have canonical copies under docs/ and portable copies under fusion/.
    root=Path(__file__).resolve().parents[1]
    for guide in ['power','leds','printing-tolerances','resistor-ladders']:
        if guide+'.md' in {name for _,name in entries}:
            for folder in ['docs','design/fusion']:
                mapped[(root/folder/(guide+'.md')).resolve()]=guide+'.md'
    def replace(match):
        prefix,label,target=match.groups();target=target.strip().strip('<>')
        if urlsplit(target).scheme or target.startswith('#'):
            return match.group(0)
        name,sep,anchor=target.partition('#')
        resolved=(source.parent/unquote(name)).resolve()
        if resolved not in mapped:
            return label
        relative=posixpath.relpath(mapped[resolved],posixpath.dirname(destination) or '.')
        return f'{prefix}[{label}]({relative}{sep}{anchor})'
    return re.sub(r'(!?)\[([^\]]*)\]\(([^)]+)\)',replace,source.read_text())
