import markdown
from markdown.inlinepatterns import SimpleTagInlineProcessor
from markdown.extensions import Extension

BOLD_RE = r'(\*\*|__)(.+?)\1'

class BoldClassInlineProcessor(SimpleTagInlineProcessor):
    def handleMatch(self, m, data):
        el, start, end = super().handleMatch(m, data)
        if el is not None:
            el.set('class', 'text-highlight')
        return el, start, end

class BoldClassExtension(Extension):
    def extendMarkdown(self, md):
        md.inlinePatterns.register(BoldClassInlineProcessor(BOLD_RE, 'strong'), 'strong', 175)

def makeExtension(**kwargs):
    return BoldClassExtension(**kwargs)
