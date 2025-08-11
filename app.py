import streamlit as st
import os
from dotenv import load_dotenv
from crewai import Crew, LLM, Process

from src.agents.outline_agent import OutlineAgent
from src.agents.story_agent import StoryAgent
from src.agents.seo_agent import SeoAgent
from src.agents.translation_agent import TranslationAgent
from src.tasks.outline_tasks import OutlineTasks
from src.tasks.story_tasks import StoryTasks
from src.tasks.seo_tasks import SeoTasks
from src.tasks.translation_tasks import TranslationTasks
from src.utils.file_handler import (
    generate_package_content,
    create_summary_story_file,
    create_metadata_summary_file,
    create_full_zip_package
)

# 加载环境变量
load_dotenv()

st.set_page_config(page_title="YouTube Creator's Copilot", layout="wide")

st.title("YouTube口播稿一站式创作平台")

# --- 辅助函数 ---
def get_llm_config(agent_prefix):
    """根据Agent前缀智能获取LLM配置，支持回退到全局默认值"""
    model = os.getenv(f"{agent_prefix}_MODEL", os.getenv("DEFAULT_OPENAI_MODEL_NAME"))
    api_base = os.getenv(f"{agent_prefix}_API_BASE", os.getenv("DEFAULT_OPENAI_API_BASE"))
    api_key = os.getenv(f"{agent_prefix}_API_KEY", os.getenv("DEFAULT_OPENAI_API_KEY"))
    return LLM(model=f"openai/{model}", base_url=api_base, api_key=api_key)


# --- Session State 初始化 ---
if 'current_step' not in st.session_state:
    st.session_state.current_step = 1
if 'outline' not in st.session_state:
    st.session_state.outline = ""
if 'story' not in st.session_state:
    st.session_state.story = ""
if 'metadata' not in st.session_state:
    st.session_state.metadata = "" # Store as a raw Markdown string
if 'translated_metadata' not in st.session_state:
    st.session_state.translated_metadata = "" # Store as a raw Markdown string for all languages
if 'translations' not in st.session_state:
    st.session_state.translations = {
        "chinese": {"story": ""},
        "english": {"story": ""},
        "french": {"story": ""},
        "german": {"story": ""},
        "spanish": {"story": ""},
        "portuguese": {"story": ""},
    }
# ... 其他状态的初始化

# --- UI 渲染 ---

# 步骤一：大纲生成
st.sidebar.header("第一步：生成视频大纲")
uploaded_file = st.sidebar.file_uploader(
    "上传参考资料 (.md 或 .txt)",
    type=['md', 'txt']
)
topic_input = st.sidebar.text_area(
    "或者，直接输入您的核心主题",
    height=150
)

if st.sidebar.button("生成大纲"):
    if uploaded_file is not None or topic_input:
        with st.spinner("🤖 大纲创作团队正在协作中，请稍候..."):
            # 根据输入准备 topic 和 context
            topic = topic_input if topic_input else uploaded_file.name
            context = None
            if uploaded_file is not None:
                context = uploaded_file.read().decode("utf-8")

            # 1. 为所有Agent配置同一个LLM（也可以按需分别配置）
            outline_llm = get_llm_config('OUTLINE_AGENT')

            # 2. 实例化所有新的 Agent 和 Task
            agents = OutlineAgent()
            tasks = OutlineTasks()

            # 创建Agents
            #researcher_agent = agents.researcher(llm=outline_llm)
            structurer_agent = agents.structurer(llm=outline_llm)
            #refiner_agent = agents.refiner(llm=outline_llm)

            # 创建Tasks，并建立依赖关系
            research_task_obj = tasks.research_task(structurer_agent, topic, context)
            #structure_task_obj = tasks.structure_task(structurer_agent, context_task=research_task_obj)
            #refine_task_obj = tasks.refine_task(refiner_agent, context_task=structure_task_obj)

            # 3. 组建并运行新的 Crew
            crew = Crew(
                # agents=[researcher_agent, structurer_agent, refiner_agent],
                # tasks=[research_task_obj, structure_task_obj, refine_task_obj],
                agents=[structurer_agent],
                tasks=[research_task_obj],
                verbose=True,
                process=Process.sequential
            )
            
            result = crew.kickoff()
            st.session_state.outline = result.raw if hasattr(result, 'raw') else result
    else:
        st.sidebar.error("请输入主题或上传文件！")

