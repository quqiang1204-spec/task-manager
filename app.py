"""
日程任务管理应用 - Streamlit 版
支持：日历视图、任务管理、数据统计
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json

# 页面配置
st.set_page_config(
    page_title="我的日程任务管理",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 数据库初始化
DB_PATH = "task_manager.db"

def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 任务表
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT DEFAULT '工作',
            priority TEXT DEFAULT '中',
            due_date TEXT,
            completed INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT
        )
    ''')
    
    # 日程表
    c.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            event_date TEXT NOT NULL,
            event_time TEXT,
            repeat TEXT DEFAULT '不重复',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# 样式优化
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .task-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .completed-task {
        text-decoration: line-through;
        color: #6c757d;
    }
</style>
""", unsafe_allow_html=True)

# 侧边栏导航
st.sidebar.title("📊 导航")
page = st.sidebar.radio(
    "选择页面",
    ["🏠 首页", "✅ 任务管理", "📅 日程管理", "📊 数据统计", "⚙️ 设置"],
    label_visibility="collapsed"
)

# ==================== 首页 ====================
if page == "🏠 首页":
    st.markdown('<p class="main-header">📅 我的日程任务管理</p>', unsafe_allow_html=True)
    
    # 统计概览
    conn = sqlite3.connect(DB_PATH)
    
    # 任务统计
    total_tasks = pd.read_sql("SELECT COUNT(*) as count FROM tasks", conn).iloc[0]['count']
    completed_tasks = pd.read_sql("SELECT COUNT(*) as count FROM tasks WHERE completed=1", conn).iloc[0]['count']
    pending_tasks = total_tasks - completed_tasks
    
    # 今日日程
    today = datetime.now().strftime("%Y-%m-%d")
    today_events = pd.read_sql(f"SELECT COUNT(*) as count FROM events WHERE event_date='{today}'", conn).iloc[0]['count']
    
    conn.close()
    
    # 展示统计卡片
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📋 总任务", total_tasks)
    with col2:
        st.metric("✅ 已完成", completed_tasks)
    with col3:
        st.metric("⏳ 待完成", pending_tasks)
    with col4:
        st.metric("📅 今日日程", today_events)
    
    st.divider()
    
    # 快速添加
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("⚡ 快速添加任务")
        quick_task = st.text_input("任务标题", placeholder="输入任务名称...")
        if st.button("添加任务", key="quick_add_task"):
            if quick_task:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("INSERT INTO tasks (title) VALUES (?)", (quick_task,))
                conn.commit()
                conn.close()
                st.success(f"✅ 已添加任务：{quick_task}")
                st.rerun()
    
    with col_right:
        st.subheader("⚡ 快速添加日程")
        quick_event = st.text_input("日程标题", placeholder="输入日程名称...")
        quick_date = st.date_input("日期", datetime.now())
        if st.button("添加日程", key="quick_add_event"):
            if quick_event:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("INSERT INTO events (title, event_date) VALUES (?, ?)", 
                         (quick_event, quick_date.strftime("%Y-%m-%d")))
                conn.commit()
                conn.close()
                st.success(f"✅ 已添加日程：{quick_event}")
                st.rerun()
    
    st.divider()
    
    # 今日待办
    st.subheader("📌 今日待办")
    conn = sqlite3.connect(DB_PATH)
    tasks_df = pd.read_sql("""
        SELECT id, title, priority, due_date, completed 
        FROM tasks 
        WHERE completed=0 
        ORDER BY 
            CASE priority 
                WHEN '高' THEN 1 
                WHEN '中' THEN 2 
                WHEN '低' THEN 3 
            END,
            due_date
    """, conn)
    conn.close()
    
    if not tasks_df.empty:
        for _, task in tasks_df.iterrows():
            col_task, col_action = st.columns([4, 1])
            with col_task:
                priority_emoji = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(task['priority'], "⚪")
                due_str = f" | 截止：{task['due_date']}" if task['due_date'] else ""
                st.write(f"{priority_emoji} {task['title']}{due_str}")
            with col_action:
                if st.button("完成", key=f"complete_{task['id']}"):
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute("""
                        UPDATE tasks 
                        SET completed=1, completed_at=CURRENT_TIMESTAMP 
                        WHERE id=?
                    """, (task['id'],))
                    conn.commit()
                    conn.close()
                    st.rerun()
    else:
        st.info("🎉 暂无待办任务！")

