"""Export/recover a compatible rule handoff. No financial calculation."""
import argparse
import json
from pathlib import Path
from contracts.common import to_common,from_common

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--input',type=Path,required=True);parser.add_argument('--reverse',action='store_true');args=parser.parse_args()
    try:
        document=json.loads(args.input.read_text(encoding='utf-8-sig'))
        result=from_common(document) if args.reverse else to_common(document)
    except (ValueError,TypeError,OSError) as e:parser.exit(2,f'Invalid handoff: {e}\n')
    print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))
if __name__=='__main__':main()
