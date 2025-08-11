from crewai import Task

class SeoTasks:
    def create_seo_task(self, agent, outline, story):
        return Task(
            description=f"""
                基于以下视频大纲和英文口播稿，为YouTube视频生成优化的元数据。

                **视频大纲：**
                {outline}

                **英文口播稿：**
                {story}

                **产出要求：**
                - **Title (标题):** 必须引人注目，包含核心关键词，长度建议在50-70字符之间。
                - **Description (描述):** 详细介绍视频内容，自然地融入关键词，并可以包含相关链接或时间戳。
                - **Tags (标签):** 提供一组相关的关键词标签，用逗号分隔。
                - **重要：** 将以上三项内容组织成一个结构清晰的Markdown文本块。
            """,
            expected_output="一份包含Title, Description, 和 Tags的、格式清晰的Markdown文本。",
            agent=agent
        )