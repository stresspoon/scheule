import streamlit as st
from openai import OpenAI

def main():
    st.set_page_config(page_title="오늘 하루 일정 정리", page_icon="📅", layout="wide")
    st.markdown("""
    <style>
    .stApp {
        background-color: #131313;
        color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)
    st.title("오늘 하루 일정 정리")

    if 'api_key' not in st.session_state:
        st.session_state.api_key = ''
    if 'page' not in st.session_state:
        st.session_state.page = 'api_key'
    if 'sorted_tasks' not in st.session_state:
        st.session_state.sorted_tasks = None
    if 'tasks' not in st.session_state:
        st.session_state.tasks = []
    if 'explanation' not in st.session_state:
        st.session_state.explanation = ''
    if 'task_count' not in st.session_state:
        st.session_state.task_count = 1
    if 'goals' not in st.session_state:
        st.session_state.goals = []

    if st.session_state.page == 'api_key':
        api_key_page()
    elif st.session_state.page == 'goal_input':
        goal_input_page()
    elif st.session_state.page == 'task_input':
        task_input_page()

def api_key_page():
    st.header("API 키 입력")
    api_key = st.text_input("OpenAI API 키를 입력하세요:", type="password")
    if st.button("입력 완료"):
        if api_key:
            st.session_state.api_key = api_key
            st.session_state.page = 'goal_input'
            st.experimental_rerun()
        else:
            st.error("API 키를 입력해주세요.")

def goal_input_page():
    st.header("목표 및 중요도 설정")
    
    # 이전에 입력한 목표 선택 옵션
    if st.session_state.goals:
        selected_goal = st.selectbox("이전에 입력한 목표 선택:", ["새로운 목표 입력"] + st.session_state.goals)
        if selected_goal != "새로운 목표 입력":
            st.session_state.goal = selected_goal
        else:
            st.session_state.goal = st.text_input("새로운 목표를 입력하세요:")
    else:
        st.session_state.goal = st.text_input("본인이 이루고자하는 최종 목표에 대해서 구체적으로 작성해주세요:")
    
    st.session_state.importance = st.slider("목표의 중요도를 선택하세요", 1, 10, 5)
    
    if st.button("다음"):
        if st.session_state.goal:
            if st.session_state.goal not in st.session_state.goals:
                st.session_state.goals.append(st.session_state.goal)
            st.session_state.page = 'task_input'
            st.experimental_rerun()
        else:
            st.error("목표를 입력하거나 선택해주세요.")

def task_input_page():
    col1, col2 = st.columns(2)

    with col1:
        st.header("해야 할 일에 대한 내용을 최대한 구체적으로 입력해주세요")
        st.markdown(
            "<p style='font-size: 16px; color: yellow;'>예) <br> ❌: 블로그 쓰기 <br> ✅: [AI 활용 방법] 무료 특강 모집 블로그 쓰기</p>",
            unsafe_allow_html=True
        )
        
        # 기존 일정 표시 및 수정
        for i in range(len(st.session_state.tasks)):
            st.session_state.tasks[i] = st.text_input(f"해야할 일 {i+1}", value=st.session_state.tasks[i], key=f"existing_task_{i}")
        
        # 새로운 일정 입력 필드 추가
        for i in range(len(st.session_state.tasks), st.session_state.task_count):
            new_task = st.text_input(f"해야할 일 {i+1}", key=f"new_task_{i}")
            if new_task:
                st.session_state.tasks.append(new_task)
        
        if st.button("해야할 일 추가"):
            st.session_state.task_count += 1
            st.experimental_rerun()

        if st.button("입력 완료"):
            if st.session_state.tasks:
                with col2:
                    with st.spinner('해야할 일을 정리하는 중...'):
                        sorted_tasks, explanation = sort_tasks(st.session_state.tasks)
                        st.session_state.sorted_tasks = sorted_tasks
                        st.session_state.explanation = explanation
                st.experimental_rerun()
            else:
                st.warning("최소한 하나의 해야할 일을 입력해주세요.")

    with col2:
        st.header("정리된 일정")
        if st.session_state.sorted_tasks:
            for i, task in enumerate(st.session_state.sorted_tasks, 1):
                st.write(f"{i}. {task}")
            
            st.subheader("일정 정리 이유")
            st.write(st.session_state.explanation)
        else:
            st.info("일정을 입력하고 '입력 완료' 버튼을 누르면 이 곳에 정리된 일정이 표시됩니다.")

def sort_tasks(tasks):
    client = OpenAI(api_key=st.session_state.api_key)
    task_list = "\n".join(tasks)
    prompt = (
        f"목표: {st.session_state.goal}\n"
        f"중요도: {st.session_state.importance}\n\n"
        "다음 일정들의 우선순위를 파악해서 리스트화해주세요:\n"
        f"{task_list}\n\n"
        "위 정보를 바탕으로, 목표와 중요도를 고려하여 우선순위가 높은 순서대로 정렬된 일정을 번호를 매기지 않고 리스트로 출력해주세요. "
        "그 다음, 왜 이런 순서로 일정을 정리했는지 그 이유를 각 일정마다 설명하는게 아니라 전체적으로 적용한 이유를 줄글로 설명해주세요."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 일정을 효율적으로 정리하고 우선순위를 파악하는 전문가입니다."},
                {"role": "user", "content": prompt}
            ]
        )
        content = response.choices[0].message.content.strip()
        tasks_and_explanation = content.split("\n\n", 1)
        sorted_tasks = tasks_and_explanation[0].split("\n")
        explanation = tasks_and_explanation[1] if len(tasks_and_explanation) > 1 else "설명이 제공되지 않았습니다."
        return [task.strip('- ') for task in sorted_tasks], explanation
    except Exception as e:
        st.error(f"일정 정리 중 오류가 발생했습니다: {str(e)}")
        return [], "오류로 인해 설명을 생성할 수 없습니다."

if __name__ == "__main__":
    main()
