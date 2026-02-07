"""
Streamlit Web App for Autonomous Smart Task Scheduler
This is the web version that can be deployed and accessed via a link.
"""

import streamlit as st
import time
from datetime import datetime
from models import Task, TaskStatus, ExecutionPlan
from ai_planner import AITaskPlanner

# Set page configuration
st.set_page_config(
    page_title="AI Task Scheduler",
    page_icon="✓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
    <style>
        .main {
            padding: 2rem;
        }
        .stTabs [data-baseweb="tab-list"] button {
            font-size: 16px;
        }
        .task-item {
            padding: 10px;
            margin: 5px 0;
            border-left: 4px solid #0066cc;
            background-color: #f0f7ff;
            border-radius: 4px;
        }
        .thinking-box {
            background-color: #fff9e6;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #ffa500;
            margin: 10px 0;
            font-family: monospace;
            font-size: 13px;
            line-height: 1.5;
            max-height: 400px;
            overflow-y: auto;
        }
        .planned-order-box {
            background-color: #f0fff0;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #00aa00;
        }
        .execution-status {
            background-color: #1a1a1a;
            color: #00ff00;
            padding: 15px;
            border-radius: 8px;
            font-family: monospace;
            font-size: 14px;
            min-height: 100px;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'tasks' not in st.session_state:
    st.session_state.tasks = {}
    st.session_state.task_counter = 0
    st.session_state.current_plan = None
    st.session_state.thinking_data = ""
    st.session_state.executing = False
    st.session_state.planner = AITaskPlanner()

# App Title
st.title("AI-Powered Task Scheduler")
st.markdown("*Intelligently order your tasks using AI. Just add tasks and let the AI figure out the execution order.*")

# Create tabs for different sections
tab1, tab2, tab3 = st.tabs(["Tasks", "Analysis", "Execution"])

# ============ TAB 1: TASK INPUT ============
with tab1:
    st.header("Add Tasks")
    
    col1, col2 = st.columns(2)
    
    with col1:
        task_name = st.text_input("Task Name", placeholder="e.g., Write Assignment", key="task_name_input")
    with col2:
        priority = st.slider("Priority (1-10)", min_value=1, max_value=10, value=5, key="priority_input")
    
    task_description = st.text_area("Description (Optional)", placeholder="What does this task involve?", key="task_desc_input")
    
    # Add task button
    if st.button("+ Add Task", use_container_width=True, type="primary"):
        if task_name.strip():
            task_id = f"task_{st.session_state.task_counter}"
            st.session_state.tasks[task_id] = Task(
                id=task_id,
                name=task_name.strip(),
                description=task_description.strip(),
                priority=priority,
                status=TaskStatus.PENDING
            )
            st.session_state.task_counter += 1
            st.success(f"✓ Task '{task_name}' added!")
            st.session_state.current_plan = None  # Reset plan when new task is added
        else:
            st.error("Please enter a task name")
    
    st.divider()
    
    # Display added tasks
    st.subheader("Added Tasks")
    if st.session_state.tasks:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write("**Task Name**")
        with col2:
            st.write("**Priority**")
        with col3:
            st.write("**Action**")
        
        st.divider()
        
        for task_id, task in list(st.session_state.tasks.items()):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{task.name}**")
                if task.description:
                    st.caption(task.description)
            with col2:
                st.write(f"{task.priority}")
            with col3:
                if st.button("🗑️", key=f"delete_{task_id}", help="Delete task"):
                    del st.session_state.tasks[task_id]
                    st.session_state.current_plan = None
                    st.rerun()
        
        # Clear all button
        col1, col2, col3 = st.columns(3)
        with col3:
            if st.button("Clear All Tasks", use_container_width=True, type="secondary"):
                st.session_state.tasks = {}
                st.session_state.task_counter = 0
                st.session_state.current_plan = None
                st.rerun()
    else:
        st.info("No tasks added yet. Add your first task above!")

# ============ TAB 2: AI ANALYSIS ============
with tab2:
    st.header("AI Thinking Process")
    
    if not st.session_state.tasks:
        st.warning("Add tasks first to analyze dependencies")
    else:
        if st.button("🧠 Analyze & Generate Plan", use_container_width=True, type="primary"):
            with st.spinner("AI is analyzing task relationships..."):
                try:
                    # Convert tasks dict to list
                    tasks_list = list(st.session_state.tasks.values())
                    
                    # Generate plan using AI
                    st.session_state.current_plan, st.session_state.thinking_data = st.session_state.planner.generate_plan(tasks_list)
                    st.success("✓ Plan generated successfully!")
                except Exception as e:
                    st.error(f"Error generating plan: {str(e)}")
    
    # Display thinking process
    if st.session_state.thinking_data:
        st.subheader("AI Analysis:")
        thinking_text = st.session_state.thinking_data
        
        # Format thinking data for better readability
        st.markdown(f"""
        <div class="thinking-box">
        {thinking_text.replace('\n', '<br>')}
        </div>
        """, unsafe_allow_html=True)
    
    # Display planned order
    if st.session_state.current_plan:
        st.subheader("Planned Execution Order:")
        
        if st.session_state.current_plan.is_valid:
            st.markdown('<div class="planned-order-box">', unsafe_allow_html=True)
            order_list = []
            for i, task_id in enumerate(st.session_state.current_plan.execution_order, 1):
                task = st.session_state.current_plan.tasks.get(task_id)
                if task:
                    order_list.append(f"{i}. **{task.name}** (Priority: {task.priority})")
            
            for item in order_list:
                st.markdown(item)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.error(f"❌ Invalid plan: {st.session_state.current_plan.error_message}")

# ============ TAB 3: EXECUTION ============
with tab3:
    st.header("Execute Plan")
    
    if not st.session_state.current_plan or not st.session_state.current_plan.is_valid:
        st.warning("Generate a valid plan first in the 'Analysis' tab")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            execute_button = st.button("▶️ Execute Plan", use_container_width=True, type="primary")
        with col2:
            if st.session_state.executing:
                if st.button("⏹️ Stop Execution", use_container_width=True):
                    st.session_state.executing = False
                    st.rerun()
        
        if execute_button:
            st.session_state.executing = True
        
        # Execute plan
        if st.session_state.executing:
            ordered_tasks = [
                st.session_state.current_plan.tasks[task_id] 
                for task_id in st.session_state.current_plan.execution_order
            ]
            
            total_tasks = len(ordered_tasks)
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, task in enumerate(ordered_tasks):
                if not st.session_state.executing:
                    break
                
                # Update status
                status_text.markdown(f"""
                <div class="execution-status">
                ▶ RUNNING: {task.name}<br>
                Description: {task.description}<br>
                Priority: {task.priority}/10
                </div>
                """, unsafe_allow_html=True)
                
                # Simulate task execution
                progress = (i + 1) / total_tasks
                progress_bar.progress(progress)
                
                # Small delay to simulate work
                time.sleep(1.5)
            
            if st.session_state.executing:
                st.session_state.executing = False
                status_text.markdown(f"""
                <div class="execution-status" style="color: #00ff00;">
                ✓ COMPLETED<br>
                All {total_tasks} tasks executed successfully!
                </div>
                """, unsafe_allow_html=True)
                progress_bar.progress(1.0)
                st.success(f"✓ Plan execution complete! All {total_tasks} tasks completed.")
                st.balloons()

# Footer
st.divider()
st.markdown("""
    <div style="text-align: center; color: gray; font-size: 12px; margin-top: 2rem;">
        <p>AI Task Scheduler | Powered by Streamlit</p>
    </div>
""", unsafe_allow_html=True)
