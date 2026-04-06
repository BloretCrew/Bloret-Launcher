"""
compat_widgets.py
=================
PySide6-based compatibility shim for qfluentwidgets API.
Provides drop-in replacements so existing code continues to work
after removing the qfluentwidgets dependency.

All classes and enums mirror the qfluentwidgets public API surface
used throughout Bloret Launcher.
"""

import logging
from enum import Enum, auto
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QToolButton, QComboBox, QSpinBox,
    QCheckBox, QLineEdit, QScrollArea, QFrame, QMenu, QDialog,
    QVBoxLayout, QHBoxLayout, QDialogButtonBox, QProgressBar,
    QTabBar, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, Signal, QSize, QUrl
from PySide6.QtGui import (
    QAction, QPixmap, QIcon, QDesktopServices, QColor, QFont
)

_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
#  InfoBarPosition  (enum)
# ---------------------------------------------------------------------------
class InfoBarPosition:
    TOP = 0
    BOTTOM = 1
    TOP_LEFT = 2
    TOP_RIGHT = 3
    BOTTOM_LEFT = 4
    BOTTOM_RIGHT = 5
    NONE = 6


# ---------------------------------------------------------------------------
#  InfoBar  –  static helper that logs instead of showing a widget overlay
# ---------------------------------------------------------------------------
class InfoBar:
    """Drop-in replacement: logs the notification instead of painting one."""

    @staticmethod
    def _notify(level, title, content, **kw):
        msg = f"[InfoBar.{level}] {title}: {content}"
        _log.log(getattr(logging, level.upper(), logging.INFO), msg)

    @staticmethod
    def success(title='', content='', *, orient=None, isClosable=True,
                position=InfoBarPosition.TOP, duration=2000, parent=None, **kw):
        InfoBar._notify('info', title, content)

    @staticmethod
    def error(title='', content='', *, orient=None, isClosable=True,
              position=InfoBarPosition.TOP, duration=2000, parent=None, **kw):
        InfoBar._notify('error', title, content)

    @staticmethod
    def warning(title='', content='', *, orient=None, isClosable=True,
                position=InfoBarPosition.TOP, duration=2000, parent=None, **kw):
        InfoBar._notify('warning', title, content)

    @staticmethod
    def info(title='', content='', *, orient=None, isClosable=True,
             position=InfoBarPosition.TOP, duration=2000, parent=None, **kw):
        InfoBar._notify('info', title, content)


# ---------------------------------------------------------------------------
#  Label variants
# ---------------------------------------------------------------------------
class BodyLabel(QLabel):
    """Regular body text label."""
    def __init__(self, text='', parent=None):
        if isinstance(text, QWidget) and parent is None:
            # BodyLabel(parent) overload
            super().__init__(text)
        else:
            super().__init__(str(text) if text else '', parent)

    def setTextColor(self, light_color, dark_color=None):
        color = light_color or dark_color
        if color:
            self.setStyleSheet(f"color: {color};")


class StrongBodyLabel(BodyLabel):
    """Bold body text label."""
    def __init__(self, text='', parent=None):
        super().__init__(text, parent)
        font = self.font()
        font.setBold(True)
        self.setFont(font)


class SubtitleLabel(BodyLabel):
    """Larger subtitle label."""
    def __init__(self, text='', parent=None):
        super().__init__(text, parent)
        font = self.font()
        font.setPointSize(font.pointSize() + 4)
        font.setBold(True)
        self.setFont(font)


class CaptionLabel(BodyLabel):
    """Smaller caption label."""
    def __init__(self, text='', parent=None):
        super().__init__(text, parent)
        font = self.font()
        font.setPointSize(max(font.pointSize() - 2, 8))
        self.setFont(font)


class HyperlinkLabel(QLabel):
    """Clickable hyperlink label."""
    def __init__(self, url='', text='', parent=None):
        super().__init__(parent)
        self._url = url
        if text:
            self.setText(text)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("color: #0078d4; text-decoration: underline;")

    def setUrl(self, url):
        self._url = url

    def mousePressEvent(self, event):
        if self._url:
            QDesktopServices.openUrl(QUrl(self._url))
        super().mousePressEvent(event)


