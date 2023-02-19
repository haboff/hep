import os
import sys
import platform
from PyQt5.QtWidgets import QAction

from PyQt5 import Qsci
from PyQt5.Qsci import QsciScintilla, QsciLexerPython, QsciAPIs
from PyQt5.QtGui import QFont, QFontMetrics, QColor
from PyQt5.Qt import Qt

import re

from runthread import RunThread
from configuration import Configuration

import random
import time

#######################################

class PythonLexer(QsciLexerPython):

    def __init__(self):
        super().__init__()

        def keywords(self, index):
            if index == 1:
                return 'self ' + ' super ' + QsciLexerPython.keywords(self, index)
                return QsciLexerPython.keywords(self, index)




######################################


class CodeEditor(QsciScintilla):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.filename = None
        self.fileBrowser = None
        self.mainWindow = parent
        self.debugging = False

        c = Configuration()
        self.pointSize = int(c.getFontSize())
        self.tabWidth = int(c.getTab())

        # Scrollbars
        scrollBarStyleSheet = """border: 20px solid black;
        background-color: %s;
        alternate-background-color: #FFFFFF;"""

        self.verticalScrollBar().setStyleSheet(scrollBarStyleSheet % "")
        self.horizontalScrollBar().setStyleSheet(scrollBarStyleSheet % "purple")


        # matched / unmatched brace color ...
        self.setMatchedBraceBackgroundColor(QColor('#232323'))
        self.setMatchedBraceForegroundColor(QColor('dark'))
        self.setUnmatchedBraceBackgroundColor(QColor('#0000s00'))
        self.setUnmatchedBraceForegroundColor(QColor('red'))

        self.setBraceMatching(QsciScintilla.SloppyBraceMatch)

        # edge mode ... line at 79 characters
        self.setEdgeColumn(79)
        self.setEdgeMode(1)
        self.setEdgeColor(QColor('white'))

        # Set the default font
        self.font = QFont()

        system = platform.system().lower()
        self.font.setFamily(('Consolas' if system == 'windows' else 'Monospace'))
        self.font.setFixedPitch(True)
        self.font.setPointSize(self.pointSize)
        
        self.setFont(self.font)
        self.setMarginsFont(self.font)


        # Margin 0 is used for line numbers
        fontmetrics = QFontMetrics(self.font)
        self.setMarginsFont(self.font)
        self.setMarginWidth(0, fontmetrics.width("00000") + 5)
        self.setMarginLineNumbers(0, True)
        self.setMarginsBackgroundColor(QColor("#000000"))
        self.setMarginsForegroundColor(QColor("#FFFFFF"))

        # Margin 1 for breakpoints
        self.setMarginSensitivity(1, True)
        self.markerDefine(QsciScintilla.RightArrow, 8)
        self.setMarkerBackgroundColor(QColor('#FF0000'), 8)

        # variable for breakpoint
        self.breakpoint = False
        self.breakpointLine = None

        # FoldingBox
        self.setFoldMarginColors(QColor('dark'), QColor('dark'))

        # CallTipBox
        self.setCallTipsForegroundColor(QColor('#FFFFFF'))
        self.setCallTipsBackgroundColor(QColor('#282828'))
        self.setCallTipsHighlightColor(QColor('#3b5784'))
        self.setCallTipsStyle(QsciScintilla.CallTipsContext)
        self.setCallTipsPosition(QsciScintilla.CallTipsBelowText)
        self.setCallTipsVisible(-1)

        # change caret's color
        self.SendScintilla(QsciScintilla.SCI_SETCARETFORE, QColor('#98fb98'))
        self.setCaretWidth(4)

        # tab Width
        self.setIndentationsUseTabs(False)
        self.setTabWidth(self.tabWidth)
        # use whitespaces instead tabs
        self.SendScintilla(QsciScintilla.SCI_SETUSETABS, False)
        self.setAutoIndent(True)
        self.setTabIndents(True)

        # BackTab
        self.setBackspaceUnindents(True)

        # Current line visible with special background color or not :)
        # self.setCaretLineVisible(False)
        # self.setCaretLineVisible(True)
        # self.setCaretLineBackgroundColor(QColor("#020202"))
        self.setMinimumSize(300, 300)

        # get style
        self.style = None

        # Call the Color-Function: ...
        self.setPythonStyle()

        # self.SendScintilla(QsciScintilla.SCI_SETHSCROLLBAR, 0)

        # Contextmenu
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        undoAction = QAction("Undo", self)
        undoAction.triggered.connect(self.undoContext)
        redoAction = QAction("Redo", self)
        redoAction.triggered.connect(self.redoContext)
        sepAction1 = QAction("", self)
        sepAction1.setSeparator(True)
        cutAction = QAction("Cut", self)
        cutAction.triggered.connect(self.cutContext)
        copyAction = QAction("Copy", self)
        copyAction.triggered.connect(self.copyContext)
        pasteAction = QAction("Paste", self)
        pasteAction.triggered.connect(self.pasteContext)
        sepAction2 = QAction("", self)
        sepAction2.setSeparator(True)
        sepAction3 = QAction("", self)
        sepAction3.setSeparator(True)
        selectAllAction = QAction("Select All", self)
        selectAllAction.triggered.connect(self.getContext)
        sepAction4 = QAction("", self)
        sepAction4.setSeparator(True)
        breakpointAction = QAction("Run until Breakpoint", self)
        breakpointAction.triggered.connect(self.breakpointContext)
        terminalAction = QAction("Open Terminal", self)
        terminalAction.triggered.connect(self.termContext)

        self.addAction(undoAction)
        self.addAction(redoAction)
        self.addAction(sepAction1)
        self.addAction(cutAction)
        self.addAction(copyAction)
        self.addAction(pasteAction)
        self.addAction(sepAction2)
        self.addAction(selectAllAction)
        self.addAction(sepAction3)
        self.addAction(breakpointAction)
        self.addAction(sepAction4)
        self.addAction(terminalAction)

        # signals
        self.SCN_FOCUSIN.connect(self.onFocusIn)
        self.textChanged.connect(self.onTextChanged)
        self.marginClicked.connect(self.onMarginClicked)

    def onFocusIn(self):
        self.mainWindow.refresh(self)

    def onTextChanged(self):
        notebook = self.mainWindow.notebook
        textPad = notebook.currentWidget()
        index = notebook.currentIndex()

        if self.debugging is True:
            self.mainWindow.statusBar.showMessage(
            'remember to update CodeView if you delete or change lines in CodeEditor !', 3000)

        if textPad == None:
            return

        
    def onMarginClicked(self, margin, line, modifiers):
        if self.markersAtLine(line) != 0:
            self.markerDelete(line, 8)
            self.breakpoint = False
            self.breakpointLine = None
            self.mainWindow.statusBar.showMessage('Breakpoint removed', 3000)
        else:
            self.markerAdd(line, 8)
            self.breakpoint = True
            self.breakpointLine = line + 1
            self.mainWindow.statusBar.showMessage('Breakpoint set on line ' + str(self.breakpointLine), 3000)

    def checkPath(self, path):
        if '\\' in path:
            path = path.replace('\\', '/')
        return path

    def undoContext(self):
        self.resetBreakpoint()
        self.undo()

    def redoContext(self):
        self.resetBreakpoint()
        self.redo()

    def cutContext(self):
        self.resetBreakpoint()
        self.cut()

    def copyContext(self):
        self.resetBreakpoint()
        self.copy()

    def pasteContext(self):
        self.resetBreakpoint()
        self.paste()

    def getContext(self):
        self.selectAll()

    def breakpointContext(self):
        c = Configuration()
        system = c.getSystem()

        if self.breakpointLine:
            code = self.text(0, self.breakpointLine)
            randomNumber = random.SystemRandom()
            number = randomNumber.randint(0, sys.maxsize)
            filename = 'temp_file_' + str(number) + '.py'

        try:
            with open(filename, 'w') as f:
                f.write(code)
                command = c.getRun(system).format(filename)
                thread = RunThread(command)
                thread.start()

        except Exception as e:
            print(str(e))

        finally:
            time.sleep(2)
            os.remove(filename)

    def termContext(self):
        c = Configuration()
        system = c.getSystem()
        command = c.getTerminal(system)

        thread = RunThread(command)
        thread.start()

    def getLexer(self):
        return self.lexer

    def setPythonStyle(self):
        self.style = 'Python'

        # Set Python lexer
        self.setAutoIndent(True)

        # self.lexer = QsciLexerPython()
        self.lexer = PythonLexer()
        self.lexer.setFont(self.font)
        self.lexer.setFoldComments(True)

        # set Lexer
        self.setLexer(self.lexer)

        self.setCaretLineBackgroundColor(QColor("#344c4c"))
        self.lexer.setDefaultPaper(QColor("black"))
        self.lexer.setDefaultColor(QColor("white"))
        self.lexer.setColor(QColor('white'), 0)  # default
        self.lexer.setPaper(QColor('black'), -1)  # default -1 vor all styles
        self.lexer.setColor(QColor('gray'), PythonLexer.Comment)  # = 1
        self.lexer.setColor(QColor('orange'), 2)   # Number = 2
        self.lexer.setColor(QColor('lightblue'), 3)   # DoubleQuotedString
        self.lexer.setColor(QColor('lightblue'), 4)   # SingleQuotedString
        self.lexer.setColor(QColor('#33cccc'), 5)   # Keyword
        # TripleSingleQuotedString
        self.lexer.setColor(QColor('lightblue'), 6)
        # TripleDoubleQuotedString
        self.lexer.setColor(QColor('lightblue'), 7)
        self.lexer.setColor(QColor('#ffff00'), 8)   # ClassName
        self.lexer.setColor(QColor('#ffff66'), 9)   # FunctionMethodName
        self.lexer.setColor(QColor('white'), 10)   # Operator
        self.lexer.setColor(QColor('white'), 11)   # Identifier
        self.lexer.setColor(QColor('gray'), 12)   # CommentBlock
        self.lexer.setColor(QColor('#ff471a'), 13)   # UnclosedString
        self.lexer.setColor(QColor('gray'), 14)   # HighlightedIdentifier
        self.lexer.setColor(QColor('#5DD3AF'), 15)   # Decorator
        self.setPythonAutocomplete()
        self.setFold()

    def setPythonAutocomplete(self):

        self.autocomplete = QsciAPIs(self.lexer)
        self.keywords = self.lexer.keywords(1)

        self.keywords = self.keywords.split(' ')

        for word in self.keywords:
            self.autocomplete.add(word)

        self.autocomplete.add('super')
        self.autocomplete.add('self')
        self.autocomplete.add('__name__')
        self.autocomplete.add('__main__')
        self.autocomplete.add('__init__')
        self.autocomplete.add('__str__')
        self.autocomplete.add('__repr__')

        self.autocomplete.prepare()

        # Set the length of the string before the editor tries to autocomplete
        self.setAutoCompletionThreshold(3)

        # Tell the editor we are using a QsciAPI for the autocompletion
        self.setAutoCompletionSource(QsciScintilla.AcsAPIs)

        self.updateAutoComplete()
    def setFold(self):
        
        x = self.FoldStyle(5)
        
        if not x:
            self.foldAll(False)
        else:
            self.setFolding(x)

    def unsetFold(self):
        self.setFolding(0)

    def keyReleaseEvent(self, e):
        text = self.text()
        self.updateCodeView(text)

        if e.key() == Qt.Key_Return:
            self.updateAutoComplete()
        elif e.key() == Qt.Key_Backspace:
            self.resetBreakpoint()
            self.updateCodeView(text)

    def resetBreakpoint(self):
        self.markerDeleteAll()
        self.breakpoint = False
        self.breakpointLine = None

    def updateCodeView(self, text=''):
        codeView = self.mainWindow.codeView
        codeViewDict = codeView.makeDictForCodeView(text)
        codeView.updateCodeView(codeViewDict)

    def updateAutoComplete(self, text=None):
        self.autocomplete = QsciAPIs(self.lexer)  # clear all

        self.keywords = self.lexer.keywords(1)
        self.keywords = self.keywords.split(' ')

        for word in self.keywords:
            self.autocomplete.add(word)

        self.autocomplete.add('super')
        self.autocomplete.add('self')
        self.autocomplete.add('__name__')
        self.autocomplete.add('__main__')
        self.autocomplete.add('__init__')
        self.autocomplete.add('__str__')
        self.autocomplete.add('__repr__')

        if not text:

            firstList = []     # list to edit
            secondList = []    # collect all items for autocomplete

            text = self.text()

            # parse complete text ....
            firstList = text.splitlines()

            for line in firstList:
                if 'def' in line:
                    item = line.strip()
                    item = item.strip('def')
                    item = item.replace(':', '')
                    if not item in secondList:
                        secondList.append(item)
                elif 'class' in line:
                    item = line.strip()
                    item = item.strip('class')
                    item = item.replace(':', '')
                    if not item in secondList:
                        secondList.append(item)

            text = text.replace('"', " ").replace("'", " ").replace("(", " ").replace(")", " ").replace("[", " ").replace("]", " ").replace(
                ':', " ").replace(',', " ").replace("<", " ").replace(">", " ").replace("/", " ").replace("=", " ").replace(";", " ")

            firstList = text.split('\n')

            for row in firstList:

                if (row.strip().startswith('#')) or (row.strip().startswith('//')):
                    continue

                else:
                    wordList = row.split()

                    for word in wordList:

                        if re.match("(^[0-9])", word):
                            continue

                        elif '#' in word or '//' in word:
                            continue

                        elif word in self.keywords:
                            continue

                        elif (word == '__init__') or (word == '__main__') or \
                             (word == '__name__') or (word == '__str__') or \
                             (word == '__repr__'):
                            continue

                        elif word in secondList:
                            continue

                        elif len(word) > 15:
                            continue

                        elif not len(word) < 3:
                            w = re.sub("{}<>;,:]", '', word)
                            # print(w)
                            secondList.append(w)

            # delete doubled entries
            x = set(secondList)
            secondList = list(x)

            # debugging ...
            # print(secondList)

            for item in secondList:
                self.autocomplete.add(item)

            self.autocomplete.prepare()

    def setPythonPrintStyle(self):
        # Set None lexer
        self.font = QFont()

        system = platform.system().lower()
        if system == 'windows':
            self.font.setFamily('Consolas')
        else:
            self.font.setFamily('Monospace')

        self.font.setFixedPitch(True)
        self.font.setPointSize(10)
        self.setFont(self.font)

        self.lexer = PythonLexer()
        self.lexer.setFont(self.font)
        # set Lexer
        self.setLexer(self.lexer)

        self.setCaretLineBackgroundColor(QColor("#344c4c"))
        self.lexer.setDefaultPaper(QColor("white"))
        self.lexer.setDefaultColor(QColor("black"))
        self.lexer.setColor(QColor('black'), -1)  # default
        self.lexer.setPaper(QColor('white'), -1)  # default
        self.lexer.setColor(
            QColor('gray'), PythonLexer.Comment)  # entspricht 1
        self.lexer.setColor(QColor('orange'), 2)   # Number entspricht 2
        # DoubleQuotedString entspricht 3
        self.lexer.setColor(QColor('white'), 3)
        # SingleQuotedString entspricht 4
        self.lexer.setColor(QColor('white'), 4)
        self.lexer.setColor(QColor('darkblue'), 5)   # Keyword entspricht 5
        # TripleSingleQuotedString entspricht 6
        self.lexer.setColor(QColor('white'), 6)
        # TripleDoubleQuotedString entspricht 7
        self.lexer.setColor(QColor('white'), 7)
        self.lexer.setColor(QColor('red'), 8)   # ClassName entspricht 8
        # FunctionMethodName entspricht 9
        self.lexer.setColor(QColor('crimson'), 9)
        self.lexer.setColor(QColor('white'), 10)   # Operator entspricht 10
        # Identifier entspricht 11 ### alle Wörter
        self.lexer.setColor(QColor('black'), 11)
        self.lexer.setColor(QColor('gray'), 12)   # CommentBlock entspricht 12
        # UnclosedString entspricht 13
        self.lexer.setColor(QColor('#ff471a'), 13)
        # HighlightedIdentifier entspricht 14
        self.lexer.setColor(QColor('gray'), 14)
        self.lexer.setColor(QColor('#5DD3AF'), 15)   # Decorator entspricht 15

        self.setNoneAutocomplete()
        self.unsetFold()

        self.font = QFont()

        system = platform.system().lower()
        if system == 'windows':
            self.font.setFamily('Consolas')
        else:
            self.font.setFamily('Monospace')

        self.font.setFixedPitch(True)
        self.font.setPointSize(self.pointSize)

    def setNoneAutocomplete(self):
        # AutoCompletion
        self.autocomplete = Qsci.QsciAPIs(self.lexer)
        self.autocomplete.clear()

        self.autocomplete.prepare()

        self.setAutoCompletionThreshold(3)
        self.setAutoCompletionSource(QsciScintilla.AcsAPIs)

    def resetPythonPrintStyle(self, lexer):
        system = platform.system().lower()
        self.font = QFont()
        self.font.setFamily('Consolas' if system == 'windows' else 'Monospace')
        self.font.setFixedPitch(True)
        self.font.setPointSize(self.pointSize)
        self.setFont(self.font)
        lexer.setFont(self.font)
        self.setLexer(lexer)
        fontmetrics = QFontMetrics(self.font)
        self.setMarginsFont(self.font)
        self.setMarginWidth(0, fontmetrics.width("00000") + 5)
        self.setMarginLineNumbers(0, True)
        self.setMarginsBackgroundColor(QColor("#000000"))
        self.setMarginsForegroundColor(QColor("#FFFFFF"))
        self.setFoldMarginColors(QColor('white'), QColor('white'))