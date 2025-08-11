import pandas as pd
import zipfile
import io
import os

def create_comparison_table(chinese_story, target_story):
    """生成中文与目标语言对照校对表 (Markdown格式)"""
    chinese_lines = chinese_story.strip().split('\n')
    target_lines = target_story.strip().split('\n')

    max_len = max(len(chinese_lines), len(target_lines))

    # 填充以确保列表长度一致
    chinese_lines += [''] * (max_len - len(chinese_lines))
    target_lines += [''] * (max_len - len(target_lines))

    df = pd.DataFrame({
        '序号 (No.)': range(1, max_len + 1),
        '中文原文 (Chinese)': chinese_lines,
        '目标语言翻译 (Target)': target_lines
    })

    return df.to_markdown(index=False)

def generate_package_content(chinese_story, target_story):
    """为单个语言生成仅包含口播稿的下载包内容"""

    # 1. 生成对照表
    table = create_comparison_table(chinese_story, target_story)

    # 2. 组装最终内容
    full_content = (
        f"# 中文与目标语言对照校对表\n\n"
        f"{table}\n\n"
        f"---\n\n"
        f"# 纯目标语言口播稿\n\n"
        f"{target_story}\n"
    )

    return full_content.encode('utf-8')

def create_summary_story_file(source_story, translations):
    """生成多语言口播文案总览文件内容"""
    content = "# 多语言口播文案总览\n\n"
    content += "## 英文原文 (Source)\n\n"
    content += f"{source_story}\n\n---\n\n"

    lang_map = {"chinese": "中文", "english": "英语", "french": "法语", "german": "德语", "spanish": "西班牙语", "portuguese": "葡萄牙语"}
    for lang_code, lang_name in lang_map.items():
        if translations[lang_code]['story']:
            content += f"## {lang_name} ({lang_code.capitalize()})\n\n"
            content += f"{translations[lang_code]['story']}\n\n---\n\n"

    return content.encode('utf-8')

def create_metadata_summary_file(source_metadata_md, translated_metadata_md):
    """生成多语言元数据总览文件内容"""
    content = "# 多语言元数据总览\n\n"
    
    content += "## 英文原文 (Source)\n\n"
    content += f"{source_metadata_md}\n\n"
    content += "---\n\n"
    
    content += "## 各语言翻译 (Translations)\n\n"
    content += f"{translated_metadata_md}\n\n"

    return content.encode('utf-8')

def create_full_zip_package(translations):
    """创建包含所有语言口播稿包的ZIP文件"""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_f:
        # 添加所有语言的口播稿包
        lang_map = {"chinese": "中文", "english": "英语", "french": "法语", "german": "德语", "spanish": "西班牙语", "portuguese": "葡萄牙语"}
        for lang_code, lang_name in lang_map.items():
            if translations[lang_code]['story']:
                package_content = generate_package_content(
                    translations['chinese']['story'],
                    translations[lang_code]['story']
                )
                zip_f.writestr(f"{lang_code}_story_package.md", package_content)

    zip_buffer.seek(0)
    return zip_buffer.getvalue()