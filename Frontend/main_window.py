"""
main_window.py
---------------
PyQt6 dashboard for Social Media Reach Analysis (YouTube Data API v3).

Layout:
  - Top bar: API key + channel handle/ID input, Analyze button
  - Tab 1: Overview  -> summary cards + reach classification
  - Tab 2: Videos    -> sortable table of recent videos
  - Tab 3: Charts    -> views trend line chart + top-videos bar chart
  - Bottom bar: Export CSV / Export PDF

Network calls run on a QThread (Worker) so the UI never freezes.
"""

import os
import sys

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QFrame, QGridLayout,
    QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Allow running this file directly (python Frontend/main_window.py) as well
# as via main.py at the project root.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Backend import youtube_api, analytics, export
from Frontend.theme import DARK_STYLESHEET

EXPORT_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "exports")
MAX_VIDEOS = 25


class AnalysisWorker(QThread):
    """Runs all network calls off the UI thread."""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, api_key: str, identifier: str):
        super().__init__()
        self.api_key = api_key
        self.identifier = identifier

    def run(self):
        try:
            channel_id = youtube_api.resolve_channel_id(self.api_key, self.identifier)
            channel_stats = youtube_api.get_channel_stats(self.api_key, channel_id)
            video_ids = youtube_api.get_recent_video_ids(
                self.api_key, channel_stats["uploads_playlist"], max_results=MAX_VIDEOS
            )
            if not video_ids:
                raise youtube_api.YouTubeAPIError("This channel has no public videos to analyze.")

            raw_videos = youtube_api.get_video_stats(self.api_key, video_ids)
            videos = analytics.enrich_videos(raw_videos)
            summary = analytics.summary_metrics(videos)
            reach_label = analytics.reach_classification(summary["avg_engagement_rate"])

            self.finished.emit({
                "channel_stats": channel_stats,
                "videos": videos,
                "summary": summary,
                "reach_label": reach_label,
            })
        except youtube_api.YouTubeAPIError as exc:
            self.error.emit(str(exc))
        except Exception as exc:  # noqa: BLE001 - surface anything unexpected to the user
            self.error.emit(f"Unexpected error: {exc}")


