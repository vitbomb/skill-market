from pathlib import Path
p=Path('revisao_artigo/convert_pdf.py')
s=p.read_text(encoding='utf-8-sig').replace('import sys','import sys, re')
a="html=re.sub(r'(<p>(?:(?!</p>).)*</p>)(<p class=\"note\">(?:(?!</p>).)*</p>)', r'<div style=\"page-break-inside:avoid\">\1\2</div>', html)\ncss += ' h2 {page-break-before: always;}'\n"
s=s.replace('story=fitz.Story(html=html,user_css=css)',a+'story=fitz.Story(html=html,user_css=css)')
s=s.replace("(root/'numbered.pdf').replace(output)","output=root/'numbered.pdf'")
p.write_text(s,encoding='utf-8')
