import re

class MACMCheckException(Exception):
    def __init__(self, message):
        self.message = re.search(r'/\*(.*?)\*/', message, re.DOTALL)
        if self.message:
            self.message = self.message.group(1).strip()
        else:
            self.message = message
        self.message = "MACM Validation Error: " + self.message
        super().__init__(self.message)

    def __str__(self):
        return self.message