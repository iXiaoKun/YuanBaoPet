"""Single-instance guard: reopening the app brings the existing pet forward."""
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtNetwork import QLocalServer, QLocalSocket

DEFAULT_KEY = "YuanBaoPet-instance-7f3c"
SHOW_COMMAND = b"SHOW\n"


class SingleInstance(QObject):
    """Second launch asks the first one to show up, then exits."""

    activated = pyqtSignal()

    def __init__(self, key=DEFAULT_KEY, parent=None):
        super().__init__(parent)
        self.key = key
        self._server = None
        self._sockets = []

    def notify_existing(self, timeout_ms=400):
        """True if another instance answered and was asked to show itself."""
        socket = QLocalSocket()
        socket.connectToServer(self.key)
        if not socket.waitForConnected(timeout_ms):
            return False
        socket.write(SHOW_COMMAND)
        socket.flush()
        socket.waitForBytesWritten(timeout_ms)
        socket.disconnectFromServer()
        return True

    def listen(self):
        QLocalServer.removeServer(self.key)
        self._server = QLocalServer(self)
        self._server.newConnection.connect(self._on_new_connection)
        return self._server.listen(self.key)

    def _on_new_connection(self):
        while self._server is not None and self._server.hasPendingConnections():
            conn = self._server.nextPendingConnection()
            self._sockets.append(conn)
            conn.readyRead.connect(lambda c=conn: self._read(c))
            conn.disconnected.connect(lambda c=conn: self._drop(c))
            self.activated.emit()

    def _read(self, conn):
        conn.readAll()
        self.activated.emit()

    def _drop(self, conn):
        if conn in self._sockets:
            self._sockets.remove(conn)
        conn.deleteLater()

    def close(self):
        if self._server is not None:
            self._server.close()
            self._server = None
