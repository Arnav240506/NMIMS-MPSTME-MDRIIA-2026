"""Audit the completed form against its exact supplied template and rendered PDF.

--reviewed-pages records a human/agent visual review; it does not perform one.
Rebuilding the DOCX resets the receipt to BUILT_PENDING_RENDER.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, zipfile
import xml.etree.ElementTree as ET
from pypdf import PdfReader

GROUP = Path(__file__).resolve().parents[1]
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{'+NS['w']+'}'

def canonical(e):
    return ET.canonicalize(ET.tostring(e, encoding='unicode'))

def protected(t):
    return t.startswith(('M09.S6.', 'M09.SIGN.', 'M09.S5.peer_')) or (
        t.startswith('M09.S2.script') and t.endswith(('.author', '.authorship')))

def sha(data):
    return hashlib.sha256(data).hexdigest()

def verify(reviewed_pages=None):
    docs = GROUP/'docs'
    original = GROUP/'archive/dossier_original_template.docx'
    target = docs/'MDRIIA_Group_09_Technical_Dossier.docx'
    pdf = docs/'MDRIIA_Group_09_Technical_Dossier.pdf'
    receipt_path = docs/'provenance/dossier_edit_receipt.json'
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    assert sha(original.read_bytes()) == receipt['input_sha256']
    assert sha(target.read_bytes()) == receipt['output_sha256']
    with zipfile.ZipFile(original) as z:
        assert z.testzip() is None
        before = {n: z.read(n) for n in z.namelist()}
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        after = {n: z.read(n) for n in z.namelist()}
    intentional = {'word/document.xml', 'word/_rels/document.xml.rels',
                   '[Content_Types].xml', 'docProps/core.xml'}
    assert all(after[n] == data for n, data in before.items() if n not in intentional)
    old = ET.fromstring(before['word/document.xml'])
    new = ET.fromstring(after['word/document.xml'])
    def controls(root):
        return {s.find('w:sdtPr/w:tag', NS).get(W+'val'): s
                for s in root.findall('.//w:sdt', NS)}
    oc, nc = controls(old), controls(new)
    assert len(oc) == len(nc) == 212 and list(oc) == list(nc)
    assert all(canonical(nc[t].find('w:sdtPr', NS)) ==
               canonical(s.find('w:sdtPr', NS)) for t, s in oc.items())
    kept = [t for t in oc if protected(t)]
    assert len(kept) == 66
    assert all(canonical(oc[t]) == canonical(nc[t]) for t in kept)
    assert len(receipt['filled_controls']) == 146
    for t, value in receipt['filled_controls'].items():
        text = ''.join(n.text or '' for n in nc[t].findall('.//w:t', NS))
        assert text == value, t
        options = nc[t].findall('w:sdtPr/w:dropDownList/w:listItem', NS)
        if options:
            assert value in [x.get(W+'displayText') for x in options], t
    # Original source signature cells have no tagged control: preserve separately.
    ot = old.findall('w:body/w:tbl', NS)
    nt = new.findall('w:body/w:tbl', NS)
    assert len(ot) == 29 and len(nt) > 29
    for row in range(1, 4):
        old_cell = ot[28].findall('w:tr', NS)[row].findall('w:tc', NS)[4]
        new_cell = nt[28].findall('w:tr', NS)[row].findall('w:tc', NS)[4]
        assert canonical(old_cell) == canonical(new_cell)
    reader = PdfReader(pdf)
    count = len(reader.pages)
    texts = [p.extract_text() or '' for p in reader.pages]
    assert count == 18 and all(len(t.strip()) > 100 for t in texts)
    full = '\n'.join(texts)
    assert all(f'Annex A{i} ' in full for i in range(1, 11))
    assert all(x in full for x in ['70362400067', '70362400086', '70362300032'])
    if reviewed_pages is not None:
        assert reviewed_pages == count
        receipt.update(status='PASS', pdf_pages=count, pdf_sha256=sha(pdf.read_bytes()),
                       all_pages_visually_reviewed=True,
                       reviewed_utc=datetime.now(timezone.utc).isoformat(),
                       renderer='Microsoft Word desktop PDF export; Poppler PNG review',
                       layout_repairs=['Left-aligned indented source code',
                                       'Unclipped plot titles and effort-axis units'],
                       unchanged_signature_cells=3)
        receipt_path.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    else:
        assert receipt['status'] == 'PASS'
        assert receipt['pdf_sha256'] == sha(pdf.read_bytes())
        assert receipt['all_pages_visually_reviewed']
    result = {'status': 'PASS', 'pages': count, 'controls_preserved': 212,
              'technical_fields_filled': 146, 'protected_fields_unchanged': 66,
              'signature_cells_unchanged': 3, 'original_unrelated_parts_identical': True,
              'dropdown_values_valid': True, 'docx_sha256': sha(target.read_bytes()),
              'pdf_sha256': sha(pdf.read_bytes())}
    (docs/'provenance/dossier_validation.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--reviewed-pages', type=int)
    args = parser.parse_args()
    print(json.dumps(verify(args.reviewed_pages), indent=2))
