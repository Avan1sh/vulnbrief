"""Parse the official Palo Alto advisory's actual product status table."""
import re
from bs4 import BeautifulSoup


def parse_palo_advisory(html, cve):
    soup=BeautifulSoup(html,'html.parser')
    headings=soup.find_all(['h1','h2','h3','h4'])
    title=next((h.get_text(' ',strip=True) for h in headings if cve in h.get_text()),None)
    if not title:
        raise ValueError('Vendor advisory identifier not found')
    status=next((h for h in headings if h.get_text(' ',strip=True).casefold()=='product status'),None)
    table=status.find_next('table') if status else None
    rows=[]
    if table:
        for row in table.find_all('tr'):
            cells=[cell.get_text(' ',strip=True) for cell in row.find_all('td')]
            if len(cells)==3:
                rows.append(dict(zip(('product','affected','unaffected'),cells)))
    if not rows:
        raise ValueError('Vendor version table unavailable; cannot infer affectedness')
    def section(name):
        heading=next((h for h in headings if h.get_text(' ',strip=True).casefold()==name.casefold()),None)
        content=[]
        if heading:
            for node in heading.next_siblings:
                if getattr(node,'name',None) in {'h1','h2','h3','h4'}:
                    break
                if hasattr(node,'get_text'):
                    content.append(node.get_text(' ',strip=True))
        return ' '.join(content)
    plain=soup.get_text(' ',strip=True)
    updated=re.search(r'Updated\s+(\d{4}-\d{2}-\d{2})',plain)
    published=re.search(r'Published\s+(\d{4}-\d{2}-\d{2})',plain)
    solution=section('Solution')
    fixed=[]
    for match in re.findall(r'\b\d+\.\d+\.\d+(?:-h\d+)?\b',solution):
        if match not in fixed:
            fixed.append(match)
    return {'cve_id':cve,'title':title,'published_at':published[1] if published else None,
            'updated_at':updated[1] if updated else None,'product_status':rows,
            'fixed_version_candidates':fixed[:40],
            'solution_excerpt':' '.join(solution.split()[:25]),
            'guidance_scope':'Vendor table and short solution excerpt; verify full advisory before operational changes',
            'metrics':[]}
