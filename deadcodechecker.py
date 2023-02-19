import io
import sys
import re

from vulture.core import Vulture
from contextlib import redirect_stdout


class DeadCodeChecker():

    def __init___(self, text):
        self.vultureObject = Vulture()
        self.vultureObject.scan(text)

    def getString(self):
        return self.getOutput().replace(':', '')

    def getList(self):
        return self.getOutput().replace(':', '').split('\n')

    def getOutput(self):
        with io.StringIO() as buf, redirect_stdout(buf):
            self.vultureObject.report()
            output = buf.getvalue()
        return output
