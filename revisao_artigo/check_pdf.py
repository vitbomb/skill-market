import sys, shutil
from pathlib import Path
sys.path.insert(0,str(Path('revisao_artigo/pdf_deps').resolve()))
import pymupdf as fitz
root=Path('revisao_artigo')
output=root/'Apontamentos_SkillMarket_Coloridos.pdf'
shutil.copyfile(root/'numbered.pdf',output)
doc=fitz.open(output)
print('pages',len(doc),'notes',sum(p.get_text().count('Conferência:') for p in doc))
for i in [0,len(doc)//2,len(doc)-1]:
 doc[i].get_pixmap(matrix=fitz.Matrix(1,1)).save(str(root/('preview_'+str(i+1)+'.png')))
