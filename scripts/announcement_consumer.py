# SPDX-License-Identifier: MIT
"""Bounded candidate announcement sidecar consumer; no PDF semantic certification."""
import argparse
import copy
import hashlib
import json
from pathlib import Path


def consume(sidecar, review, original_path, prospective=False):
    if sidecar.get('schema') != 'bjx-announcement-sidecar.v1':
        raise ValueError('unsupported candidate sidecar; not a shared standard')
    native = sidecar['native_payload']
    source = native['documents']['result']
    digest = hashlib.sha256(Path(original_path).read_bytes()).hexdigest()
    if digest != sidecar['sha256'] or digest != source['sha256']:
        raise ValueError('original file digest mismatch')
    if sidecar['official_url'] != source['url']:
        raise ValueError('official URL conflicts with native source')
    version = sidecar['source_version']['announcement_number']
    if version != source['announcement_number']:
        raise ValueError('source version conflicts with native source')
    if sidecar['publisher'] != native['issuer_name']:
        raise ValueError('publisher conflicts with native issuer')
    if sidecar['document_id'] != f"BSE:{native['security']}:{version}":
        raise ValueError('document identity conflict')
    for key in ('published_at', 'historical_available_at'):
        time = sidecar['times'][key]
        if time['value'] is None and not time.get('reason'):
            raise ValueError('unknown time needs a reason')
    if prospective:
        # This candidate adapter supports retrospective inspection only.
        raise ValueError('prospective use unsupported; no historical availability certification')
    if review.get('schema') != 'cn-market-rules.announcement-review/1':
        raise ValueError('unsupported rules review')
    if review['source_sha256'] != digest or review['source_version'] != version:
        raise ValueError('review binding conflicts with source digest/version')
    if review['document_id'] != sidecar['document_id']:
        raise ValueError('review document identity conflict')
    for key in review['reviewed_native_fields']:
        if review['reviewed_native_fields'][key] != native['fields'][key]:
            raise ValueError('reviewed field conflicts with native field')
        if native['fields'][key]['source_id'] != 'result':
            raise ValueError('this review covers result notice only')
    if review['rule_version_id'] is not None or review['qualification']['value'] is not None:
        raise ValueError('this notice review cannot select a rule version or certify qualification')
    return dict(schema='cn-market-rules.announcement-consumption/1',
                candidate_support='bjx-announcement-sidecar.v1; retrospective result notice only',
                source_sha256=digest, byte_binding='matched; not semantic verification',
                source_attachment=copy.deepcopy(sidecar), rules_review=copy.deepcopy(review),
                historical_available_at=copy.deepcopy(sidecar['times']['historical_available_at']),
                native_payload_preserved=True,
                semantic_status='caller supplied selected-page review; not inferred from hash')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sidecar', type=Path, required=True)
    parser.add_argument('--review', type=Path, required=True)
    parser.add_argument('--original', type=Path, required=True)
    parser.add_argument('--prospective', action='store_true')
    args = parser.parse_args()
    try:
        result = consume(json.loads(args.sidecar.read_text(encoding='utf-8')),
                         json.loads(args.review.read_text(encoding='utf-8')),
                         args.original, args.prospective)
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(2, f'Announcement consumption refused: {error}\n')
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
