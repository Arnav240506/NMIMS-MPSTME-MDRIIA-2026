"""Build and verify portable offline and GitHub packages from the current group."""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import argparse, csv, hashlib, io, json, zipfile
import xml.etree.ElementTree as ET
from pypdf import PdfReader

GROUP = Path(__file__).resolve().parents[1]
PREFIX = GROUP.name + '/'
OUT = GROUP.parent / 'submission'
EXCLUDE = {'.venv', '.git', '__pycache__', '.pytest_cache', 'local_runs', 'development_runs', 'development_evidence', 'capstone_rerun'}
HISTORICAL = {'benchmark', 'obstacle_course', 'climbing_course', 'demo_runs', 'dossier', 'course_regressions', 'safety_fixtures', 'smoke'}

def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4*1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def selected(github=False):
    for p in sorted(GROUP.rglob('*')):
        if not p.is_file():
            continue
        rel = p.relative_to(GROUP)
        if EXCLUDE.intersection(rel.parts) or p.suffix.lower() in {'.pyc', '.aux', '.out', '.log', '.bak'}:
            continue
        if p.name in {'FILE_MANIFEST.json', 'FILE_INVENTORY.csv'}:
            continue
        if github and (p.suffix.lower() in {'.mp4', '.avi', '.npz'} or (rel.parts[0] == 'analytics' and len(rel.parts) > 1 and rel.parts[1] in HISTORICAL)):
            continue
        yield p

def verify(archive):
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        assert len(names) == len(set(names))
        for n in names:
            p = PurePosixPath(n)
            assert n.startswith(PREFIX) and not p.is_absolute() and '..' not in p.parts
            assert not EXCLUDE.intersection(p.parts)
        manifest_name = PREFIX+'docs/FILE_MANIFEST.json'
        manifest = json.loads(z.read(manifest_name))
        assert set(names) == {r['path'] for r in manifest['files']} | {manifest_name}
        assert manifest['file_count'] == len(names)-1
        for row in manifest['files']:
            h = hashlib.sha256(); count = 0
            with z.open(row['path']) as f:
                for block in iter(lambda: f.read(4*1024*1024), b''):
                    h.update(block); count += len(block)
            assert count == row['bytes'] and h.hexdigest() == row['sha256'], row['path']
        # Reading all members to EOF also checks ZIP CRC.
        assert len([n for n in names if n.startswith(PREFIX+'M20/meshes/') and n.lower().endswith('.stl')]) == 17
        required = {'MDRIIA_Group_09_Technical_Dossier.pdf': 4, 'M20_Complete_Step_by_Step_Run_Guide.pdf': 10,
                    'M20_Extended_Technical_Report.pdf': 6, 'paper/Group09_HazardousTerrain_IEEE.pdf': 4}
        pages = {}
        for filename, count in required.items():
            pages[filename] = len(PdfReader(io.BytesIO(z.read(PREFIX+'docs/'+filename))).pages)
            assert pages[filename] == count
        with zipfile.ZipFile(io.BytesIO(z.read(PREFIX+'docs/MDRIIA_Group_09_Technical_Dossier.docx'))) as d:
            tree = ET.fromstring(d.read('word/document.xml'))
            assert len(tree.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}sdt')) == 212
        audit = json.loads(z.read(PREFIX+'analytics/capstone_500hz/verification.json'))
        assert audit['status'] == 'PASS' and audit['actual_trials_checked'] == 60 and audit['total_actual_samples'] == 4495972
        physical = hashlib.sha256()
        model_prefix = PREFIX+'M20/'
        for n in sorted(n for n in names if n.startswith(model_prefix) and '/' not in n[len(model_prefix):] and n.endswith('.py')):
            physical.update(PurePosixPath(n).name.encode()); physical.update(z.read(n))
        physical.update(z.read(model_prefix+'M20.xml'))
        for n in sorted(n for n in names if n.startswith(model_prefix+'meshes/') and n.endswith('.STL')):
            physical.update(z.read(n))
        assert physical.hexdigest() == audit['source_sha256'], 'Archived physical source differs from measured study'
        assert len([n for n in names if n.startswith(PREFIX+'analytics/capstone_500hz/') and n.endswith('/summary.json')]) == 60
        portable = json.loads(z.read(PREFIX+'analytics/capstone_group_only_verification.json'))
        assert portable['status'] == 'PASS' and portable['tests'] == 54 and portable['accepted'] and portable['climbs'] == 2
        assert portable['source_sha256'] == audit['source_sha256']
        roster = z.read(PREFIX+'docs/TEAM_ROSTER.json').decode('utf-8')
        assert all(x in roster for x in ['70362400067', '70362400086', '70362300032'])
        qa = json.loads(z.read(PREFIX+'docs/provenance/capstone_document_qa.json'))
        for row in qa['documents']:
            assert hashlib.sha256(z.read(PREFIX+row['path'])).hexdigest() == row['sha256']
        if manifest['kind'] == 'github':
            assert not any(PurePosixPath(n).suffix.lower() in {'.mp4', '.avi', '.npz'} for n in names)
            assert max(i.file_size for i in z.infolist()) < 100*1024*1024
    return {'status': 'PASS', 'kind': manifest['kind'], 'entries': len(names), 'all_member_SHA256_and_CRC': 'PASS',
            'actual_trials': 60, 'actual_500hz_samples': 4495972, 'tests_in_portability_receipt': 54,
            'dossier_controls': 212, 'PDF_pages': pages, 'archive_sha256': sha256(archive)}

