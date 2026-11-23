#!/usr/bin/env python3
"""Cross-check REA/Craft root inventory hashes against one locked source."""
import argparse
import gzip
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MAX_BYTES=128*1024*1024


def read_json(path):
    opener=gzip.open if path.suffix=='.gz' else open
    with opener(path,'rb') as stream:
        data=stream.read(MAX_BYTES+1)
    if len(data)>MAX_BYTES:
        raise ValueError('Evidence exceeds 128 MiB expanded limit')
    return json.loads(data)


def verify_tools(source_id, craft_path, rea_path, root=ROOT):
    source=next((s for s in json.loads((root/'sources.lock.json').read_text())['sources'] if s['id']==source_id),None)
    if source is None:
        raise ValueError('Unknown locked source')
    with gzip.open(root/'research/inventories'/f'{source_id}.jsonl.gz','rt') as stream:
        rows=[json.loads(line) for line in stream]
    expected={r['path']:r for r in rows if r['kind']!='submodule'}
    craft,rea=read_json(craft_path),read_json(rea_path)
    if craft['subject']['sha256']!=source['archive_sha256'] or rea['subject']['digest']['sha256']!=source['archive_sha256']:
        raise ValueError('Tool evidence targets another snapshot')
    entries=[e for e in craft['result']['entries'] if e['depth']==0]
    indexed={e['path']:e for e in entries}
    if len(entries)!=len(indexed) or indexed.keys()!=expected.keys():
        raise ValueError('Craft root membership mismatch')
    for name,row in expected.items():
        if indexed[name].get('sha256')!=row['sha256']:
            raise ValueError('Craft root hash mismatch: '+name)
    inventory=next((s['evidence']['normalized_result'] for s in rea['normalized_result']['substeps'] if s['operation']=='inventory_artifact' and s['status']=='completed'),None)
    if inventory is None:
        raise ValueError('REA completed inventory not found')
    anchors=[o for o in inventory['occurrences'] if o['parent_occurrence_id'] is None]
    if len(anchors)!=1:
        raise ValueError('REA root occurrence is ambiguous')
    entries=[o for o in inventory['occurrences'] if o['parent_occurrence_id']==anchors[0]['occurrence_id']]
    occurrences={o['logical_path']:o for o in entries}
    if len(entries)!=len(occurrences) or occurrences.keys()!=expected.keys():
        raise ValueError('REA root membership mismatch')
    nodes={n['artifact_id']:n for n in inventory['nodes']};matched=0;unhashed=[]
    for name,row in expected.items():
        entry=occurrences[name]
        if entry['artifact_id'] is None or entry['hash_status']!='verified':
            unhashed.append(name)
        elif nodes[entry['artifact_id']]['sha256']!=row['sha256']:
            raise ValueError('REA root hash mismatch: '+name)
        else:
            matched+=1
    return {'source':source_id,'commit':source['commit'],'archive_sha256':source['archive_sha256'],'root_files':len(expected),
            'craft_root_hashes_matched':len(expected),'rea_root_hashes_matched':matched,'rea_unhashed_root_entries':unhashed,
            'craft_coverage':craft['coverage'],'rea_coverage':inventory['coverage'],'gitlinks_not_collected':source['unfetched_gitlinks'],
            'limitation':'Root inventory agreement only; not semantic coverage, tool authenticity, nested archive coverage or runtime verification.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source');parser.add_argument('--craft',type=Path,required=True);parser.add_argument('--rea',type=Path,required=True)
    args=parser.parse_args()
    try:
        result=verify_tools(args.source,args.craft,args.rea)
    except (ValueError,OSError,KeyError,TypeError) as error:
        parser.exit(2,str(error)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
