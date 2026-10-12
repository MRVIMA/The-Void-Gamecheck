import gc
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qapp():
    widgets = pytest.importorskip("PySide6.QtWidgets")
    app = widgets.QApplication.instance() or widgets.QApplication([])
    yield app
    _delete_widgets(app)


@pytest.fixture(autouse=True)
def _cleanup_widgets(request):
    """Delete windows after each test so PySide6 never crashes at interpreter exit."""
    yield
    if "qapp" in request.fixturenames:
        _delete_widgets(request.getfixturevalue("qapp"))


def _delete_widgets(app):
    from PySide6.QtCore import QCoreApplication, QEvent

    for widget in app.topLevelWidgets():
        widget.close()
        widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    app.processEvents()
    gc.collect()