# ==================== 任务管理 ====================
elif page == "✅ 任务管理":
    st.title("✅ 任务管理")
    
    # 添加任务表单
    with st.expander("➕ 添加新任务", expanded=False):
        with st.form("add_task_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_title = st.text_input("任务标题 *", placeholder="必填")
                new_category = st.selectbox("分类", ["工作", "生活", "游戏运营", "学习", "其他"])
                new_priority = st.selectbox("优先级", ["高", "中", "低"])
            
            with col2:
                new_due_date = st.date_input("截止日期", value=None)
                new_description = st.text_area("描述", placeholder="选填")
            
            submitted = st.form_submit_button("添加任务")
            
            if submitted:
                if new_title:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute("""
                        INSERT INTO tasks (title, description, category, priority, due_date)
                        VALUES (?, ?, ?, ?, ?)
                    """, (new_title, new_description, new_category, new_priority, 
                          new_due_date.strftime("%Y-%m-%d") if new_due_date else None))
                    conn.commit()
                    conn.close()
                    st.success("✅ 任务添加成功！")
                    st.rerun()
                else:
                    st.error("❌ 请填写任务标题")
    
    # 筛选器
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_category = st.selectbox("分类筛选", ["全部", "工作", "生活", "游戏运营", "学习", "其他"])
    with col2:
        filter_status = st.selectbox("状态筛选", ["待完成", "已完成", "全部"])
    with col3:
        filter_priority = st.selectbox("优先级筛选", ["全部", "高", "中", "低"])
    
    # 构建查询
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []
    
    if filter_category != "全部":
        query += " AND category=?"
        params.append(filter_category)
    
    if filter_status == "待完成":
        query += " AND completed=0"
    elif filter_status == "已完成":
        query += " AND completed=1"
    
    if filter_priority != "全部":
        query += " AND priority=?"
        params.append(filter_priority)
    
    query += " ORDER BY completed, CASE priority WHEN '高' THEN 1 WHEN '中' THEN 2 WHEN '低' THEN 3 END"
    
    conn = sqlite3.connect(DB_PATH)
    tasks_df = pd.read_sql(query, conn, params=params)
    conn.close()
    
    # 显示任务列表
    if not tasks_df.empty:
        for idx, task in tasks_df.iterrows():
            with st.container():
                col_check, col_info, col_action = st.columns([0.5, 6, 2])
                
                with col_check:
                    completed = st.checkbox("", value=bool(task['completed']), key=f"check_{task['id']}")
                    if completed != bool(task['completed']):
                        conn = sqlite3.connect(DB_PATH)
                        c = conn.cursor()
                        c.execute("""
                            UPDATE tasks 
                            SET completed=?, completed_at=CURRENT_TIMESTAMP 
                            WHERE id=?
                        """, (int(completed), task['id']))
                        conn.commit()
                        conn.close()
                        st.rerun()
                
                with col_info:
                    priority_emoji = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(task['priority'], "⚪")
                    title_class = "completed-task" if task['completed'] else ""
                    due_str = f" | 📅 {task['due_date']}" if task['due_date'] else ""
                    st.markdown(
                        f"<span class='{title_class}'>{priority_emoji} **{task['title']}** | "
                        f"📁 {task['category']}{due_str}</span>",
                        unsafe_allow_html=True
                    )
                    if task['description']:
                        st.caption(task['description'])
                
                with col_action:
                    if st.button("🗑️", key=f"del_{task['id']}", help="删除"):
                        conn = sqlite3.connect(DB_PATH)
                        c = conn.cursor()
                        c.execute("DELETE FROM tasks WHERE id=?", (task['id'],))
                        conn.commit()
                        conn.close()
                        st.rerun()
                
                st.divider()
    else:
        st.info("📭 暂无任务")

# ==================== 日程管理 ====================
elif page == "📅 日程管理":
    st.title("📅 日程管理")
    
    # 添加日程表单
    with st.expander("➕ 添加新日程", expanded=False):
        with st.form("add_event_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                event_title = st.text_input("日程标题 *", placeholder="必填")
                event_date = st.date_input("日期 *", datetime.now())
                event_time = st.time_input("时间", datetime.now())
            
            with col2:
                event_repeat = st.selectbox("重复", ["不重复", "每天", "每周", "每月"])
                event_description = st.text_area("描述", placeholder="选填")
            
            submitted = st.form_submit_button("添加日程")
            
            if submitted:
                if event_title:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute("""
                        INSERT INTO events (title, description, event_date, event_time, repeat)
                        VALUES (?, ?, ?, ?, ?)
                    """, (event_title, event_description, event_date.strftime("%Y-%m-%d"),
                          event_time.strftime("%H:%M"), event_repeat))
                    conn.commit()
                    conn.close()
                    st.success("✅ 日程添加成功！")
                    st.rerun()
                else:
                    st.error("❌ 请填写日程标题")
    
    # 日历视图
    st.subheader("📆 日历视图")
    
    # 日期范围选择
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("开始日期", datetime.now() - timedelta(days=7))
    with col2:
        end_date = st.date_input("结束日期", datetime.now() + timedelta(days=14))
    
    # 查询日程
    conn = sqlite3.connect(DB_PATH)
    events_df = pd.read_sql("""
        SELECT * FROM events 
        WHERE event_date BETWEEN ? AND ?
        ORDER BY event_date, event_time
    """, conn, params=(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
    conn.close()
    
    if not events_df.empty:
        # 按日期分组显示
        for date, group in events_df.groupby('event_date'):
            st.markdown(f"### 📅 {date}")
            
            for _, event in group.iterrows():
                col_info, col_action = st.columns([7, 1])
                
                with col_info:
                    time_str = f"⏰ {event['event_time']} | " if event['event_time'] else ""
                    repeat_str = f"🔄 {event['repeat']} | " if event['repeat'] != "不重复" else ""
                    st.write(f"{time_str}{repeat_str}**{event['title']}**")
                    if event['description']:
                        st.caption(event['description'])
                
                with col_action:
                    if st.button("🗑️", key=f"del_event_{event['id']}", help="删除"):
                        conn = sqlite3.connect(DB_PATH)
                        c = conn.cursor()
                        c.execute("DELETE FROM events WHERE id=?", (event['id'],))
                        conn.commit()
                        conn.close()
                        st.rerun()
                
                st.write("---")
    else:
        st.info("📭 该时间段内暂无日程")

# ==================== 数据统计 ====================
elif page == "📊 数据统计":
    st.title("📊 数据统计")
    
    conn = sqlite3.connect(DB_PATH)
    
    # 任务完成统计
    tasks_df = pd.read_sql("SELECT * FROM tasks", conn)
    events_df = pd.read_sql("SELECT * FROM events", conn)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("✅ 任务完成情况")
        if not tasks_df.empty:
            completed_count = len(tasks_df[tasks_df['completed'] == 1])
            pending_count = len(tasks_df[tasks_df['completed'] == 0])
            
            st.metric("完成率", f"{completed_count / len(tasks_df) * 100:.1f}%")
            
            # 分类统计
            category_stats = tasks_df.groupby('category').size().reset_index(name='count')
            st.bar_chart(category_stats.set_index('category'))
        else:
            st.info("暂无任务数据")
    
    with col2:
        st.subheader("📅 日程分布")
        if not events_df.empty:
            # 按日期统计
            date_stats = events_df.groupby('event_date').size().reset_index(name='count')
            st.line_chart(date_stats.set_index('event_date'))
        else:
            st.info("暂无日程数据")
    
    conn.close()

# ==================== 设置 ====================
elif page == "⚙️ 设置":
    st.title("⚙️ 设置")
    
    st.subheader("💾 数据管理")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 导出数据")
        export_format = st.selectbox("格式", ["JSON", "CSV"])
        
        if st.button("导出"):
            conn = sqlite3.connect(DB_PATH)
            tasks_df = pd.read_sql("SELECT * FROM tasks", conn)
            events_df = pd.read_sql("SELECT * FROM events", conn)
            conn.close()
            
            if export_format == "JSON":
                data = {
                    "tasks": tasks_df.to_dict('records'),
                    "events": events_df.to_dict('records')
                }
                st.download_button(
                    "下载 JSON",
                    json.dumps(data, ensure_ascii=False, indent=2),
                    file_name=f"task_manager_export_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
            else:
                st.download_button(
                    "下载任务 CSV",
                    tasks_df.to_csv(index=False),
                    file_name=f"tasks_export_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
    
    with col2:
        st.markdown("#### 清空数据")
        st.warning("⚠️ 此操作不可恢复！")
        
        if st.button("清空所有任务"):
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("DELETE FROM tasks")
            conn.commit()
            conn.close()
            st.success("✅ 已清空所有任务")
            st.rerun()
        
        if st.button("清空所有日程"):
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("DELETE FROM events")
            conn.commit()
            conn.close()
            st.success("✅ 已清空所有日程")
            st.rerun()
    
    st.divider()
    st.subheader("ℹ️ 关于")
    st.info("""
    **日程任务管理系统 v1.0**
    
    - 📅 日程管理：日历视图、提醒、重复事件
    - ✅ 任务管理：分类、优先级、进度跟踪
    - 📊 数据统计：完成率、时间分布
    - 💾 数据导出：JSON/CSV 格式
    
    数据存储：本地 SQLite 数据库
    """)
