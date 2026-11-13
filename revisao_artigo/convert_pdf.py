import sys, re
from pathlib import Path
sys.path.insert(0,str(Path('revisao_artigo/pdf_deps').resolve()))
import pymupdf as fitz
root=Path('revisao_artigo')
html=(root/'Apontamentos_SkillMarket_Conferidos.html').read_text(encoding='utf-8-sig')
html=html.replace('font-size:16px','font-size:11pt').replace('margin:40px auto','margin:0').replace('padding:0 28px','padding:0').replace('font-size:14px','font-size:9pt')
css='body {font-family: sans-serif;} h1,h2 {page-break-after: avoid;} p {orphans:3; widows:3;}'
html=re.sub(r'(<p>(?:(?!</p>).)*</p>)(<p class="note">(?:(?!</p>).)*</p>)', r'<div style="page-break-inside:avoid"></div>', html)
css += ' h2 {page-break-before: always;}'
story=fitz.Story(html=html,user_css=css)
output=root/'Apontamentos_SkillMarket_Conferidos.pdf'
writer=fitz.DocumentWriter(str(output))
page=fitz.paper_rect('a4')
area=page+(42,40,-42,-42)
more=True
while more:
 device=writer.begin_page(page)
 more,filled=story.place(area)
 story.draw(device)
 writer.end_page()
writer.close()
doc=fitz.open(output)
for i in range(len(doc)):
 p=doc[i]
 p.insert_text((page.width-64,page.height-22),str(i+1),fontsize=9,color=(0.3,0.3,0.3))
doc.save(str(root/'numbered.pdf'))
doc.close()
output=root/'numbered.pdf'
doc=fitz.open(output)
text=''.join(p.get_text() for p in doc)
print('pages',len(doc),'notes',text.count('Conferência:'))
for i in [0,len(doc)//2,len(doc)-1]:
 doc[i].get_pixmap(matrix=fitz.Matrix(1,1)).save(str(root/('preview_'+str(i+1)+'.png')))
print(str(output.resolve()))
