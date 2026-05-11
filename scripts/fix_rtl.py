import zipfile
import re

backup = r'C:\Users\urial\OneDrive\Dev\phd_research_agent\doctoral_proposal_geopolitical_hebrew_backup.docx'
output = r'C:\Users\urial\OneDrive\Dev\phd_research_agent\doctoral_proposal_geopolitical_hebrew_final.docx'

with zipfile.ZipFile(backup, 'r') as z:
    all_files = {name: z.read(name) for name in z.namelist()}

content = all_files['word/document.xml'].decode('utf-8')

def apply(xml, old, new, label):
    if old in xml:
        print(f"  OK: {label}")
        return xml.replace(old, new)
    else:
        print(f"  NOT FOUND: {label}")
        return xml

# ── Step 1: RTL paragraphs ─────────────────────────────────────────────────
def add_bidi(xml):
    def r(m):
        p = m.group(0)
        return p if '<w:bidi' in p else p.replace('<w:pPr>', '<w:pPr><w:bidi/>', 1)
    return re.sub(r'<w:pPr>.*?</w:pPr>', r, xml, flags=re.DOTALL)

print("Step 1: RTL paragraphs")
content = add_bidi(content)

# ── Step 2: Single-run citations (simple text replacement in <w:t>) ─────────
print("\nStep 2: Single-run citations")
single = [
    (' (Bebbington et al., 2011)', ' (2011)',                               'Bebbington'),
    (' (Prem et al., 2020)',       ' (2020)',                               'Prem'),
    (' (Gallwey et al., 2020)',    ' (2020)',                               'Gallwey single'),
    (' (Willard et al., 2020)',    ' (2020)',                               'Willard single'),
    (' (Shen et al., 2023)',       ' (2023)',                               'Shen'),
    (' (Lu et al., 2021)',         ' (2021)',                               'Lu'),
    (' (Bueno de Mesquita et al. 1985) ', ' (1985) ',                      'Bueno de Mesquita'),
    (' (Khorshidi et al. 2024). ', ' (2024). ',                            'Khorshidi'),
    (' (Marcus et al. 2020) ',    ' (2020) ',                              'Marcus'),
    (' (Willard et al. 2020; Shen et al. 2023; Lu et al. 2021; Shuai et al. 2024) ',
     ' (2020; 2023; 2021; 2024) ',                                          'Willard multi'),
]
for old, new, label in single:
    content = apply(content, old, new, label)

# ── Step 3: Split-run citations (raw XML replacement) ──────────────────────
print("\nStep 3: Split-run citations")

# Balaniuk single: ' (' + 'Balaniuk' + ' et al., 2020)'
content = apply(content,
    '<w:t xml:space="preserve"> (</w:t></w:r><w:proofErr w:type="spellStart"/>'
    '<w:r><w:rPr><w:b/><w:bCs/></w:rPr><w:t>Balaniuk</w:t></w:r>'
    '<w:proofErr w:type="spellEnd"/><w:r><w:rPr><w:b/><w:bCs/></w:rPr>'
    '<w:t xml:space="preserve"> et al., 2020)</w:t></w:r>',
    '<w:t xml:space="preserve"> (2020)</w:t></w:r>',
    'Balaniuk single')

# Lambin single: '(Lambin & ' + 'Meyfroidt' + ', 2011)'
content = apply(content,
    '<w:t xml:space="preserve"> (Lambin &amp; </w:t></w:r><w:proofErr w:type="spellStart"/>'
    '<w:r><w:rPr><w:b/><w:bCs/></w:rPr><w:t>Meyfroidt</w:t></w:r>'
    '<w:proofErr w:type="spellEnd"/><w:r><w:rPr><w:b/><w:bCs/></w:rPr>'
    '<w:t>, 2011)</w:t></w:r>',
    '<w:t xml:space="preserve"> (2011)</w:t></w:r>',
    'Lambin single')

# Lambin multi: '(Lambin & ' + 'Meyfroidt' + ' 2011; Bebbington...'
content = apply(content,
    '<w:t xml:space="preserve"> (Lambin &amp; </w:t></w:r><w:proofErr w:type="spellStart"/>'
    '<w:r><w:t>Meyfroidt</w:t></w:r>'
    '<w:proofErr w:type="spellEnd"/><w:r>'
    '<w:t xml:space="preserve"> 2011; Bebbington et al. 2011; Prem et al. 2020) </w:t></w:r>',
    '<w:t xml:space="preserve"> (2011; 2011; 2020) </w:t></w:r>',
    'Lambin multi')

# Gallwey multi: '(Gallwey et al. 2020; ' + 'Balaniuk' + ' et al. 2020; Usmanov...'
content = apply(content,
    '<w:t xml:space="preserve"> (Gallwey et al. 2020; </w:t></w:r><w:proofErr w:type="spellStart"/>'
    '<w:r><w:t>Balaniuk</w:t></w:r>'
    '<w:proofErr w:type="spellEnd"/><w:r>'
    '<w:t xml:space="preserve"> et al. 2020; Usmanov et al. 2021) </w:t></w:r>',
    '<w:t xml:space="preserve"> (2020; 2020; 2021) </w:t></w:r>',
    'Gallwey multi')

# Bawa: '-ML (' + 'בעקבות' + ' Bawa et al. 2025)'
content = apply(content,
    '<w:t>-ML (</w:t></w:r><w:proofErr w:type="spellStart"/>'
    '<w:r><w:t>בעקבות</w:t></w:r>'
    '<w:proofErr w:type="spellEnd"/><w:r>'
    '<w:t xml:space="preserve"> Bawa et al. 2025) </w:t></w:r>',
    '<w:t xml:space="preserve">-ML (בעקבות, 2025) </w:t></w:r>',
    'Bawa')

# ── Save ───────────────────────────────────────────────────────────────────
all_files['word/document.xml'] = content.encode('utf-8')
with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as z:
    for name, data in all_files.items():
        z.writestr(name, data)

print(f"\nDone! Open: {output}")
