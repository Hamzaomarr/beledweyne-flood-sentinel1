"""Move the 'Placeholders inserted' and 'Unresolved issues' sections out of the Methods scripts into a separate author-notes document."""
import re
D = r'.\scripts'
def read(n): return open(D + '\\' + n, encoding='utf-8-sig').read()
def write(n, t): open(D + '\\' + n, 'w', encoding='utf-8', newline='').write(t)

# paper-style script (25): cut the two sections, keep them to build the notes file
s = read('25_make_methods_paperstyle_docx.js')
a = s.index("K.push(H2('Placeholders inserted'));"); b = s.index('const doc = new Document')
chunk = s[a:b]
write('25_make_methods_paperstyle_docx.js', s[:a] + s[b:])
head = s[:s.index('const K = [];')]
notes = head + "const K = [];\nK.push(new Paragraph({ alignment: AlignmentType.LEFT, spacing: { line: 240, after: 200 }, children: [run('Author notes for the Methods', { bold: true })] }));\n" \
    "K.push(body('This file is for the authors and is not part of the manuscript. It lists what must still be supplied and what could not be settled. The section numbers refer to MANUSCRIPT_Methods_paperstyle.docx.'));\n" + chunk + \
    s[b:s.index('Packer.toBuffer')] + "Packer.toBuffer(doc).then(b => { fs.writeFileSync(path.join(BASE, 'METHODS_author_notes.docx'), b); console.log('written notes', b.length); });\n"
# the doc definition in 25 references K; keep it. Remove the trailing original Packer line if duplicated
notes = notes.replace("const doc = new Document({", "const doc = new Document({", 1)
write('28_make_author_notes_docx.js', notes)

# first Methods script (14): cut the same two sections
s = read('14_make_methods_docx.js')
a = s.index("K.push(H('Placeholders inserted'));"); b = s.index('const doc = new Document')
write('14_make_methods_docx.js', s[:a] + s[b:])
print('split done')
