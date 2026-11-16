"""Optional audit-friendly dataset export with provenance JSON."""
from pathlib import Path
import argparse,json
from lunaris_climate.sources import fetch_training_data

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--start",required=True)
    p.add_argument("--end",required=True)
    p.add_argument("--out",default="data/dubai_training.csv")
    a=p.parse_args()
    f, meta=fetch_training_data(a.start,a.end)
    dest=Path(a.out)
    dest.parent.mkdir(parents=True,exist_ok=True)
    f.to_csv(dest,index=False)
    dest.with_suffix(".provenance.json").write_text(json.dumps(meta,indent=2))
    print(f"Saved {len(f)} provider-derived hourly rows to {dest}")
if __name__=="__main__": main()
