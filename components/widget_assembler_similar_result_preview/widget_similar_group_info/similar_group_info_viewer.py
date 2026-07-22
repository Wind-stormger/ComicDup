from typing import Dict

import lzytools_Qt
from PySide6.QtCore import Signal
from PySide6.QtGui import QMouseEvent, Qt
from PySide6.QtWidgets import (QWidget, QApplication, QToolButton,
                                QVBoxLayout, QHBoxLayout, QLabel, QFrame)

from common.class_sign import TYPE_SIGN_STATUS
from components.widget_assembler_similar_result_preview.widget_similar_group_info.res.icon_base64 import ICON_ZOOM_IN
from components.widget_assembler_similar_result_preview.widget_similar_group_info.res.ui_similar_group_info import \
    Ui_Form


class SimilarGroupInfoViewer(QWidget):
    """单个相似组信息模块的界面组件"""
    Preview = Signal(name='预览相似组')
    TableDelete = Signal(object, name='表格-删除漫画')
    TableOpenPath = Signal(object, name='表格-打开路径')
    TableRefreshInfo = Signal(object, name='表格-刷新信息')

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # 设置图标
        self.ui.toolButton_preview.setIcon(lzytools_Qt.convert_base64_image_to_pixmap(ICON_ZOOM_IN))
        self.ui.toolButton_preview.clicked.connect(self.Preview.emit)

        # 存储表格行映射: filepath -> row(QFrame)
        self._table_rows: Dict[str, QFrame] = {}

        # 初始化对比表格（默认折叠）
        self._init_comparison_table()

    # ── 现有方法 ──────────────────────────────────────────

    def set_group_index(self, index: int):
        """设置当前组的编号"""
        self.ui.label_index.setText(str(index))

    def set_item_count(self, count: int):
        """设置当前组内部项目的总数"""
        self.ui.label_item_count.setText(str(count))

    def set_item_size(self, size: str):
        """设置当前组内部项目的文件大小统计"""
        self.ui.label_size_count.setText(size)

    def set_group_sign(self, sign: TYPE_SIGN_STATUS):
        """设置当前组的标记"""
        sign_str = sign.text
        self.ui.label_sign.setText(sign_str)

    def add_widget(self, widget: QWidget):
        """添加漫画项控件"""
        layout = self.ui.scrollAreaWidgetContents_similar_group.layout()
        layout.addWidget(widget)

    def remove_widget(self, widget: QWidget):
        """删除漫画项控件"""
        layout = self.ui.scrollAreaWidgetContents_similar_group.layout()
        layout.removeWidget(widget)
        widget.deleteLater()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.Preview.emit()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    # ── 对比表格方法 ──────────────────────────────────────

    def _init_comparison_table(self):
        """初始化对比表格（头部折叠按钮 + 表格容器）"""
        # 在头部栏末尾追加折叠按钮
        self.toolButton_toggle_table = QToolButton()
        self.toolButton_toggle_table.setText("表格 ▼")
        self.toolButton_toggle_table.setToolTip("展开/折叠对比表格")
        self.ui.horizontalLayout.addWidget(self.toolButton_toggle_table)
        self.toolButton_toggle_table.clicked.connect(self._toggle_table)

        # 分隔线（位于卡片区和表格之间）
        self._separator = QFrame(self)
        self._separator.setFrameShape(QFrame.Shape.HLine)
        self._separator.setFrameShadow(QFrame.Shadow.Sunken)
        self.ui.verticalLayout.addWidget(self._separator)
        self._separator.setVisible(False)

        # 表格容器
        self.widget_comparison_table = QWidget(self)
        self.widget_comparison_table.setObjectName("widget_comparison_table")
        self._layout_table = QVBoxLayout(self.widget_comparison_table)
        self._layout_table.setContentsMargins(3, 3, 3, 3)
        self._layout_table.setSpacing(0)
        self.widget_comparison_table.setVisible(False)

        # 添加到根布局末尾
        self.ui.verticalLayout.addWidget(self.widget_comparison_table)

    def _toggle_table(self):
        """切换表格显隐"""
        visible = not self.widget_comparison_table.isVisible()
        self.widget_comparison_table.setVisible(visible)
        self._separator.setVisible(visible)
        self.toolButton_toggle_table.setText("表格 ▲" if visible else "表格 ▼")

    def clear_table(self):
        """清空所有表格行"""
        for row in self._table_rows.values():
            row.deleteLater()
        self._table_rows.clear()

    def add_table_row(self, comic_info, color: str = None, similarity: str = None):
        """添加一行对比表格"""
        from common import function_file
        from common.class_config import FileType
        from components.widget_assembler_similar_result_preview.widget_comic_info.res.icon_base64 import \
            ICON_JUMP_TO, ICON_REFRESH, ICON_DELETE
        from components.widget_search_list.res.icon_base64 import \
            ICON_FOLDER, ICON_ARCHIVE

        filepath = comic_info.filepath

        # ── 行容器 ──
        row_frame = QFrame()
        row_frame.setFrameShape(QFrame.Shape.HLine)
        row_frame.setFrameShadow(QFrame.Shadow.Plain)
        row_layout = QHBoxLayout(row_frame)
        row_layout.setContentsMargins(6, 4, 6, 4)
        row_layout.setSpacing(12)

        # ── 第1列：信息区 (stretch=1) ──
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        # 图标+标题
        title_line = QHBoxLayout()
        title_line.setSpacing(4)
        icon_label = QLabel()
        filetype = comic_info.filetype
        if isinstance(filetype, FileType.Folder):
            icon = ICON_FOLDER
        elif isinstance(filetype, FileType.Archive):
            icon = ICON_ARCHIVE
        else:
            icon = None
        if icon:
            icon_label.setPixmap(
                lzytools_Qt.convert_base64_image_to_pixmap(icon))
        title_line.addWidget(icon_label)

        title_label = QLabel(comic_info.filetitle)
        title_label.setWordWrap(True)
        title_style = "font-weight: bold;"
        if color:
            title_style += f" color: {color};"
        title_label.setStyleSheet(title_style)
        title_line.addWidget(title_label, 1)  # stretch=1 撑满
        info_layout.addLayout(title_line)

        # 父目录路径
        path_label = QLabel(comic_info.parent_dirpath)
        path_label.setWordWrap(True)
        path_style = "color: #888888;"
        if color:
            path_style = f"color: {color};"
        path_label.setStyleSheet(path_style)
        info_layout.addWidget(path_label)

        # 页数 + 文件大小 + 相似度
        stats_line = QHBoxLayout()
        stats_line.setSpacing(8)
        page_label = QLabel(str(comic_info.page_count))
        page_ye = QLabel("页")
        size_label = QLabel(function_file.format_bytes_size(
            comic_info.filesize_bytes))
        stats_line.addWidget(page_label)
        stats_line.addWidget(page_ye)
        stats_line.addWidget(size_label)

        if similarity:
            sim_label = QLabel(similarity)
            sim_val = float(similarity.replace('%', ''))
            if sim_val >= 90:
                sim_label.setStyleSheet("color: green;")
            elif sim_val >= 80:
                sim_label.setStyleSheet("color: blue;")
            stats_line.addWidget(sim_label)

        stats_line.addStretch()
        if color:
            page_label.setStyleSheet(f"color: {color};")
            page_ye.setStyleSheet(f"color: {color};")
            size_label.setStyleSheet(f"color: {color};")
        info_layout.addLayout(stats_line)

        row_layout.addLayout(info_layout, 1)  # stretch=1

        # ── 第2列：操作按钮区 ──
        btn_column = QVBoxLayout()
        btn_column.setSpacing(4)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        btn_open = QToolButton()
        btn_open.setIcon(
            lzytools_Qt.convert_base64_image_to_pixmap(ICON_JUMP_TO))
        btn_open.setToolTip("打开路径")
        btn_open.clicked.connect(lambda: self.TableOpenPath.emit(comic_info))

        btn_refresh = QToolButton()
        btn_refresh.setIcon(
            lzytools_Qt.convert_base64_image_to_pixmap(ICON_REFRESH))
        btn_refresh.setToolTip("刷新信息")
        btn_refresh.clicked.connect(
            lambda: self.TableRefreshInfo.emit(comic_info))

        btn_delete = QToolButton()
        btn_delete.setIcon(
            lzytools_Qt.convert_base64_image_to_pixmap(ICON_DELETE))
        btn_delete.setToolTip("删除漫画")
        btn_delete.clicked.connect(lambda: self.TableDelete.emit(comic_info))

        btn_row.addWidget(btn_open)
        btn_row.addWidget(btn_refresh)
        btn_row.addWidget(btn_delete)
        btn_column.addLayout(btn_row)
        btn_column.addStretch()

        row_layout.addLayout(btn_column)

        # 注册到布局和映射表
        self._layout_table.addWidget(row_frame)
        self._table_rows[filepath] = row_frame

    def remove_table_row(self, comic_info):
        """删除指定漫画对应的表格行"""
        filepath = comic_info.filepath
        row = self._table_rows.pop(filepath, None)
        if row:
            self._layout_table.removeWidget(row)
            row.deleteLater()


if __name__ == "__main__":
    app_ = QApplication()
    program_ui = SimilarGroupInfoViewer()
    program_ui.show()
    app_.exec()
