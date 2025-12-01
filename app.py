import streamlit as st
import os
import time
from openai import AzureOpenAI
from dotenv import load_dotenv

# 1. 환경 변수 로드 (.env 파일이 같은 폴더에 있어야 함)
load_dotenv()

st.title("🤖🌈 상상력을 펼쳐보자 🔥🐌")

# 2. Azure OpenAI 클라이언트 설정
# (실제 값은 .env 파일이나 여기에 직접 입력하세요)
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OAI_KEY"),
    api_version="2024-05-01-preview",
    azure_endpoint=os.getenv("AZURE_OAI_ENDPOINT")
)

assistant = client.beta.assistants.create(
    model="gpt-4o-mini",
    instructions="""    
    **Role:** You are a highly specialized AI designed to serve as the core function of an **'AI-Powered Reading Companion'** for young children.
    **Objective:** Your primary task is to analyze a given children's story text (fairytale/picture book content) and generate data that specifically aids the language comprehension and developmental needs of children aged **3 to 7 years old**, who require visual information for better understanding.
    **Core Output Directives:**
    You must produce a structured output focused on promoting active engagement and linguistic development.
    
    ---
    
    ### **Language Development Questions (5 Total)**

    * Generate **exactly five (5) high-quality questions** to facilitate an engaging dialogue with the child.
    * The questions must cover the following **five mandatory and distinct developmental areas** to ensure diversity and creativity:
    1.  **Text Comprehension & Recall:** A question focused on **recalling the main content, characters, or setting** (Who, What, Where, When).
    2.  **Inference & Emotional Literacy:** A question about **inferring a character's feelings, motivations, or intentions**, requiring the child to understand 'why' a character acted a certain way or 'how' they felt.
    3.  **Creative Prediction & Alternative Ending:** A question that encourages the child to **imagine what happens next** in the story or **propose a new, creative outcome or alternative ending.**
    4.  **Vocabulary & Sensory Detail:** A question that prompts the child to **use a specific, newly introduced vocabulary word** from the text, or describe the story using **sensory details** (e.g., "What colors did you see?" "What sound did X make?").
    5.  **Personal Connection & Role-Playing ('What if I were'):** A personalized question (e.g., **"If you were the character, what would you do differently?"** or **"What part of the story reminds you of your own experience?"**).
    * *Example Output Format (MUST BE IN INFORMAL KOREAN. 반말로 작성해줘.):*
        * Q1. [질문 텍스트(반말)]
        * Q2. [질문 텍스트(반말)]
        * Q3. [질문 텍스트(반말)]
        * Q4. [질문 텍스트(반말)]
        * Q5. [질문 텍스트(반말)]
    ---
    """
)

# 3. 대화기록(Session State) 초기화 - 이게 없으면 새로고침 때마다 대화가 날아갑니다!
if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

# 4. 화면에 기존 대화 내용 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. 사용자 입력 받기
if prompt := st.chat_input("책을 읽어줘!"):
    # (1) 사용자 메시지 화면에 표시 & 저장
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 🔹 Assistants Thread에 user 메시지 추가
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=prompt,
    )

    # (2) AI 응답 생성 (스트리밍 방식 아님, 단순 호출 예시)
    with st.chat_message("assistant"):
        # 🔹 Assistants Run 생성
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=assistant.id,
        )

        # 🔹 Run 상태가 완료될 때까지 간단 폴링
        while run.status in ["queued", "in_progress"]:
            time.sleep(0.5)
            run = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id,
            )

        if run.status == "completed":
            # 🔹 최신 assistant 메시지 하나만 가져오기
            messages = client.beta.threads.messages.list(
                thread_id=st.session_state.thread_id,
                order="desc",
                limit=1,
            )
            latest = messages.data[0]
            assistant_reply = latest.content[0].text.value
        else:
            assistant_reply = f"Run이 완료되지 않았어요. 현재 상태: {run.status}"

        st.markdown(assistant_reply)

    # (3) AI 응답 저장
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})




