import os
import sys
from docx.api import Document
import openpyxl
from shutil import copyfile

folder_path = '.'

# templates = os.fsencode(folder_path + '/templates')
# forms = os.fsencode(folder_path + '/forms')

templates = []
forms = []

alias_vals = {}
conflicts = {}
labels = []

for line in open(folder_path + "/labels.txt", "r"):
  labels.append(line)

def check_alias(text):
  for arg in labels:
    if (arg.strip().lower() == text.strip().lower()):
      return arg
  return False


def find_all(a_str, sub):
  start = 0
  while True:
    start = a_str.find(sub, start)
    if start == -1:
      return
    yield start
    start += len(sub)  # use start += 1 to find overlapping matches


def swap_text(paragraph):
  indicies = list(find_all(paragraph.text, '*'))
  if len(indicies) >= 2:
    for label in alias_vals.keys():
      if type(label) is str:
        for i in range(0, len(indicies) - 1):
          if label.lower().strip() == paragraph.text[(indicies[i] + 1):indicies[i + 1]].lower().strip():
            paragraph.text = paragraph.text[:indicies[i]] + \
                alias_vals[label] + paragraph.text[indicies[i + 1]:(len(paragraph.text) - 2)]

def get_files(dir, tab):
  for root, subdirs, files in os.walk(dir):
    if len(files) > 0:
      backup_path = os.path.join(root, 'backup')
      os.mkdir(backup_path)
      for file in files:
        path = os.path.join(root, file)
        copyfile(path, backup_path + '/' + file)
        tab.append(path)

def clone_values(doc):
  for table in doc.tables:
    for row_i in range(0, len(table.rows)):
      for col_i, cell in enumerate(table.row_cells(row_i)):
        check = check_alias(cell.text)  # standard table cell check
        if check != False:
          table.cell(row_i, col_i).text = alias_vals[check]
        else:
          for paragraph in cell.paragraphs:  # check for paragraphs in table cell
            swap_text(paragraph)

  for paragraph in doc.paragraphs:
    swap_text(paragraph)

get_files(sys.argv[1], forms)
for dir in sys.argv[2:]:
  get_files(dir, templates)

#pull values
# for form in os.listdir(forms):
#   form_name = os.fsdecode(form)
#   if form_name.endswith('.docx'):
#     doc = Document(folder_path + '/forms/' + form_name)
for form_dir in forms:
  if form_dir.endswith('.docx'):
    doc = Document(form_dir)
    for table in doc.tables:
      for i, row in enumerate(table.rows):
        check = check_alias(row.cells[0].text)
        if check != False:
          cell_text = row.cells[1].text
          if (check in alias_vals.keys()) and (alias_vals[check] != cell_text):
            if (check in conflicts.keys()) == False:
              conflicts[check] = [row.cells[1].text, alias_vals[check]]
            else:
              conflicts[check].append(row.cells[1].text)

          else:
            alias_vals[check] = cell_text

          # print(check, row.cells[1].text)

#resolve conflicting values
for label in conflicts:
  print("There's conflicting values for label " + label)
  for i, value in enumerate(conflicts[label]):
    print(str(i) + ") " + value)
  sys.stdout.flush()
  s = input("Select which value to use: ")
  print(s)
  sys.stdout.flush()
  alias_vals[label] = conflicts[label][int(s)]

#clone values
# for template in os.listdir(templates):
#   template_name = os.fsdecode(template)
#   if template_name.endswith('.docx') and template_name[0] != '~':
for template_dir in templates:
  if template_dir.endswith('.docx') and template_dir.find('~') == -1:
    # doc = Document(folder_path + '/templates/' + template_name)
    doc = Document(template_dir)
    clone_values(doc)
    for section in doc.sections:
      clone_values(section.header)
      clone_values(section.footer)
    doc.save(template_dir)
  # elif template_name.endswith('.xlsx'):
  elif template_dir.endswith('.xlsx'):
    wb = openpyxl.load_workbook(template_dir)
    for sheet_name in wb.sheetnames:
      sheet = wb[sheet_name]
      for row in sheet.iter_rows():
        for cell in row:
          cell_text = cell.value
          if (cell_text != 'None' and cell_text is not None):
            print(cell_text is None)
            for label in alias_vals:
              val = alias_vals[label]
              if type(label) is str:
                check = list(
                    find_all(cell_text.strip().lower(), label.strip().lower()))
                if len(check) > 0:
                  # print(cell_text)
                  if len(check) == 1:
                    if (check[0] == 0 and cell_text.strip().lower() == label.strip().lower()):
                      cell.value = val
                    elif check[0] != 0:
                      cell.value = cell_text[:check[0]] + \
                          val + cell_text[(len(val) + check[0]):]
                  else:
                    last_index = check[len(check) - 1]
                    cell.value = cell_text[:last_index] + \
                        val + cell_text[(len(val) + last_index):]
    wb.save(template_dir)

