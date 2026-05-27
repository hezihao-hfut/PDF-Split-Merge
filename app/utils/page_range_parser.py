import re


def parse_page_ranges(text: str, max_page: int) -> tuple[list[int], list[str]]:
    """解析页码范围字符串，返回 (0-indexed 页码列表, 错误信息列表)。

    支持格式: "1-3,5,7-10" -> [0,1,2,4,6,7,8,9]
    """
    text = text.strip()
    if not text:
        return [], ["页码范围不能为空"]

    indices: list[int] = []
    errors: list[str] = []
    seen: set[int] = set()

    parts = [p.strip() for p in text.split(",") if p.strip()]
    for part in parts:
        m = re.fullmatch(r"(\d+)\s*-\s*(\d+)", part)
        if m:
            start, end = int(m.group(1)), int(m.group(2))
            if start > end:
                errors.append(f"'{part}': 起始页不能大于结束页")
                continue
            if start < 1:
                errors.append(f"'{part}': 页码不能小于 1")
                continue
            if end > max_page:
                errors.append(f"'{part}': 页码超出范围 (最大 {max_page})")
                continue
            for i in range(start, end + 1):
                if i - 1 not in seen:
                    seen.add(i - 1)
                    indices.append(i - 1)
        elif part.isdigit():
            page = int(part)
            if page < 1:
                errors.append(f"'{part}': 页码不能小于 1")
            elif page > max_page:
                errors.append(f"'{part}': 页码超出范围 (最大 {max_page})")
            elif page - 1 not in seen:
                seen.add(page - 1)
                indices.append(page - 1)
        else:
            errors.append(f"'{part}': 无效的页码格式")

    indices.sort()
    return indices, errors


def indices_to_range_text(indices: list[int]) -> str:
    """将 0-indexed 页码列表转为可读的范围字符串。

    [0,1,2,4,6,7,8,9] -> "1-3,5,7-10"
    """
    if not indices:
        return ""
    ranges: list[str] = []
    start = indices[0]
    end = start
    for i in indices[1:]:
        if i == end + 1:
            end = i
        else:
            ranges.append(_format_range(start, end))
            start = end = i
    ranges.append(_format_range(start, end))
    return ",".join(ranges)


def _format_range(start: int, end: int) -> str:
    if start == end:
        return str(start + 1)
    return f"{start + 1}-{end + 1}"
