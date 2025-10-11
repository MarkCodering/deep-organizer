"""Graphical user interface for the Deep Organizer application."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Optional, Set

from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot, QSettings
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSpinBox,
    QStatusBar,
    QToolButton,
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
        self.setMinimumSize(1080, 720)

        self._thread: Optional[QThread] = None
        self._worker: Optional[OrganizerWorker] = None

        self._settings = QSettings("DeepOrganizer", "DesktopApp")
        self._loading_saved_api = False

        self._directory_field = QLineEdit()
        self._directory_field.setPlaceholderText("Choose a directory to organize…")
        self._directory_field.setClearButtonEnabled(True)
        self._directory_field.setMinimumHeight(44)

        self._model_select = QComboBox()
        self._model_select.addItems(
            [
                "openai:gpt-4o-mini",
                "openai:gpt-4-mini",
                "openai:gpt-4.1-mini",
                "anthropic:claude-3-sonnet",
            ]
        )
        self._model_select.setMinimumHeight(40)

        self._dry_run_check = QCheckBox(
            "Dry run (analyze without moving files)"
        )
        self._dry_run_check.setChecked(True)
        self._dry_run_check.setObjectName("dryRunCheck")

        self._max_file_size = QSpinBox()
        self._max_file_size.setRange(200, 10_000)
        self._max_file_size.setSingleStep(200)
        self._max_file_size.setValue(FileOrganizer.DEFAULT_MAX_FILE_READ_SIZE)
        self._max_file_size.setMinimumHeight(40)

        self._excluded_files = QLineEdit()
        self._excluded_files.setPlaceholderText(
            "Comma-separated list of additional files"
        )
        self._excluded_files.setMinimumHeight(40)

        self._excluded_folders = QLineEdit()
        self._excluded_folders.setPlaceholderText(
            "Comma-separated list of additional folders"
        )
        self._excluded_folders.setMinimumHeight(40)

        self._api_key_field = QLineEdit()
        self._api_key_field.setPlaceholderText("sk-… or claude-api-key")
        self._api_key_field.setMinimumHeight(44)
        self._api_key_field.setEchoMode(QLineEdit.Password)
        self._api_key_field.textChanged.connect(self._handle_api_key_change)

        self._api_toggle = QToolButton()
        self._api_toggle.setCheckable(True)
        self._api_toggle.setObjectName("tertiaryButton")
        self._api_toggle.setCursor(Qt.PointingHandCursor)
        self._api_toggle.setText("Show")
        self._api_toggle.toggled.connect(self._toggle_api_visibility)

        self._save_api_button = QPushButton("Save for this Mac")
        self._save_api_button.setObjectName("secondaryButton")
        self._save_api_button.setCursor(Qt.PointingHandCursor)
        self._save_api_button.clicked.connect(self._save_api_key)

        self._log_view = QTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setObjectName("logView")
        self._log_view.setMinimumHeight(200)

        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)

        self._start_button = QPushButton("Start Organizing")
        self._start_button.setDefault(True)
        self._start_button.setObjectName("primaryButton")
        self._start_button.setCursor(Qt.PointingHandCursor)
        self._start_button.clicked.connect(self._start_organizing)

        self._directory_button = QPushButton("Browse…")
        self._directory_button.setObjectName("secondaryButton")
        self._directory_button.setCursor(Qt.PointingHandCursor)
        self._directory_button.setMinimumHeight(40)
        self._directory_button.clicked.connect(self._select_directory)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setFixedHeight(4)
        self._progress_bar.setObjectName("progressBar")
        self._progress_bar.hide()

        self._status_chip = QLabel("Ready")
        self._status_chip.setObjectName("statusChip")
        self._status_chip.setAlignment(Qt.AlignCenter)
        self._status_chip.setProperty("state", "ready")
        self._status_chip.setMinimumWidth(120)

        self._api_status_label: Optional[QLabel] = None

        self._load_saved_api_key()
        self._configure_palette()
        self.setCentralWidget(self._build_layout())
        self._update_status_chip("ready", "Ready")
        self._sync_api_status()

    def _configure_palette(self) -> None:
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#F3F4F6"))
        palette.setColor(QPalette.WindowText, QColor("#0F172A"))
        palette.setColor(QPalette.Base, QColor("#FFFFFF"))
        palette.setColor(QPalette.AlternateBase, QColor("#F8FAFC"))
        palette.setColor(QPalette.Text, QColor("#0F172A"))
        palette.setColor(QPalette.Button, QColor("#2563EB"))
        palette.setColor(QPalette.ButtonText, QColor("#F8FAFC"))
        palette.setColor(QPalette.Highlight, QColor("#2563EB"))
        palette.setColor(QPalette.HighlightedText, QColor("#F8FAFC"))
        self.setPalette(palette)

        app = QApplication.instance()
        if app:
            app.setPalette(palette)
            app.setFont(QFont("SF Pro Text", 12))

        self.setStyleSheet(
            """
            QWidget#root {
                background-color: #F3F4F6;
            }
            QFrame#heroPanel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2563EB, stop:1 #14B8A6);
                border-radius: 28px;
            }
            QLabel#heroTitle {
                font-size: 32px;
                font-weight: 700;
                color: #FDFDFC;
            }
            QLabel#heroSubtitle {
                color: rgba(248, 250, 252, 0.88);
                font-size: 16px;
            }
            QLabel#heroDetail {
                color: rgba(241, 244, 248, 0.78);
                font-size: 13px;
            }
            QLabel#statusChip {
                border-radius: 14px;
                padding: 6px 14px;
                font-size: 13px;
                font-weight: 600;
            }
            QLabel#statusChip[state="ready"] {
                background-color: rgba(248, 250, 252, 0.18);
                color: #F8FAFC;
            }
            QLabel#statusChip[state="working"] {
                background-color: rgba(248, 250, 252, 0.28);
                color: #F8FAFC;
            }
            QLabel#statusChip[state="success"] {
                background-color: rgba(134, 239, 172, 0.9);
                color: #064E3B;
            }
            QLabel#statusChip[state="error"] {
                background-color: rgba(248, 113, 113, 0.9);
                color: #7F1D1D;
            }
            QLabel#apiStatus {
                border-radius: 12px;
                padding: 6px 12px;
                font-size: 13px;
                font-weight: 600;
            }
            QLabel#apiStatus[state="ready"] {
                background-color: rgba(134, 239, 172, 0.35);
                color: #065F46;
            }
            QLabel#apiStatus[state="missing"] {
                background-color: rgba(251, 191, 36, 0.35);
                color: #92400E;
            }
            QFrame[card="true"] {
                background-color: #FFFFFF;
                border-radius: 24px;
            }
            QFrame[section="true"] {
                background-color: rgba(15, 23, 42, 0.035);
                border-radius: 18px;
            }
            QLabel#sectionTitle {
                font-size: 18px;
                font-weight: 600;
                color: #0F172A;
            }
            QLabel#sectionHelper {
                color: #475569;
                font-size: 13px;
            }
            QLabel#formLabel {
                color: #1F2937;
                font-weight: 500;
                padding-bottom: 4px;
            }
            QLabel#tipsTitle, QLabel#cardTitle {
                font-size: 17px;
                font-weight: 600;
                color: #0F172A;
            }
            QLabel#tipsList {
                color: #475569;
                font-size: 14px;
            }
            QLineEdit, QComboBox, QSpinBox, QTextEdit {
                background-color: #FFFFFF;
                border: 1px solid rgba(148, 163, 184, 0.5);
                border-radius: 12px;
                padding: 10px 12px;
                font-size: 14px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus {
                border: 1px solid #2563EB;
            }
            QCheckBox {
                font-size: 14px;
                color: #1E293B;
            }
            QTextEdit#logView {
                background-color: #0F172A;
                color: #F8FAFC;
                border: none;
                border-radius: 16px;
                padding: 16px;
            }
            QPushButton#primaryButton {
                background-color: #2563EB;
                color: #F8FAFC;
                font-weight: 600;
                padding: 14px 28px;
                border-radius: 20px;
            }
            QPushButton#primaryButton:disabled {
                background-color: rgba(148, 163, 184, 0.4);
                color: rgba(255, 255, 255, 0.7);
            }
            QPushButton#primaryButton:hover:!disabled {
                background-color: #1D4ED8;
            }
            QPushButton#secondaryButton {
                background-color: rgba(37, 99, 235, 0.1);
                color: #1E3A8A;
                font-weight: 600;
                padding: 10px 20px;
                border-radius: 16px;
            }
            QPushButton#secondaryButton:hover {
                background-color: rgba(37, 99, 235, 0.18);
            }
            QToolButton#tertiaryButton {
                background-color: transparent;
                border: none;
                color: rgba(15, 23, 42, 0.7);
                font-weight: 600;
                padding: 0 12px;
            }
            QToolButton#tertiaryButton:hover {
                color: rgba(29, 78, 216, 0.9);
            }
            QProgressBar#progressBar {
                background-color: rgba(37, 99, 235, 0.12);
                border: none;
                border-radius: 2px;
                min-height: 4px;
            }
            QProgressBar#progressBar::chunk {
                background-color: #2563EB;
                border-radius: 2px;
            }
            """
        )

    def _build_layout(self) -> QWidget:
        content = QWidget()
        content.setObjectName("root")
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(24)

        hero = self._create_hero_header()
        main_layout.addWidget(hero)

        body_layout = QHBoxLayout()
        body_layout.setSpacing(18)
        body_layout.addWidget(self._create_form_card(), stretch=2)
        body_layout.addWidget(self._create_insights_card(), stretch=1)
        main_layout.addLayout(body_layout)

        main_layout.addWidget(self._create_log_card(), stretch=1)

        footer = QHBoxLayout()
        footer.setSpacing(12)
        footer.addWidget(self._progress_bar, stretch=1)
        footer.addStretch(1)
        footer.addWidget(self._start_button)
        main_layout.addLayout(footer)

        return content

    def _create_hero_header(self) -> QFrame:
        hero = QFrame()
        hero.setObjectName("heroPanel")
        layout = QVBoxLayout(hero)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        status_row = QHBoxLayout()
        status_row.addWidget(self._status_chip, alignment=Qt.AlignLeft)
        status_row.addStretch()
        layout.addLayout(status_row)

        title = QLabel("Deep Organizer for macOS")
        title.setObjectName("heroTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Effortlessly curate your workspace with an AI assistant that understands context."
        )
        subtitle.setObjectName("heroSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        detail = QLabel(
            "Choose a directory, preview suggestions in dry-run mode, then let Deep Organizer tidy things up when you're ready."
        )
        detail.setObjectName("heroDetail")
        detail.setWordWrap(True)
        layout.addWidget(detail)

        self._apply_card_shadow(hero, blur=46, y_offset=28, alpha=0.25)
        return hero

    def _create_form_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("card", True)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(20)

        layout.addWidget(self._create_workspace_section())
        layout.addWidget(self._create_preferences_section())
        layout.addWidget(self._create_credentials_section())

        self._apply_card_shadow(card)
        return card

    def _create_workspace_section(self) -> QWidget:
        section, section_layout = self._build_section("Workspace")

        dir_layout = QHBoxLayout()
        dir_layout.setSpacing(12)
        dir_layout.addWidget(self._directory_field, stretch=1)
        dir_layout.addWidget(self._directory_button)
        section_layout.addLayout(dir_layout)

        env_label = QLabel(
            "Pick a directory to organize. Provide credentials via the API Access section, a .env file, or environment variables."
        )
        env_label.setObjectName("sectionHelper")
        env_label.setWordWrap(True)
        section_layout.addWidget(env_label)

        return section

    def _create_preferences_section(self) -> QWidget:
        section, section_layout = self._build_section("AI Preferences")

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFormAlignment(Qt.AlignTop)
        form.setSpacing(18)

        form.addRow(self._build_form_label("AI model"), self._model_select)
        form.addRow(
            self._build_form_label("Max characters per file"), self._max_file_size
        )
        form.addRow(
            self._build_form_label("Additional excluded files"), self._excluded_files
        )
        form.addRow(
            self._build_form_label("Additional excluded folders"),
            self._excluded_folders,
        )
        form.addRow(self._dry_run_check)

        section_layout.addLayout(form)
        return section

    def _create_insights_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("card", True)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        title = QLabel("Quick Tips")
        title.setObjectName("tipsTitle")
        layout.addWidget(title)

        highlight = QLabel(
            "Optimized for macOS Sonoma+ with native fonts, crisp shadows, and smooth gradients."
        )
        highlight.setObjectName("sectionHelper")
        highlight.setWordWrap(True)
        layout.addWidget(highlight)

        tips = QLabel(
            "• Start in Dry run mode to review the suggested structure.<br>"
            "• Add folders like `node_modules` or `venv` to the excluded list.<br>"
            "• Keep a `.deep-organizer-ignore` file to persist exclusions."
        )
        tips.setObjectName("tipsList")
        tips.setWordWrap(True)
        layout.addWidget(tips)

        self._api_status_label = QLabel()
        self._api_status_label.setObjectName("apiStatus")
        layout.addWidget(self._api_status_label)

        layout.addStretch(1)

        self._apply_card_shadow(card)
        return card

    def _create_credentials_section(self) -> QWidget:
        section, section_layout = self._build_section("API Access")

        helper = QLabel(
            "Store an API key locally or use a temporary one below. Saved keys are scoped to this user account."
        )
        helper.setObjectName("sectionHelper")
        helper.setWordWrap(True)
        section_layout.addWidget(helper)

        api_row = QHBoxLayout()
        api_row.setSpacing(0)
        api_row.addWidget(self._api_key_field, stretch=1)
        api_row.addWidget(self._api_toggle)
        section_layout.addLayout(api_row)

        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(12)
        buttons_row.addWidget(self._save_api_button)

        use_once = QPushButton("Use for this session")
        use_once.setObjectName("secondaryButton")
        use_once.setCursor(Qt.PointingHandCursor)
        use_once.clicked.connect(self._apply_api_key_once)
        buttons_row.addWidget(use_once)

        buttons_row.addStretch(1)
        section_layout.addLayout(buttons_row)

        return section

    def _create_log_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("card", True)
        card.setObjectName("logCardContainer")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)

        title = QLabel("Activity")
        title.setObjectName("cardTitle")
        layout.addWidget(title)
        layout.addWidget(self._log_view)

        self._apply_card_shadow(card)
        return card

    def _build_section(self, title: str) -> tuple[QFrame, QVBoxLayout]:
        section = QFrame()
        section.setProperty("section", True)
        layout = QVBoxLayout(section)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QLabel(title)
        header.setObjectName("sectionTitle")
        layout.addWidget(header)

        return section, layout

    def _apply_card_shadow(
        self,
        widget: QWidget,
        *,
        blur: int = 28,
        y_offset: int = 16,
        alpha: float = 0.12,
    ) -> None:
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(blur)
        shadow.setOffset(0, y_offset)
        shadow.setColor(QColor(15, 23, 42, int(255 * alpha)))
        widget.setGraphicsEffect(shadow)

    def _build_form_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("formLabel")
        return label

    def _sync_api_status(self) -> None:
        if not self._api_status_label:
            return

        if self._get_api_key():
            self._api_status_label.setText("API key ready ✅")
            self._api_status_label.setProperty("state", "ready")
        else:
            self._api_status_label.setText("API key missing ⚠️")
            self._api_status_label.setProperty("state", "missing")

        self._api_status_label.style().unpolish(self._api_status_label)
        self._api_status_label.style().polish(self._api_status_label)

    def _select_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self._directory_field.setText(directory)

    def _start_organizing(self) -> None:
        self._sync_api_status()

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

        api_key = self._get_api_key()
        if not api_key:
            self._update_status_chip("error", "Missing API key")
            self._show_message(
                "Missing OpenAI API key",
                "Set the OPENAI_API_KEY environment variable before running the organizer.",
                icon=QMessageBox.Icon.Warning,
            )
            return

        os.environ["OPENAI_API_KEY"] = api_key

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
        self._progress_bar.show()
        self._update_status_chip("working", "Organizing…")
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
        self._progress_bar.hide()
        self._start_button.setEnabled(True)

        if result.get("success"):
            message = result.get("message", "Organization finished successfully.")
            details = self._extract_summary(result)
            self._update_status_chip("success", "Completed")
            self._show_message(
                "Deep Organizer",
                f"{message}\n\n{details}",
                icon=QMessageBox.Icon.Information,
            )
        else:
            error = result.get("error", "Unknown error occurred.")
            self._update_status_chip("error", "Needs attention")
            self._show_message(
                "Deep Organizer",
                error,
                icon=QMessageBox.Icon.Critical,
            )

    def _handle_error(self, message: str) -> None:
        self._append_log(f"❌ {message}")
        self._status_bar.showMessage("Organization failed", 5000)
        self._progress_bar.hide()
        self._start_button.setEnabled(True)
        self._update_status_chip("error", "Failed")
        self._show_message("Deep Organizer", message, icon=QMessageBox.Icon.Critical)

    def _cleanup_thread(self) -> None:
        if self._thread:
            self._thread.deleteLater()
        self._thread = None
        self._worker = None

        if self._status_chip.property("state") == "working":
            self._update_status_chip("ready", "Ready")
        self._progress_bar.hide()

    def _update_status_chip(self, state: str, text: str) -> None:
        self._status_chip.setProperty("state", state)
        self._status_chip.setText(text)
        self._status_chip.style().unpolish(self._status_chip)
        self._status_chip.style().polish(self._status_chip)

        if state == "ready":
            self._status_bar.showMessage("Ready")

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

    def _load_saved_api_key(self) -> None:
        stored_key = self._settings.value("api_key", type=str)
        if stored_key:
            self._loading_saved_api = True
            self._api_key_field.setText(stored_key)
            self._loading_saved_api = False

    def _save_api_key(self) -> None:
        key = self._api_key_field.text().strip()
        if not key:
            self._show_message(
                "Missing key",
                "Enter an API key before saving.",
                icon=QMessageBox.Icon.Warning,
            )
            return

        self._settings.setValue("api_key", key)
        self._settings.sync()
        self._show_message(
            "API key stored",
            "Your key is saved locally for future launches.",
            icon=QMessageBox.Icon.Information,
        )
        self._sync_api_status()

    def _apply_api_key_once(self) -> None:
        key = self._api_key_field.text().strip()
        if not key:
            self._show_message(
                "Missing key",
                "Enter an API key to use for this session.",
                icon=QMessageBox.Icon.Warning,
            )
            return

        os.environ["OPENAI_API_KEY"] = key
        self._show_message(
            "API key applied",
            "This key will be used until you quit the app.",
            icon=QMessageBox.Icon.Information,
        )
        self._sync_api_status()

    def _handle_api_key_change(self) -> None:
        if self._loading_saved_api:
            return

        if not self._api_key_field.text().strip():
            self._settings.remove("api_key")
        self._sync_api_status()

    def _toggle_api_visibility(self, checked: bool) -> None:
        self._api_key_field.setEchoMode(
            QLineEdit.Normal if checked else QLineEdit.Password
        )
        self._api_toggle.setText("Hide" if checked else "Show")

    def _get_api_key(self) -> str:
        text_value = self._api_key_field.text().strip()
        if text_value:
            return text_value
        env_value = os.getenv("OPENAI_API_KEY", "").strip()
        if env_value:
            return env_value
        stored_value = self._settings.value("api_key", "", type=str).strip()
        if stored_value:
            return stored_value
        return ""


def run_app() -> int:
    """Launch the Deep Organizer GUI application."""

    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")

    window = OrganizerWindow()
    window.show()
    return app.exec()
