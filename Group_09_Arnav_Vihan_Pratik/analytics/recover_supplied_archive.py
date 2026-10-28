"""Recover complete selected local ZIP records into a NEW directory, checking CRC and sizes."""
from pathlib import Path,PurePosixPath
import argparse,struct,zlib,json,hashlib

def recover(source,destination):
    if destination.exists():raise ValueError('Choose a new destination; existing sources will never be overwritten')
    destination.mkdir(parents=True);blob=source.read_bytes();cursor=0;rows=[]
    allowed={'.gitignore','ACADEMIC_AND_INDUSTRY_STANDARDS_MANUAL.md','BRANCHING_GUIDE.md','CONTRIBUTING.md',
        'GRADING_RUBRIC_AND_EVALUATION_POLICY.md','README.md','requirements.txt','MDRIIA_Group_09_Technical_Dossier.docx'}
    while True:
        pos=blob.find(b'PK\x03\x04',cursor)
        if pos<0:break
        cursor=pos+4
        try:
            _,_,flags,method,_,_,crc,csize,usize,nlen,xlen=struct.unpack_from('<IHHHHHIIIHH',blob,pos)
            if not 0<nlen<2000:continue
            name=blob[pos+30:pos+30+nlen].decode('utf-8')
            path=PurePosixPath(name)
            if not path.parts or path.parts[0]!='NMIMS-MPSTME-MDRIIA-2026' or name.endswith('/'):continue
            rel=PurePosixPath(*path.parts[1:])
            if not rel.parts or any(part in {'.git','.venv','.project','__pycache__','..'} for part in rel.parts):continue
            if rel.parts[0] not in {'M20','Group_09_Arnav_Vihan_Pratik'} and str(rel) not in allowed:continue
            start=pos+30+nlen+xlen
            if method==8:
                decoder=zlib.decompressobj(-15);pieces=[];end=start;size=0
                while not decoder.eof:
                    chunk=blob[end:end+65536]
                    if not chunk:raise ValueError('Truncated DEFLATE stream')
                    part=decoder.decompress(chunk);pieces.append(part);size+=len(part);end+=len(chunk)
                    if size>100_000_000:raise ValueError('Selected entry exceeds size limit')
                raw=b''.join(pieces);consumed=end-start-len(decoder.unused_data)
            elif method==0:raw=blob[start:start+csize];consumed=csize
            else:raise ValueError('Unsupported selected compression')
            if flags&8:
                end=start+consumed
                if blob[end:end+4]==b'PK\x07\x08':end+=4
                crc,csize,usize=struct.unpack_from('<III',blob,end)
            assert (zlib.crc32(raw)&0xffffffff,consumed,len(raw))==(crc,csize,usize),'CRC/size mismatch'
            target=destination/str(rel)
            assert target.resolve().is_relative_to(destination.resolve()),'Unsafe path'
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            rows.append({'path':rel.as_posix(),'bytes':len(raw),'crc32':f'{crc:08x}','sha256':hashlib.sha256(raw).hexdigest(),'status':'RECOVERED_CRC_AND_SIZE_VERIFIED'})
        except (UnicodeDecodeError,struct.error):continue
    (destination/'recovered_manifest.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    return {'selected_complete_entries':len(rows),'archive_bytes':len(blob),'archive_sha256':hashlib.sha256(blob).hexdigest()}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('new_destination',type=Path);a=p.parse_args()
    print(json.dumps(recover(a.archive,a.new_destination),indent=2))