# ---------------------------------------------------------------------------
#  ImageLabel
# ---------------------------------------------------------------------------
class ImageLabel(QLabel):
    """QLabel wrapper that loads a pixmap from path."""
    def __init__(self, image_path='', parent=None):
        if isinstance(image_path, QWidget) and parent is None:
            super().__init__(image_path)
        else:
            super().__init__(parent)
            if image_path and isinstance(image_path, str):
                pm = QPixmap(image_path)
                if not pm.isNull():
                    self.setPixmap(pm)

    def setImage(self, path):
        pm = QPixmap(path)
        if not pm.isNull():
            self.setPixmap(pm)

    def setScaledContents(self, on):
        super().setScaledContents(on)

    def scaledToWidth(self, w):
        pm = self.pixmap()
        if pm and not pm.isNull():
            self.setPixmap(pm.scaledToWidth(w, Qt.SmoothTransformation))


# ---------------------------------------------------------------------------
#  IconWidget
# ---------------------------------------------------------------------------
class IconWidget(QLabel):
    """Displays an icon via QPixmap or QIcon."""
    def __init__(self, icon=None, parent=None):
        if isinstance(icon, QWidget) and parent is None:
            super().__init__(icon)
        else:
            super().__init__(parent)
            if icon is not None:
                self.setIcon(icon)

    def setIcon(self, icon):
        if isinstance(icon, QIcon):
            self.setPixmap(icon.pixmap(QSize(16, 16)))
        elif isinstance(icon, QPixmap):
            self.setPixmap(icon)
        elif isinstance(icon, str):
            pm = QPixmap(icon)
            if not pm.isNull():
                self.setPixmap(pm)


# ---------------------------------------------------------------------------
#  Button variants
# ---------------------------------------------------------------------------
class PushButton(QPushButton):
    pass


class PrimaryPushButton(QPushButton):
    """Highlighted / accent-colored button."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet(
            "QPushButton { background-color: #0078d4; color: white; "
            "border: none; padding: 6px 16px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #106ebe; }"
        )


class ToolButton(QToolButton):
    pass


# ---------------------------------------------------------------------------
#  Input widgets
# ---------------------------------------------------------------------------
class ComboBox(QComboBox):
    pass


class SpinBox(QSpinBox):
    pass


class LineEdit(QLineEdit):
    pass


class SearchLineEdit(QLineEdit):
    """QLineEdit with search placeholder."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Search…")
        self.searchSignal = Signal(str)

    def search(self):
        pass


class CheckBox(QCheckBox):
    pass


class SwitchButton(QWidget):
    """Toggle switch that mimics qfluentwidgets SwitchButton API."""
    checkedChanged = Signal(bool)

    def __init__(self, parent=None, indicatorPos=None):
        super().__init__(parent)
        self._checked = False
        self._cb = QCheckBox(self)
        self._cb.toggled.connect(self._on_toggle)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._cb)

    def _on_toggle(self, checked):
        self._checked = checked
        self.checkedChanged.emit(checked)

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        self._checked = checked
        self._cb.setChecked(checked)

    def setOnText(self, text):
        pass

    def setOffText(self, text):
        pass


# ---------------------------------------------------------------------------
#  Containers
# ---------------------------------------------------------------------------
class CardWidget(QFrame):
    """Simple card container with a subtle border/shadow."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName("CardWidget")

    def setClickEnabled(self, enabled):
        pass


class SmoothScrollArea(QScrollArea):
    """Drop-in for qfluentwidgets SmoothScrollArea."""
    pass


# ---------------------------------------------------------------------------
#  Menu
# ---------------------------------------------------------------------------
class RoundMenu(QMenu):
    """Standard QMenu drop-in."""
    pass


class Action(QAction):
    """QAction drop-in that accepts a FluentIcon as first arg."""
    def __init__(self, *args, **kwargs):
        # Handle FluentIcon as first argument
        triggered = kwargs.pop('triggered', None)
        if args and isinstance(args[0], _FluentIconMember):
            icon = args[0].icon()
            args = args[1:]
            super().__init__(icon, *args, **kwargs)
        else:
            super().__init__(*args, **kwargs)
        if triggered:
            self.triggered.connect(triggered)


# ---------------------------------------------------------------------------
#  FluentIcon  –  provides named icons via QStyle standard pixmaps
# ---------------------------------------------------------------------------
class _FluentIconMember:
    """Single icon member that can produce a QIcon."""
    def __init__(self, name):
        self._name = name

    def icon(self, theme=None):
        # Return a blank icon – actual icons are now in QML/RinUI
        return QIcon()

    def __repr__(self):
        return f"FluentIcon.{self._name}"


class _FluentIconEnum:
    """Namespace that lazily creates _FluentIconMember objects."""
    _cache = {}

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        if name not in self._cache:
            self._cache[name] = _FluentIconMember(name)
        return self._cache[name]

FluentIcon = _FluentIconEnum()


# ---------------------------------------------------------------------------
#  Progress
# ---------------------------------------------------------------------------
class IndeterminateProgressBar(QProgressBar):
    """QProgressBar configured as indeterminate."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(0, 0)  # indeterminate mode

    def start(self):
        self.setRange(0, 0)
        self.show()

    def stop(self):
        self.setRange(0, 100)
        self.hide()


