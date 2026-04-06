import sys
sys.path.insert(0, '.')
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtCore import QUrl

engine = QQmlEngine()

for f in ['qml/components/ErrorAnalysisDialog.qml', 'qml/main.qml']:
    component = QQmlComponent(engine)
    component.loadUrl(QUrl.fromLocalFile(f))
    errors = component.errors()
    if errors:
        print(f"Errors in {f}:")
        for e in errors:
            print(f"  {e.toString()}")
    else:
        print(f"No errors in {f}")