def main():
    OUT.mkdir(exist_ok=True)
    receipts = []
    for github, name in [(False, 'Group09_M20_Quadruped_Submission.zip'), (True, 'Group09_GitHub_Ready.zip')]:
        files = list(selected(github))
        rows = []
        for index,p in enumerate(files):
            rows.append({'path': PREFIX+p.relative_to(GROUP).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha256(p)})
            if index % 250 == 0:
                print(f'Hashing {name}: {index+1}/{len(files)}', flush=True)
        inventory = io.StringIO(newline='')
        writer = csv.DictWriter(inventory, fieldnames=['path', 'bytes', 'sha256'])
        writer.writeheader(); writer.writerows(rows)
        inventory_data = inventory.getvalue().encode('utf-8')
        rows.append({'path': PREFIX+'docs/FILE_INVENTORY.csv', 'bytes': len(inventory_data), 'sha256': hashlib.sha256(inventory_data).hexdigest()})
        manifest = {'created_utc': datetime.now(timezone.utc).isoformat(), 'kind': 'github' if github else 'offline',
                    'scope': 'Portable group folder; final 60-trial 500 Hz evidence. Included historical evidence remains separate.',
                    'manifest_excludes_itself': True, 'file_count': len(rows), 'files': rows}
        data = json.dumps(manifest, indent=2).encode('utf-8')
        target = OUT/name; temporary = target.with_suffix('.building.zip')
        print(f'Building {name}: {len(files)} files, {sum(r["bytes"] for r in rows):,} uncompressed bytes', flush=True)
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED, compresslevel=3) as z:
            for p, row in zip(files, rows):
                z.write(p, row['path'])
            z.writestr(PREFIX+'docs/FILE_INVENTORY.csv', inventory_data)
            z.writestr(PREFIX+'docs/FILE_MANIFEST.json', data)
        receipt = verify(temporary)
        temporary.replace(target)
        receipt.update(archive=name, bytes=target.stat().st_size)
        receipts.append(receipt)
        if not github:
            (GROUP/'docs/FILE_MANIFEST.json').write_bytes(data)
            (GROUP/'docs/FILE_INVENTORY.csv').write_bytes(inventory_data)
        print(json.dumps(receipt), flush=True)
    (OUT/'package_receipt.json').write_text(json.dumps(receipts, indent=2), encoding='utf-8')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    if args.verify:
        print(json.dumps(verify(args.verify), indent=2))
    else:
        main()
