"""Graphical user interface for the Deep Organizer application."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Optional, Set

from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .core import FileOrganizer


@dataclass
class OrganizerConfig:
    """Configuration for running the file organizer."""

    directory: str
    model: str
    dry_run: bool
    max_file_size: int
    excluded_files: Set[str]
    excluded_folders: Set[str]


class OrganizerWorker(QObject):
    """Background worker that executes the organization process."""

    finished = Signal(dict)
    failed = Signal(str)
    progress = Signal(str)

    def __init__(self, config: OrganizerConfig) -> None:
        super().__init__()
        self._config = config

    @Slot()
    def run(self) -> None:
        try:
            self.progress.emit("Initializing organizer…")
            organizer = FileOrganizer(
                work_dir=self._config.directory,
                model=self._config.model,
                excluded_files=self._config.excluded_files or None,
                excluded_folders=self._config.excluded_folders or None,
                max_file_read_size=self._config.max_file_size,
            )

            preview = organizer.get_file_list()
            self.progress.emit(
                f"Analyzing {len(preview)} items in '{self._config.directory}'."
            )

            result = organizer.organize(dry_run=self._config.dry_run)
            self.finished.emit(result)
        except Exception as exc:  # pragma: no cover - GUI runtime safety
            self.failed.emit(str(exc))


class OrganizerWindow(QMainWindow):
    """Main window for the Deep Organizer GUI."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Deep Organizer")
        self.setMinimumSize(960, 640)

        self._thread: Optional[QThread] = None
        self._worker: Optional[OrganizerWorker] = None

        self._directory_field = QLineEdit()
        self._directory_field.setPlaceholderText("Choose a directory to organize…")
        self._directory_field.setClearButtonEnabled(True)

        self._model_select = QComboBox()
        self._model_select.addItems(
            [
                "openai:gpt-4-mini",
                "openai:gpt-4o-mini",
                "openai:gpt-4.1-mini",
                "anthropic:claude-3-sonnet",
            ]
        )

        self._dry_run_check = QCheckBox("Dry run (analyze without moving files)")
        self._dry_run_check.setChecked(True)

        self._max_file_size = QSpinBox()
        self._max_file_size.setRange(200, 10_000)
        self._max_file_size.setSingleStep(200)
        self._max_file_size.setValue(FileOrganizer.DEFAULT_MAX_FILE_READ_SIZE)

        self._excluded_files = QLineEdit()
        self._excluded_files.setPlaceholderText("Comma-separated list of additional files")

        self._excluded_folders = QLineEdit()
        self._excluded_folders.setPlaceholderText(
            "Comma-separated list of additional folders"
        )

        self._log_view = QTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setObjectName("logView")

        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)

        self._start_button = QPushButton("Start Organizing")
        self._start_button.setDefault(True)
        self._start_button.clicked.connect(self._start_organizing)

        self._directory_button = QPushButton("Browse…")
        self._directory_button.clicked.connect(self._select_directory)

        self._configure_palette()
        self.setCentralWidget(self._build_layout())

    def _configure_palette(self) -> None:
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#101827"))
        palette.setColor(QPalette.WindowText, QColor("#F8FAFC"))
        palette.setColor(QPalette.Base, QColor("#0F172A"))
        palette.setColor(QPalette.AlternateBase, QColor("#1E293B"))
        palette.setColor(QPalette.Text, QColor("#E2E8F0"))
        palette.setColor(QPalette.Button, QColor("#1E293B"))
        palette.setColor(QPalette.ButtonText, QColor("#E2E8F0"))
        palette.setColor(QPalette.Highlight, QColor("#38BDF8"))
        palette.setColor(QPalette.HighlightedText, QColor("#0F172A"))
        self.setPalette(palette)

        font = QFont("SF Pro Display", 11)
        QApplication.instance().setFont(font)

        self._log_view.setStyleSheet(
            "QTextEdit#logView {"
            "    border-radius: 12px;"
            "    border: 1px solid rgba(148, 163, 184, 0.25);"
            "    padding: 12px;"
            "    background-color: #0F172A;"
            "    color: #E2E8F0;"
            "}"
        )

        self._start_button.setStyleSheet(
            "QPushButton {"
            "    background-color: #38BDF8;"
            "    color: #0F172A;"
            "    font-weight: 600;"
            "    padding: 12px 24px;"
            "    border-radius: 18px;"
            "}"
            "QPushButton:disabled {"
            "    background-color: rgba(148, 163, 184, 0.25);"
            "    color: rgba(226, 232, 240, 0.6);"
            "}"
        )

    def _build_layout(self) -> QWidget:
        content = QWidget()
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(24)

        header = QLabel("Deep Organizer")
        header.setStyleSheet(
            "font-size: 28px; font-weight: 700; color: #F8FAFC; margin-bottom: 4px;"
        )
        subheader = QLabel(
            "Intelligently categorize your files with AI-powered insights."
        )
        subheader.setStyleSheet("color: #94A3B8; font-size: 15px;")

        main_layout.addWidget(header)
        main_layout.addWidget(subheader)

        main_layout.addWidget(self._create_source_group())
        main_layout.addWidget(self._create_preferences_group())

        main_layout.addWidget(self._log_view, stretch=2)

        footer = QHBoxLayout()
        footer.addStretch()
        footer.addWidget(self._start_button)
        main_layout.addLayout(footer)

        return content

    def _create_source_group(self) -> QGroupBox:
        group = QGroupBox("Workspace")
        group.setStyleSheet(
            "QGroupBox {"
            "    color: #E2E8F0;"
            "    border: 1px solid rgba(148, 163, 184, 0.25);"
            "    border-radius: 16px;"
            "    margin-top: 16px;"
            "    padding: 16px;"
            "}"
            "QGroupBox::title {"
            "    subcontrol-origin: margin;"
            "    left: 16px;"
            "    padding: 0 8px;"
            "    font-size: 16px;"
            "    font-weight: 600;"
            "}"
        )

        layout = QVBoxLayout(group)
        layout.setSpacing(12)

        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self._directory_field)
        dir_layout.addWidget(self._directory_button)
        layout.addLayout(dir_layout)

        env_label = QLabel(
            "OpenAI API key must be available in your environment (.env or system)."
        )
        env_label.setStyleSheet("color: #94A3B8; font-size: 13px;")
        layout.addWidget(env_label)

        return group

    def _create_preferences_group(self) -> QGroupBox:
        group = QGroupBox("AI Preferences")
        group.setStyleSheet(
            "QGroupBox {"
            "    color: #E2E8F0;"
            "    border: 1px solid rgba(148, 163, 184, 0.25);"
            "    border-radius: 16px;"
            "    margin-top: 16px;"
            "    padding: 16px;"
            "}"
            "QGroupBox::title {"
            "    subcontrol-origin: margin;"
            "    left: 16px;"
            "    padding: 0 8px;"
            "    font-size: 16px;"
            "    font-weight: 600;"
            "}"
        )

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFormAlignment(Qt.AlignTop)
        form.setSpacing(12)

        form.addRow(QLabel("AI model"), self._model_select)
        form.addRow(QLabel("Max characters per file"), self._max_file_size)
        form.addRow(QLabel("Additional excluded files"), self._excluded_files)
        form.addRow(QLabel("Additional excluded folders"), self._excluded_folders)
        form.addRow(self._dry_run_check)

        group.setLayout(form)
        return group

    def _select_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self._directory_field.setText(directory)

    def _start_organizing(self) -> None:
        directory = self._directory_field.text().strip()
        if not directory:
            self._show_message("Choose a directory", "Please select a directory first.")
            return

        if not os.path.isdir(directory):
            self._show_message(
                "Invalid directory",
                "The selected path is not a valid directory on this system.",
            )
            return

        if not os.getenv("OPENAI_API_KEY"):
            self._show_message(
                "Missing OpenAI API key",
                "Set the OPENAI_API_KEY environment variable before running the organizer.",
                icon=QMessageBox.Icon.Warning,
            )
            return

        config = OrganizerConfig(
            directory=directory,
            model=self._model_select.currentText(),
            dry_run=self._dry_run_check.isChecked(),
            max_file_size=self._max_file_size.value(),
            excluded_files=self._parse_csv(self._excluded_files.text()),
            excluded_folders=self._parse_csv(self._excluded_folders.text()),
        )

        self._log_view.clear()
        self._start_button.setEnabled(False)
        self._status_bar.showMessage("Organizing files…")
        self._append_log("🚀 Starting Deep Organizer…")

        self._thread = QThread(self)
        self._worker = OrganizerWorker(config)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._append_log)
        self._worker.finished.connect(self._handle_result)
        self._worker.failed.connect(self._handle_error)

        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.failed.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._cleanup_thread)

        self._thread.start()

    def _handle_result(self, result: dict) -> None:
        self._append_log("✅ Organization completed.")
        self._status_bar.showMessage("Organization finished", 5000)
        self._start_button.setEnabled(True)

        if result.get("success"):
            message = result.get("message", "Organization finished successfully.")
            details = self._extract_summary(result)
            self._show_message("Deep Organizer", f"{message}\n\n{details}", icon=QMessageBox.Icon.Information)
        else:
            error = result.get("error", "Unknown error occurred.")
            self._show_message("Deep Organizer", error, icon=QMessageBox.Icon.Critical)

    def _handle_error(self, message: str) -> None:
        self._append_log(f"❌ {message}")
        self._status_bar.showMessage("Organization failed", 5000)
        self._start_button.setEnabled(True)
        self._show_message("Deep Organizer", message, icon=QMessageBox.Icon.Critical)

    def _cleanup_thread(self) -> None:
        if self._thread:
            self._thread.deleteLater()
        self._thread = None
        self._worker = None

    def _append_log(self, message: str) -> None:
        self._log_view.append(message)
        self._log_view.verticalScrollBar().setValue(
            self._log_view.verticalScrollBar().maximum()
        )

    def _parse_csv(self, text: str) -> Set[str]:
        return {item.strip() for item in text.split(",") if item.strip()}

    def _extract_summary(self, result: dict) -> str:
        try:
            messages = result["result"]["messages"]
            if not messages:
                return ""
            last_message = messages[-1]
            content = last_message.get("content", "").strip()
            if not content:
                return ""
            return content
        except Exception:  # pragma: no cover - defensive
            return ""

    def _show_message(
        self,
        title: str,
        message: str,
        *,
        icon: QMessageBox.Icon = QMessageBox.Icon.Information,
    ) -> None:
        QMessageBox(icon, title, message, parent=self).exec()


def run_app() -> int:
    """Launch the Deep Organizer GUI application."""

    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")

    window = OrganizerWindow()
    window.show()
    return app.exec()