class MetricCard(QFrame):
    def __init__(self, label: str, value: str = "--"):
        super().__init__()
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        self.value_label = QLabel(value)
        self.value_label.setObjectName("cardValue")
        caption = QLabel(label)
        caption.setObjectName("cardLabel")
        layout.addWidget(self.value_label)
        layout.addWidget(caption)

    def set_value(self, value: str):
        self.value_label.setText(value)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Social Media Reach Analysis — Task 4 (CodTech Internship)")
        self.resize(1100, 720)
        self.setStyleSheet(DARK_STYLESHEET)

        self.current_data = None
        self.worker = None

        self._build_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        # ---- Header ----
        header = QLabel("Social Media Reach Analysis")
        header.setObjectName("headline")
        subheader = QLabel("Powered by YouTube Data API v3 — real channel & video reach metrics")
        subheader.setObjectName("subheadline")
        root.addWidget(header)
        root.addWidget(subheader)

        # ---- Input bar ----
        input_bar = QHBoxLayout()
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("YouTube Data API v3 Key")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.channel_input = QLineEdit()
        self.channel_input.setPlaceholderText("Channel handle (e.g. @MrBeast) or Channel ID")

        self.analyze_btn = QPushButton("Analyze")
        self.analyze_btn.clicked.connect(self.on_analyze_clicked)

        input_bar.addWidget(self.api_key_input, 2)
        input_bar.addWidget(self.channel_input, 2)
        input_bar.addWidget(self.analyze_btn, 1)
        root.addLayout(input_bar)

        self.status_label = QLabel("")
        self.status_label.setObjectName("subheadline")
        root.addWidget(self.status_label)

        # ---- Tabs ----
        self.tabs = QTabWidget()
        self.overview_tab = self._build_overview_tab()
        self.videos_tab = self._build_videos_tab()
        self.charts_tab = self._build_charts_tab()

        self.tabs.addTab(self.overview_tab, "Overview")
        self.tabs.addTab(self.videos_tab, "Videos")
        self.tabs.addTab(self.charts_tab, "Charts")
        root.addWidget(self.tabs, 1)

        # ---- Export bar ----
        export_bar = QHBoxLayout()
        self.export_csv_btn = QPushButton("Export CSV")
        self.export_csv_btn.setObjectName("secondary")
        self.export_csv_btn.clicked.connect(self.on_export_csv)
        self.export_csv_btn.setEnabled(False)

        self.export_pdf_btn = QPushButton("Export PDF Report")
        self.export_pdf_btn.setObjectName("secondary")
        self.export_pdf_btn.clicked.connect(self.on_export_pdf)
        self.export_pdf_btn.setEnabled(False)

        export_bar.addStretch(1)
        export_bar.addWidget(self.export_csv_btn)
        export_bar.addWidget(self.export_pdf_btn)
        root.addLayout(export_bar)

        self.setCentralWidget(central)

    def _build_overview_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.channel_title_label = QLabel("No channel analyzed yet")
        self.channel_title_label.setObjectName("headline")
        layout.addWidget(self.channel_title_label)

        self.reach_label = QLabel("")
        self.reach_label.setObjectName("subheadline")
        layout.addWidget(self.reach_label)

        grid = QGridLayout()
        grid.setSpacing(12)

        self.card_subs = MetricCard("Subscribers")
        self.card_total_views = MetricCard("Total Channel Views")
        self.card_video_count = MetricCard("Total Videos")
        self.card_avg_views = MetricCard(f"Avg Views (last {MAX_VIDEOS})")
        self.card_avg_engagement = MetricCard("Avg Engagement Rate")
        self.card_avg_likes = MetricCard("Avg Likes / Video")

        grid.addWidget(self.card_subs, 0, 0)
        grid.addWidget(self.card_total_views, 0, 1)
        grid.addWidget(self.card_video_count, 0, 2)
        grid.addWidget(self.card_avg_views, 1, 0)
        grid.addWidget(self.card_avg_engagement, 1, 1)
        grid.addWidget(self.card_avg_likes, 1, 2)

        layout.addLayout(grid)
        layout.addStretch(1)
        return tab

    def _build_videos_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Title", "Published", "Views", "Likes", "Comments", "Engagement %"]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)

        layout.addWidget(self.table)
        return tab

    def _build_charts_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.trend_figure = Figure(figsize=(6, 3), facecolor="#121212")
        self.trend_canvas = FigureCanvas(self.trend_figure)

        self.top_figure = Figure(figsize=(6, 3), facecolor="#121212")
        self.top_canvas = FigureCanvas(self.top_figure)

        layout.addWidget(QLabel("Views Trend (recent uploads, chronological)"))
        layout.addWidget(self.trend_canvas)
        layout.addWidget(QLabel("Top 5 Videos by Views"))
        layout.addWidget(self.top_canvas)
        return tab

    # ------------------------------------------------------------- actions
    def on_analyze_clicked(self):
        api_key = self.api_key_input.text().strip()
        identifier = self.channel_input.text().strip()

        if not api_key:
            QMessageBox.warning(self, "Missing API Key", "Please enter your YouTube Data API v3 key.")
            return
        if not identifier:
            QMessageBox.warning(self, "Missing Channel", "Please enter a channel handle or ID.")
            return

        self.analyze_btn.setEnabled(False)
        self.analyze_btn.setText("Analyzing...")
        self.status_label.setText("Fetching live data from YouTube...")

        self.worker = AnalysisWorker(api_key, identifier)
        self.worker.finished.connect(self.on_analysis_finished)
        self.worker.error.connect(self.on_analysis_error)
        self.worker.start()

    def on_analysis_error(self, message: str):
        self.analyze_btn.setEnabled(True)
        self.analyze_btn.setText("Analyze")
        self.status_label.setText("")
        QMessageBox.critical(self, "Analysis Failed", message)

    def on_analysis_finished(self, data: dict):
        self.current_data = data
        self.analyze_btn.setEnabled(True)
        self.analyze_btn.setText("Analyze")
        self.status_label.setText("Analysis complete.")
        self.export_csv_btn.setEnabled(True)
        self.export_pdf_btn.setEnabled(True)

        self._populate_overview(data)
        self._populate_table(data["videos"])
        self._populate_charts(data["videos"])

    def _populate_overview(self, data: dict):
        cs = data["channel_stats"]
        summary = data["summary"]

        self.channel_title_label.setText(cs["title"])
        self.reach_label.setText(f"Reach Classification: {data['reach_label']}")

        self.card_subs.set_value(f"{cs['subscribers']:,}")
        self.card_total_views.set_value(f"{cs['total_views']:,}")
        self.card_video_count.set_value(f"{cs['video_count']:,}")
        self.card_avg_views.set_value(f"{summary['avg_views']:,}")
        self.card_avg_engagement.set_value(f"{summary['avg_engagement_rate']}%")
        self.card_avg_likes.set_value(f"{summary['avg_likes']:,}")

    def _populate_table(self, videos: list):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(videos))
        for row, v in enumerate(videos):
            self.table.setItem(row, 0, QTableWidgetItem(v["title"]))
            self.table.setItem(row, 1, QTableWidgetItem(v.get("published_at", "")[:10]))
            self.table.setItem(row, 2, QTableWidgetItem(str(v["views"])))
            self.table.setItem(row, 3, QTableWidgetItem(str(v["likes"])))
            self.table.setItem(row, 4, QTableWidgetItem(str(v["comments"])))
            self.table.setItem(row, 5, QTableWidgetItem(f"{v['engagement_rate']}"))
        self.table.setSortingEnabled(True)

    def _populate_charts(self, videos: list):
        # Trend line chart
        dates, views = analytics.views_trend(videos)
        self.trend_figure.clear()
        ax = self.trend_figure.add_subplot(111, facecolor="#1A1A1A")
        ax.plot(dates, views, color="#A29BFE", marker="o")
        ax.tick_params(axis="x", colors="#CCCCCC", rotation=45, labelsize=7)
        ax.tick_params(axis="y", colors="#CCCCCC", labelsize=8)
        for spine in ax.spines.values():
            spine.set_color("#333333")
        self.trend_figure.tight_layout()
        self.trend_canvas.draw()

        # Top videos bar chart
        top = analytics.top_videos_by_views(videos, top_n=5)
        labels = [v["title"][:22] + ("..." if len(v["title"]) > 22 else "") for v in top]
        values = [v["views"] for v in top]

        self.top_figure.clear()
        ax2 = self.top_figure.add_subplot(111, facecolor="#1A1A1A")
        ax2.barh(labels[::-1], values[::-1], color="#6C5CE7")
        ax2.tick_params(axis="x", colors="#CCCCCC", labelsize=8)
        ax2.tick_params(axis="y", colors="#CCCCCC", labelsize=8)
        for spine in ax2.spines.values():
            spine.set_color("#333333")
        self.top_figure.tight_layout()
        self.top_canvas.draw()

    def on_export_csv(self):
        if not self.current_data:
            return
        path = export.export_csv(
            self.current_data["videos"], EXPORT_FOLDER, self.current_data["channel_stats"]["title"]
        )
        QMessageBox.information(self, "Exported", f"CSV saved to:\n{path}")

    def on_export_pdf(self):
        if not self.current_data:
            return
        top = analytics.top_videos_by_views(self.current_data["videos"], top_n=5)
        path = export.export_pdf(
            self.current_data["channel_stats"],
            self.current_data["summary"],
            top,
            self.current_data["reach_label"],
            EXPORT_FOLDER,
        )
        QMessageBox.information(self, "Exported", f"PDF report saved to:\n{path}")


def run():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
