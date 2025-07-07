from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

class TableStyleRemover(Treeprocessor):
    def run(self, root):
        for table in root.iter('table'):
            # Remove 'style' attribute from the table and all its descendants
            table.attrib['class'] = 'table table-hover table-striped table-bordered'
            for elem in table.iter():
                if 'style' in elem.attrib:
                    del elem.attrib['style']

class TableClassExtension(Extension):
    def extendMarkdown(self, md):
        md.treeprocessors.register(TableStyleRemover(md), 'tableclassadder', 15)

def makeExtension(**kwargs):
    return TableClassExtension(**kwargs)