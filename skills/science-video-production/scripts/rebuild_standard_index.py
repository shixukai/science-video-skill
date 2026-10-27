#!/usr/bin/env python3
"""Rebuild navigation from maintained responsibility bodies, never from copied rules."""
from pathlib import Path
import hashlib
import json
import re
import unicodedata


def slug(text):
    return ''.join(c for c in text.lower() if not unicodedata.category(c).startswith('P') or c in '_-').replace(' ', '-')


def build(root):
    root=Path(root).resolve()
    owners=json.loads((root/'indexes/rule-owners.json').read_text(encoding='utf-8'))['owners']
    sections=[]
    for owner in owners:
        for name in [owner['file'], *owner.get('supporting_files', [])]:
            if not isinstance(name, str) or not (root/name).resolve().is_relative_to(root):
                raise ValueError('navigation path must stay inside Skill')
            p=root/name
            sections.append({'owner_id':owner['id'], 'file':name,
                             'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                             'anchors':[slug(h) for h in re.findall(r'^#{1,6} (.+)$',p.read_text(encoding='utf-8'),re.M)]})
    return {'schema_version':2, 'authority':'responsibility_body', 'status':'navigation_only',
            'scope':'Section navigation and file integrity only. Read the responsible body for applicability; no duplicated requirements, evidence templates, or automatic approval.',
            'sections':sections}


if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    (root/'indexes/standard-coverage.json').write_text(json.dumps(build(root),ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Navigation rebuilt; this does not validate editorial policy or media.')
