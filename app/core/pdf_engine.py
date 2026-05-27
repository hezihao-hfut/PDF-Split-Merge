import io
import fitz
from PIL import Image


def _compress_images(doc, jpeg_quality: int = 65, progress_cb=None):
    """遍历所有页面，将图片重编码为低质量 JPEG 以减小体积。"""
    total = doc.page_count
    xref_cache: dict[int, bytes] = {}
    for page_num in range(total):
        page = doc[page_num]
        images = page.get_images(full=True)
        for img_info in images:
            xref = img_info[0]
            if xref in xref_cache:
                compressed = xref_cache[xref]
            else:
                try:
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n > 4:  # CMYK 等，转为 RGB
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    pil_img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                    buf = io.BytesIO()
                    pil_img.save(buf, format="JPEG", quality=jpeg_quality, optimize=True)
                    compressed = buf.getvalue()
                    xref_cache[xref] = compressed
                except Exception:
                    continue
            try:
                page.replace_image(xref, stream=compressed)
            except Exception:
                pass
        if progress_cb:
            progress_cb(page_num + 1, total)


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
            dst.save(output_path, garbage=4, deflate=True)
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
    def merge(input_paths: list[str], output_path: str,
              page_ranges: list[list[int] | None] | None = None) -> int:
        """将多个 PDF 合并为一个。

        Args:
            input_paths: 源 PDF 路径列表（按顺序）
            output_path: 输出 PDF 路径
            page_ranges: 每个文件的 0-indexed 页码列表，None 表示全部页

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
            for i, path in enumerate(input_paths):
                src = fitz.open(path)
                sources.append(src)
                pages = page_ranges[i] if page_ranges and i < len(page_ranges) else None
                if pages:
                    for idx in pages:
                        dst.insert_pdf(src, from_page=idx, to_page=idx)
                else:
                    dst.insert_pdf(src)
            dst.save(output_path, garbage=4, deflate=True)
            return dst.page_count
        except FileNotFoundError:
            raise FileNotFoundError("找不到文件")
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

    @staticmethod
    def compress(input_path: str, output_path: str, quality: int = 1,
                 progress_cb=None) -> None:
        """压缩 PDF 文件。

        Args:
            input_path: 源 PDF 路径
            output_path: 输出路径
            quality: 0=低(最小体积), 1=中(推荐), 2=高(最佳质量)
            progress_cb: 可选回调 (current_page, total_pages)
        """
        doc = None
        try:
            doc = fitz.open(input_path)
            total = doc.page_count

            if quality == 0:
                # 低质量：重压缩图片为低质量 JPEG
                _compress_images(doc, jpeg_quality=40, progress_cb=progress_cb)
            elif quality == 1:
                # 中等质量：适度压缩图片
                _compress_images(doc, jpeg_quality=65, progress_cb=progress_cb)
            else:
                # 高质量：仅回调进度
                if progress_cb:
                    for i in range(total):
                        progress_cb(i + 1, total)

            save_opts = {
                "garbage": 4,
                "deflate": True,
                "clean": True,
            }
            doc.save(output_path, **save_opts)
        except FileNotFoundError:
            raise FileNotFoundError(f"找不到文件: {input_path}")
        except RuntimeError as e:
            raise RuntimeError(f"PDF 处理失败: {e}")
        finally:
            if doc:
                doc.close()
