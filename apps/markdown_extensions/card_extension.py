from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
import xml.etree.ElementTree as ET

class CardTreeprocessor(Treeprocessor):
    def run(self, root):
        print(f"Running CardTreeprocessor on root: {root.tag}")
        new_root = ET.Element('div')  # Wrapper per tutti i contenuti
        current_card = None

        for child in list(root):
            print(f"Current child tag: {child.tag}")
            if child.tag in ['h1', 'h2']:
                # Inizia una nuova card
                current_card = ET.Element('div', {'class': 'card mb-3'})
                header = ET.SubElement(current_card, 'div', {'class': 'card-header'})
                header.append(child)  # sposta h1 dentro header
                body = ET.SubElement(current_card, 'div', {'class': 'card-body'})
                new_root.append(current_card)
            else:
                # Appendi al body dell’ultima card
                if current_card is not None:
                    body = current_card.find(".//div[@class='card-body']")
                    body.append(child)
                else:
                    new_root.append(child)

        return new_root

class CardExtension(Extension):
    def extendMarkdown(self, md):
        md.treeprocessors.register(CardTreeprocessor(md), 'cardtreeprocessor', 25)