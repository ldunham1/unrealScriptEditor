"""
https://wiki.python.org/moin/PyQt/Python%20syntax%20highlighting
"""
from collections import namedtuple

from Qt import QtCore, QtGui, QtWidgets


def getFormat(color=None, styles=None):
    """
    Get a QTextCharFormat with the given attributes.
    :rtype: QtGui.QTextCharFormat
    """
    _format = QtGui.QTextCharFormat()

    if color is not None:
        _color = QtGui.QColor(color)
        _format.setForeground(_color)

    if styles is not None:
        styles = styles if isinstance(styles, (list, tuple, set)) else [styles]

        if 'bold' in styles:
            _format.setFontWeight(QtGui.QFont.Bold)

        if 'italic' in styles:
            _format.setFontItalic(True)

    return _format


# Syntax styles that can be shared by all languages
STYLES = {
    'keyword': getFormat('#c98300'),
    'operator': getFormat('#828282'),
    'brace': getFormat('#828282'),
    'def': getFormat('#d4bc08'),
    'class': getFormat(),
    'string': getFormat('#41b55c'),
    'stringBlock': getFormat('#41b55c'),
    'comment': getFormat('#828282'),
    'clsself': getFormat(styles='italic'),
    'private': getFormat('#d200f7', 'italic'),
    'numbers': getFormat(),
}
LineRule = namedtuple('LineRule', 'pattern captureBlock style')
MultiLineRule = namedtuple('MultiLineRule', 'start end state style')


class PythonHighlighter(QtGui.QSyntaxHighlighter):
    """
    Syntax highlighter for the Python language.
    """
    # Python keywords
    keywords = [
        'and', 'assert', 'break', 'class', 'continue', 'def',
        'del', 'elif', 'else', 'except', 'exec', 'finally',
        'for', 'from', 'global', 'if', 'import', 'in',
        'is', 'lambda', 'not', 'or', 'pass', 'print',
        'raise', 'return', 'try', 'while', 'yield',
        'None', 'True', 'False',
    ]

    # Python operators
    operators = [
        '=',
        # Comparison
        '==', '!=', '<', '<=', '>', '>=',
        # Arithmetic
        '\+', '-', '\*', '/', '//', '\%', '\*\*',
        # In-place
        '\+=', '-=', '\*=', '/=', '\%=',
        # Bitwise
        '\^', '\|', '\&', '\~', '>>', '<<',
    ]

    # Python braces
    braces = [
        '\{', '\}', '\(', '\)', '\[', '\]',
    ]

    def __init__(self, parent=None):
        super(PythonHighlighter, self).__init__(parent)

        styles = STYLES.copy()

        # Build the basic scripting syntax rules.
        self.rules = []
        self.blockRules = []

        rules = []
        rules += (
            LineRule(pattern=r'\b%s\b' % k, captureBlock=0, style=STYLES['keyword'])
            for k in self.keywords
        )
        rules += (
            LineRule(pattern=r'%s' % o, captureBlock=0, style=STYLES['operator'])
            for o in self.operators
        )
        rules += (
            LineRule(pattern=r'%s' % b, captureBlock=0, style=STYLES['brace'])
            for b in self.braces
        )
        rules += [
            # 'cls' or 'self'
            LineRule(pattern=r'\b(?:cls|self)\b', captureBlock=0, style=STYLES['clsself']),
            # 'def' followed by an identifier
            LineRule(pattern=r'\bdef\b\s*(\w+)', captureBlock=1, style=STYLES['def']),
            # 'class' followed by an identifier
            LineRule(pattern=r'\bclass\b\s*(\w+)', captureBlock=1, style=STYLES['class']),
            # Numeric literals
            LineRule(pattern=r'\b[+-]?[0-9]+[lL]?\b', captureBlock=0, style=STYLES['numbers']),
            LineRule(pattern=r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', captureBlock=0, style=STYLES['numbers']),
            LineRule(pattern=r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', captureBlock=0, style=STYLES['numbers']),
            # Private identifiers
            LineRule(pattern=r'\b_[\w]+\b', captureBlock=0, style=STYLES['private']),
            # Singleline quoted string, possibly containing escape sequences.
            LineRule(pattern=r'"[^"\\]*(\\.[^"\\]*)*"', captureBlock=0, style=STYLES['string']),
            LineRule(pattern=r"'[^'\\]*(\\.[^'\\]*)*'", captureBlock=0, style=STYLES['string']),
            # From '#' until a newline
            LineRule(pattern=r'#[^\n]*', captureBlock=0, style=STYLES['comment']),
            # Multiline quoted string, possibly containing escape sequences
            MultiLineRule(start='"""', end='"""', state=1, style=STYLES['stringBlock']),
            MultiLineRule(start="'''", end="'''", state=2, style=STYLES['stringBlock']),
        ]
        self.buildRules(rules)

    def buildRules(self, rule_list, append=False):
        if not append:
            self.rules = []
            self.blockRules = []

        case_sensitive = QtCore.Qt.CaseSensitive if self.caseSensitive else QtCore.Qt.CaseInsensitive
        for rule in rule_list:
            if isinstance(rule, MultiLineRule):
                start, end, state, fmt = rule
                self.blockRules.append(
                    (
                        QtCore.QRegExp(start, case_sensitive),
                        QtCore.QRegExp(end, case_sensitive),
                        state,
                        fmt,
                    )
                )
            else:
                pat, index, fmt = rule
                self.rules.append(
                    (
                        QtCore.QRegExp(pat, case_sensitive),
                        index,
                        fmt,
                    )
                )

    def highlightMultilineBlock(self, text, start, end, in_state, style):
        """
        Do highlighting of multi-line patterns.

        :param str text: Text to match.
        :param QtCore.QRegExp start: Multiline start block pattern.
        :param QtCore.QRegExp end: Multiline end block pattern.
        :param int in_state: A unique integer to represent the corresponding state changes when
        inside those strings.
        :param QtGui.QFormat style: Format to apply to matching text.

        :return: True if we're still inside a multi-line string when this function is finished.
        :rtype: bool
        """
        # If inside triple-single quotes, start at 0
        if self.previousBlockState() == in_state:
            start_index = 0
            add = 0

        # Otherwise, look for the delimiter on this line
        else:
            start_index = start.indexIn(text)

            # Move past this match
            add = start.matchedLength()

        # As long as there's a delimiter match on this line...
        while start_index >= 0:

            # Look for the ending delimiter
            end_index = end.indexIn(text, start_index + add)

            # Ending delimiter on this line?
            if end_index >= add:
                length = end_index - start_index + add + end.matchedLength()
                self.setCurrentBlockState(0)

            # No multi-line string
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start_index + add

            # Apply formatting
            self.setFormat(start_index, length, style)

            # Look for the next match
            start_index = start.indexIn(text, start_index + length)

        # Return True if still inside a multi-line string, False otherwise
        return self.currentBlockState() == in_state

    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text."""

        # Do multi-line strings
        matched_multiline = False
        for start, end, idx, fmt in self.blockRules:
            matched_multiline = self.highlightMultilineBlock(text, start, end, idx, fmt)
            if matched_multiline:
                break

        if matched_multiline:
            return

        # Do other syntax formatting
        for pattern, nth, fmt in self.rules:
            index = pattern.indexIn(text, 0)

            # We actually want the index of the nth match
            while index >= 0:
                index = pattern.pos(nth)
                length = len(pattern.cap(nth))
                self.setFormat(index, length, fmt)
                index = pattern.indexIn(text, index + length)

        self.setCurrentBlockState(0)