st.subheader("1. 视频大纲")
outline_text = st.text_area(
    "请在此处编辑和完善您的视频大纲：",
    value=st.session_state.outline,
    height=300
)

if st.button("确认大纲，进入下一步"):
    st.session_state.outline = outline_text # 保存最终修改
    st.session_state.current_step = 2
    st.success("大纲已确认！请在侧边栏进入第二步。")
    # st.experimental_rerun() # 强制刷新以更新UI状态

# --- 步骤二：英文口播稿生成 ---
if st.session_state.current_step >= 2:
    st.sidebar.header("第二步：生成英文口播稿")

    # 动态扫描文风库
    style_files = ["无"] + [f for f in os.listdir("style_library") if f.endswith(('.txt', '.md'))]
    selected_style = st.sidebar.selectbox("从文风库选择", options=style_files)

    uploaded_style_file = st.sidebar.file_uploader(
        "或，临时上传文风参考 (支持中文或英文文本)",
        type=['md', 'txt'],
        help="上传的文风参考将用于指导中文口播稿的创作风格、结构和表达方式"
    )

    if st.sidebar.button("生成中文口播稿"):
        with st.spinner("✍️ 中文口播稿撰写师正在创作中，请稍候..."):
            # 1. 处理文风指南
            style_guide = None
            if uploaded_style_file is not None:
                style_guide = uploaded_style_file.read().decode("utf-8")
            elif selected_style != "无":
                with open(os.path.join("style_library", selected_style), "r", encoding="utf-8") as f:
                    style_guide = f.read()

            # 2. 配置LLM和创建Agent/Task
            story_llm = get_llm_config('STORY_AGENT')
            agents = StoryAgent()
            tasks = StoryTasks()

            writer_agent = agents.writer(llm=story_llm)
            story_task = tasks.create_story_task(writer_agent, st.session_state.outline, style_guide)

            # 3. 组建并运行Crew
            crew = Crew(
                agents=[writer_agent],
                tasks=[story_task],
                verbose=True,
                process=Process.sequential
            )
            result = crew.kickoff()
            st.session_state.story = result.raw if hasattr(result, 'raw') else result

    st.subheader("2. 中文口播稿 (Chinese Story)")
    story_text = st.text_area(
        "请在此处编辑您的中文口播稿：",
        value=st.session_state.story,
        height=400
    )

    if st.button("确认中文稿，进入下一步"):
        st.session_state.story = story_text
        st.session_state.current_step = 3
        st.success("中文稿已确认！请在侧边栏进入第三步。")
        # st.experimental_rerun()

# --- 步骤三：视频元数据生成 ---
if st.session_state.current_step >= 3:
    st.sidebar.header("第三步：生成视频元数据")
    if st.sidebar.button("生成元数据 (Title, Desc, Tags)"):
        with st.spinner("📈 SEO专家正在优化中，请稍候..."):
            # 1. 配置LLM和创建Agent/Task
            seo_llm = get_llm_config('SEO_AGENT')
            agents = SeoAgent()
            tasks = SeoTasks()

            seo_agent = agents.expert(llm=seo_llm)
            seo_task = tasks.create_seo_task(seo_agent, st.session_state.outline, st.session_state.story)

            # 2. 组建并运行Crew
            crew = Crew(
                agents=[seo_agent],
                tasks=[seo_task],
                verbose=True
            )
            result = crew.kickoff()
            
            # 3. 直接将原始Markdown字符串存入session_state
            st.session_state.metadata = result.raw if hasattr(result, 'raw') else result

    st.subheader("3. 视频元数据 (Metadata)")
    metadata_markdown_str = st.text_area(
        "编辑元数据 (Markdown格式)",
        value=st.session_state.metadata,
        height=250
    )

    if st.button("确认元数据，进入下一步"):
        st.session_state.metadata = metadata_markdown_str # 保存编辑后的字符串
        st.session_state.current_step = 4
        st.success("元数据已确认！请在侧边栏进入第四步。")
        # st.experimental_rerun()