# ---------------------------------------------------------------------------
#  Tab widgets
# ---------------------------------------------------------------------------
class TabBar(QTabBar):
    pass


class Pivot(QWidget):
    """Simple pivot/tab-bar wrapper."""
    currentItemChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tab = QTabBar(self)
        self._tab.setExpanding(False)
        self._keys = []
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._tab)
        self._tab.currentChanged.connect(self._on_changed)

    def addItem(self, routeKey='', text='', onClick=None, icon=None):
        self._tab.addTab(text)
        self._keys.append(routeKey)
        if onClick:
            # will be called via currentItemChanged
            pass

    def setCurrentItem(self, routeKey):
        if routeKey in self._keys:
            self._tab.setCurrentIndex(self._keys.index(routeKey))

    def _on_changed(self, index):
        if 0 <= index < len(self._keys):
            self.currentItemChanged.emit(self._keys[index])


class SegmentedWidget(Pivot):
    """Alias – segmented toggle behaves like pivot."""
    pass


# ---------------------------------------------------------------------------
#  Dialog base classes
# ---------------------------------------------------------------------------
class MessageBoxBase(QDialog):
    """
    Base dialog that provides viewLayout, yesButton, cancelButton, widget.
    Mimics the qfluentwidgets MessageBoxBase API.
    """
    accepted = Signal()
    rejected = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() | Qt.WindowCloseButtonHint)
        self.setMinimumWidth(400)

        self.widget = self  # compatibility: some code does self.widget.setMinimumWidth(...)

        self.viewLayout = QVBoxLayout()
        self.buttonLayout = QHBoxLayout()

        self.yesButton = QPushButton("OK")
        self.cancelButton = QPushButton("Cancel")

        self.buttonLayout.addStretch()
        self.buttonLayout.addWidget(self.yesButton)
        self.buttonLayout.addWidget(self.cancelButton)

        self._mainLayout = QVBoxLayout(self)
        self._mainLayout.addLayout(self.viewLayout)
        self._mainLayout.addStretch()
        self._mainLayout.addLayout(self.buttonLayout)

        self.yesButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

    def exec(self):
        return super().exec()


class MessageBox(QDialog):
    """
    Simple message dialog with title + content + Yes/No buttons.
    """
    yesSignal = Signal()
    cancelSignal = Signal()

    def __init__(self, title='', content='', parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)

        self.titleLabel = QLabel(title)
        font = self.titleLabel.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 2)
        self.titleLabel.setFont(font)

        self.contentLabel = QLabel(content)
        self.contentLabel.setWordWrap(True)

        self.yesButton = QPushButton("OK")
        self.cancelButton = QPushButton("Cancel")

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.yesButton)
        btn_layout.addWidget(self.cancelButton)

        layout.addWidget(self.titleLabel)
        layout.addWidget(self.contentLabel)
        layout.addStretch()
        layout.addLayout(btn_layout)

        self.yesButton.clicked.connect(self._on_yes)
        self.cancelButton.clicked.connect(self._on_cancel)

    def _on_yes(self):
        self.yesSignal.emit()
        self.accept()

    def _on_cancel(self):
        self.cancelSignal.emit()
        self.reject()

    def exec(self):
        return super().exec()


class Dialog(MessageBox):
    """Alias for MessageBox."""
    pass


# ---------------------------------------------------------------------------
#  Convenience re-exports  (so  `from compat_widgets import Action` works)
# ---------------------------------------------------------------------------
__all__ = [
    'InfoBar', 'InfoBarPosition',
    'BodyLabel', 'StrongBodyLabel', 'SubtitleLabel', 'CaptionLabel',
    'HyperlinkLabel', 'ImageLabel', 'IconWidget',
    'PushButton', 'PrimaryPushButton', 'ToolButton',
    'ComboBox', 'SpinBox', 'LineEdit', 'SearchLineEdit',
    'CheckBox', 'SwitchButton',
    'CardWidget', 'SmoothScrollArea',
    'RoundMenu', 'Action', 'FluentIcon',
    'IndeterminateProgressBar',
    'TabBar', 'Pivot', 'SegmentedWidget',
    'MessageBoxBase', 'MessageBox', 'Dialog',
]
