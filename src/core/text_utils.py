"""文字处理工具类"""

from PIL import ImageFont

FontType = ImageFont.FreeTypeFont | ImageFont.ImageFont


class TextProcessor:
    """文字处理器，处理文字的截断"""

    @staticmethod
    def get_text_size(text: str, font: FontType) -> tuple[int, int]:
        """获取文字的尺寸"""
        bbox = font.getbbox(text)
        return int(bbox[2] - bbox[0]), int(bbox[3] - bbox[1])

    @staticmethod
    def truncate_text(
        text: str, font: FontType, max_width: int, suffix: str = "..."
    ) -> str:
        """截断文字，确保总宽度不超过限制"""
        if not text:
            return text

        # 检查原文字是否需要截断
        text_width, _ = TextProcessor.get_text_size(text, font)
        if text_width <= max_width:
            return text

        # 获取后缀的宽度
        suffix_width, _ = TextProcessor.get_text_size(suffix, font)
        available_width = max_width - suffix_width

        if available_width <= 0:
            # 如果连后缀都放不下，返回空字符串或尽可能短的后缀
            return suffix[:1] if suffix else ""

        # 二分查找最佳截断位置
        left, right = 0, len(text)
        result = ""

        while left <= right:
            mid = (left + right) // 2
            test_text = text[:mid]
            test_width, _ = TextProcessor.get_text_size(test_text, font)

            if test_width <= available_width:
                result = test_text
                left = mid + 1
            else:
                right = mid - 1

        return result + suffix

    @staticmethod
    def process_text(
        text: str,
        font: FontType,
        max_width: int | None,
        truncate_suffix: str = "...",
    ) -> str:
        """处理文字，返回截断后的文字"""
        if not text or max_width is None:
            return text if text else ""

        return TextProcessor.truncate_text(text, font, max_width, truncate_suffix)

    @staticmethod
    def get_processed_text_size(
        text: str,
        font: FontType,
        max_width: int | None,
        truncate_suffix: str = "...",
    ) -> tuple[int, int]:
        """获取处理后文字的总尺寸"""
        processed_text = TextProcessor.process_text(
            text, font, max_width, truncate_suffix
        )

        if not processed_text:
            return 0, 0

        return TextProcessor.get_text_size(processed_text, font)