# --- 步骤四：多语言翻译 ---
if st.session_state.current_step >= 4:
    st.sidebar.header("第四步：多语言翻译")

    # --- 阶段一：口播稿翻译 ---
    st.sidebar.subheader("阶段一：口播稿翻译")

    # 将中文稿存储到translations中
    if st.session_state.story and not st.session_state.translations['chinese']['story']:
        st.session_state.translations['chinese']['story'] = st.session_state.story

    # 多语言翻译 - 基于中文稿进行翻译
    chinese_story_available = bool(st.session_state.story)
    languages = {"english": "英语", "french": "法语", "german": "德语", "spanish": "西班牙语", "portuguese": "葡萄牙语"}
    for lang_code, lang_name in languages.items():
        if st.sidebar.button(f"生成{lang_name}稿", key=f"translate_{lang_code}", disabled=not chinese_story_available):
            with st.spinner(f"🌍 正在翻译为{lang_name}..."):
                trans_llm = get_llm_config('TRANSLATION_AGENT')
                agents = TranslationAgent()
                tasks = TranslationTasks()
                translator_agent = agents.translator(llm=trans_llm)
                # 使用中文稿作为翻译源
                translate_task_obj = tasks.translate_story_task(translator_agent, st.session_state.story, lang_name)
                crew = Crew(agents=[translator_agent], tasks=[translate_task_obj], verbose=True)
                result = crew.kickoff()
                st.session_state.translations[lang_code]['story'] = result.raw if hasattr(result, 'raw') else result
                st.success(f"{lang_name}稿生成成功！")

    # --- 阶段二：元数据翻译 ---
    st.sidebar.subheader("阶段二：元数据翻译")
    if st.sidebar.button("一键翻译所有元数据", disabled=not st.session_state.metadata):
        with st.spinner("📜 正在一键翻译所有元数据..."):
            trans_llm = get_llm_config('TRANSLATION_AGENT')
            agents = TranslationAgent()
            tasks = TranslationTasks()
            translator_agent = agents.translator(llm=trans_llm)
            metadata_task = tasks.translate_metadata_task(translator_agent, st.session_state.metadata)
            
            crew = Crew(agents=[translator_agent], tasks=[metadata_task], verbose=True)
            result = crew.kickoff()
            
            # 直接存储返回的Markdown文本
            st.session_state.translated_metadata = result.raw if hasattr(result, 'raw') else result
            st.success("所有元数据翻译完成！")

    # --- 主页面展示翻译结果 ---
    st.subheader("4. 多语言内容")

    # 展示所有翻译后的元数据
    if st.session_state.translated_metadata:
        st.markdown("#### 翻译后的元数据")
        st.text_area(
            "所有语言的元数据预览",
            value=st.session_state.translated_metadata,
            height=300,
            disabled=True
        )

    # 中文（原文）
    with st.expander("中文 (Chinese) - 原文"):
        chinese_story = st.session_state.story if st.session_state.story else st.session_state.translations['chinese']['story']
        st.text_area("口播稿", value=chinese_story, height=200, key="zh_story_display")
        st.download_button(
            "下载中文稿",
            data=generate_package_content(
                chinese_story,
                chinese_story
            ),
            file_name="chinese_story_package.md",
            disabled=not chinese_story
        )

    # 其他语言
    for lang_code, lang_name in languages.items():
        with st.expander(f"{lang_name} ({lang_code.capitalize()})"):
            st.text_area(f"{lang_name}口播稿", value=st.session_state.translations[lang_code]['story'], height=200, key=f"{lang_code}_story_display")
            chinese_story = st.session_state.story if st.session_state.story else st.session_state.translations['chinese']['story']
            st.download_button(
                f"下载{lang_name}稿",
                data=generate_package_content(
                    chinese_story,
                    st.session_state.translations[lang_code]['story']
                ),
                file_name=f"{lang_code}_story_package.md",
                disabled=not st.session_state.translations[lang_code]['story']
            )

# --- 步骤五：汇总下载 ---
if st.session_state.current_step >= 4 and st.session_state.story:
    st.header("第五步：汇总下载")
    st.info("所有任务已完成！您现在可以下载汇总文件或包含所有语言包的ZIP文件。")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            label="下载多语言口播文案总览",
            data=create_summary_story_file(st.session_state.story, st.session_state.translations),
            file_name="summary_stories.md",
            mime="text/markdown",
        )

    with col2:
        st.download_button(
            label="下载多语言元数据总览",
            data=create_metadata_summary_file(st.session_state.metadata, st.session_state.translated_metadata),
            file_name="summary_metadata.md",
            mime="text/markdown",
        )

    with col3:
        st.download_button(
            label="一键下载全部分发包 (.zip)",
            data=create_full_zip_package(
                st.session_state.translations
            ),
            file_name="youtube_story_packages.zip",
            mime="application/zip",
        )
