from crewai import Task

class TranslationTasks:
    def translate_story_task(self, agent, chinese_story, target_language):
        return Task(
            description=f"""
                将以下中文口播稿，准确地翻译成指定的语言：{target_language}。

                **产出要求：**
                - 翻译必须准确、自然、流畅。
                - 返回纯文本格式的翻译稿件。
                - 翻译的段落数量和行数应与原始中文稿保持一致，以便生成对照表格。
                - 请你直接生成，不要问我任何问题。

                **原始中文稿 (Source Story):**
                {chinese_story}
            """,
            expected_output="一篇准确、流畅的{target_language}翻译稿。",
            agent=agent
        )

    def translate_metadata_task(self, agent, metadata):
        return Task(
            description=f"""
                将以下中文元数据（包含Title, Description, Tags），高质量地翻译成五种语言：
                英语、法语、德语、西班牙语、葡萄牙语。

                **产出要求：**
                - 对每种语言，都提供一个包含'title', 'description', 'tags'的翻译版本。
                - 将所有五种语言的翻译结果，组织成一个结构清晰的Markdown文本块。
                  每个语言占一个部分，并用三级标题（###）明确标识，例如：'### 中文 (Chinese)'。

                **原始元数据:**
                {metadata}
            """,
            expected_output="一份包含五种目标语言元数据翻译的、格式清晰的Markdown文本。",
            agent=agent
        )