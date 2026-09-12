"""Check provenance, measurements, exports and figure embedding contracts."""
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
import matplotlib
import numpy
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
NAMES = ['fig1_agent_architecture','fig2_gb1_convergence','fig3_epistasis_landscape',
         'fig4_aav_exploration_tax','fig5_five_machine_rsi']

def verify():
    source_dir = ROOT / 'artifacts/figures_data'
    provenance = json.loads((source_dir/'provenance.json').read_text())
    points = 0
    for key, pin in provenance.items():
        raw = (source_dir/f'{key}.json').read_bytes()
        assert hashlib.sha256(raw).hexdigest() == pin['snapshot_sha256'], key
        d = json.loads(raw)
        assert d['provenance']['sha256'] == pin['sha256']
        series = [(v['rounds'],d['summary'][k]) for k,v in d['strategies'].items()] if 'strategies' in d else [(d['rounds'], d['summary'])]
        for rows, summary in series:
            spent = 0
            curve = []
            for i,r in enumerate(rows,1):
                assert r['round'] == i
                assert r['n_nominated'] > 0
                spent += r['n_nominated']
                assert spent == r['spent_after']
                curve.append(r['cum_top10_max'])
                points += 1
            assert curve == sorted(curve)
            assert curve == summary['cum_top10_max_curve']
            assert curve[-1] == summary['final_cum_top10_max']
            if 'budget_spent' in d: assert spent == d['budget_spent']
    inventory=[]
    for name in NAMES:
        p=ROOT/'reports/figures'/f'{name}.png'
        with Image.open(p) as im:
            im.load()
            assert min(im.info['dpi']) >= 299.99, (name, im.info)
            assert min(im.size) >= 1500
            assert im.getextrema()[0][0] < 250  # Nonempty image.
            inventory.append({'file':str(p.relative_to(ROOT)), 'pixels':im.size, 'dpi':im.info['dpi'],
                              'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
        p=p.with_suffix('.svg')
        svg=ET.parse(p).getroot()
        assert svg.tag == '{http://www.w3.org/2000/svg}svg'
        assert len(svg.findall('.//{http://www.w3.org/2000/svg}path')) > 0
        assert not svg.findall('.//{http://www.w3.org/2000/svg}image'), 'Expected vector, not embedded raster'
        inventory.append({'file':str(p.relative_to(ROOT)), 'viewBox':svg.attrib['viewBox'],
                          'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    class Images(HTMLParser):
        def __init__(self): super().__init__(); self.sources=[]
        def handle_starttag(self,tag,attrs):
            if tag=='img': self.sources.append(dict(attrs).get('src',''))
    report=ROOT/'reports/scientific_report_v1.0.md'
    markdown_links=re.findall(r'!\[[^\]]*\]\(([^)]+)\)',report.read_text())
    html=Images();html.feed((ROOT/'reports/explainer_for_humans.html').read_text())
    for links in (markdown_links,html.sources):
        for name in NAMES:
            link=f'figures/{name}.png'
            assert links.count(link) == 1, (name,links)
            assert (report.parent/link).is_file()
    result={'status':'passed','metric_snapshots':len(provenance),'verified_round_endpoints':points,
            'embedded_figures_per_document':5, 'documents':['reports/scientific_report_v1.0.md','reports/explainer_for_humans.html'],
            'environment':{'python':sys.version.split()[0],'matplotlib':matplotlib.__version__,'numpy':numpy.__version__},
            'files':inventory}
    (ROOT/'reports/figures/verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='files'},indent=2))
    return result

if __name__ == '__main__': verify()
