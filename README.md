# PDF 切分与整合

一个基于 PySide6 + PyMuPDF 的桌面应用，支持可视化地切分和整合 PDF 文件。

## 功能

- **PDF 切分**：加载 PDF 后，通过点击页面缩略图或输入页码范围选择需要的页面，导出为新 PDF
- **PDF 整合**：添加多个 PDF 文件，拖拽调整顺序后合并为一个 PDF
- **页面预览**：异步渲染页面缩略图，支持大文件流畅加载

## 安装

```bash
pip install PySide6 PyMuPDF
```

## 运行

```bash
python main.py
```

## 使用说明

### 切分

1. 点击 **"加载 PDF"** 选择文件
2. 左侧会显示所有页面的缩略图
3. 选择页面（两种方式）：
   - 直接点击缩略图选中/取消
   - 在右侧输入页码范围，如 `1-3,5,7-10`
4. 点击 **"切分并保存"** 导出

### 整合

1. 点击 **"添加 PDF"** 选择多个文件
2. 拖拽列表项调整合并顺序
3. 点击 **"合并并保存"** 导出

## 项目结构

```
PDF-Split-Merge/
├── main.py                          # 入口
├── requirements.txt                 # 依赖
├── app/
│   ├── main_window.py               # 主窗口（Tab 容器）
│   ├── split_tab.py                 # 切分页 UI
│   ├── merge_tab.py                 # 整合页 UI
│   ├── core/
│   │   ├── pdf_engine.py            # PDF 切分/整合逻辑
│   │   └── thumbnail_worker.py      # 异步缩略图渲染线程
│   ├── widgets/
│   │   ├── page_thumbnail.py        # 单页缩略图控件
│   │   ├── thumbnail_grid.py        # 缩略图网格
│   │   ├── pdf_list_item.py         # 整合列表项
│   │   └── drag_list_widget.py      # 可拖拽排序列表
│   └── utils/
│       └── page_range_parser.py     # 页码范围解析
```

## 技术栈

- **GUI**：PySide6 (Qt for Python)
- **PDF 处理**：PyMuPDF (fitz)
- **异步渲染**：QThread + Signal

## 许可证

MIT
