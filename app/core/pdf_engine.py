import fitz


class PdfEngine:
    """PDF 切分与整合的无状态操作引擎。"""

    @staticmethod
    def split(input_path: str, page_indices: list[int], output_path: str) -> int:
        """将指定页码提取到新 PDF。

        Args:
            input_path: 源 PDF 路径
            page_indices: 0-indexed 页码列表
            output_path: 输出 PDF 路径

        Returns:
            输出文件的页数

        Raises:
            FileNotFoundError: 源文件不存在
            RuntimeError: PDF 损坏或写入失败
        """
        if not page_indices:
            raise ValueError("至少选择一页")

        src = None
        dst = None
        try:
            src = fitz.open(input_path)
            dst = fitz.open()
            for idx in page_indices:
                dst.insert_pdf(src, from_page=idx, to_page=idx)
            dst.save(output_path)
            return dst.page_count
        except FileNotFoundError:
            raise FileNotFoundError(f"找不到文件: {input_path}")
        except RuntimeError as e:
            raise RuntimeError(f"PDF 处理失败: {e}")
        finally:
            if src:
                src.close()
            if dst:
                dst.close()

    @staticmethod
    def merge(input_paths: list[str], output_path: str) -> int:
        """将多个 PDF 合并为一个。

        Args:
            input_paths: 源 PDF 路径列表（按顺序）
            output_path: 输出 PDF 路径

        Returns:
            输出文件的总页数

        Raises:
            FileNotFoundError: 某个源文件不存在
            RuntimeError: PDF 损坏或写入失败
        """
        if not input_paths:
            raise ValueError("至少添加一个 PDF 文件")

        dst = None
        sources = []
        try:
            dst = fitz.open()
            for path in input_paths:
                src = fitz.open(path)
                sources.append(src)
                dst.insert_pdf(src)
            dst.save(output_path)
            return dst.page_count
        except FileNotFoundError:
            raise FileNotFoundError(f"找不到文件")
        except RuntimeError as e:
            raise RuntimeError(f"PDF 处理失败: {e}")
        finally:
            for s in sources:
                s.close()
            if dst:
                dst.close()

    @staticmethod
    def get_page_count(path: str) -> int:
        """获取 PDF 页数。"""
        doc = None
        try:
            doc = fitz.open(path)
            return doc.page_count
        finally:
            if doc:
                doc.close()
