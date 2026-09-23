import streamlit as st
import time
from st_copy_to_clipboard import st_copy_to_clipboard
from google import genai
from google.genai import types

# 페이지 기본 설정
st.set_page_config(
    page_title="이모지가 가득해", page_icon="🎨", layout="centered"
)

st.markdown(
    """
    <style>
    /* 상단 메뉴바 숨기기 (모바일에서 화면을 덜 가리게 함) */
    header {visibility: hidden;}
    /* 하단 Streamlit 워터마크 숨기기 */
    footer {visibility: hidden;}
    /* 앱 전체 위아래 여백을 극한으로 줄임 */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 0rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# API 클라이언트 초기화
if "GEMINI_API_KEY" in st.secrets:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ API 키를 찾을 수 없습니다. .streamlit/secrets.toml 파일을 확인해주세요.")


# 1. 문장 전체를 한 번에 Gemini에게 맡기는 함수
def process_full_sentence(sentence: str) -> str:
    system_instruction = """
You are a strict word-by-word emoji appending tool.

[Rules]
1. EVERY BOUNDARY: Append an emoji immediately after EACH word. If the input lacks spaces, automatically detect morpheme/semantic boundaries and generously insert emojis between them.
2. KEEP ORIGINAL: NEVER translate, delete, or alter the original text. 
3. EMOTION: Prioritize facial emojis (😀, 😭, 😡) for emotional words.
4. FORMAT: Output ONLY the final text. No greetings, no explanations.

[Examples]
Input: 오늘 진짜 너무 짜증나는 일이 있었어
Output: 오늘📅 진짜⁉️ 너무😤 짜증나는🤬 일이📄 있었어😔

Input: 띄어쓰기없이그냥다붙여서써도알아서이모지넣어줘
Output: 띄어쓰기없이🙅‍♂️그냥🤷다💯붙여서🔗써도✍️알아서🧠이모지🥰넣어줘🙏
"""
    try:
        # 💡 경고 해결: generate_content 대신 권장되는 chats 세션 방식으로 변경
        chat = client.chats.create(
            model='gemini-3.5-flash-lite', # 혹은 사용중인 1.5-flash-8b 등
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3,
            )
        )
        response = chat.send_message(f"다음 문장을 화려하게 변환해줘: {sentence}")
        return response.text.strip()
    except Exception as e:
        error_msg = str(e)
        if "503" in error_msg or "UNAVAILABLE" in error_msg:
            return "🚨 지금 구글 AI 서버에 사람이 너무 많아요! 10초 뒤에 다시 버튼을 눌러주세요 😭"
        else:
            return f"🚨 에러 발생!!!! 잠시 후 다시 시도해주세요 😭"

# --- 스크롤 방지 콤팩트 UI ---
st.markdown(
    "<p style='font-size: 1.6rem; font-weight: bold; margin-bottom: 0px;'>✨ 주접 & 밈 이모티콘 변환기</p>", 
    unsafe_allow_html=True
)
st.caption("평범한 문장을 화려한✨이모지로📝채워드립니다!🔍")

# 💡 1. 텍스트 지우기를 위해 'input_text' 세션 상태 추가
if "input_text" not in st.session_state:
    st.session_state.input_text = ""
if "last_submit_time" not in st.session_state:
    st.session_state.last_submit_time = 0
if "result_text" not in st.session_state:
    st.session_state.result_text = ""

# 넉넉한 글자 제한으로 복사/붙여넣기 튕김 방지
user_input = st.text_area(
    "입력창",
    label_visibility="collapsed",
    placeholder="변환할 문장을 입력하세요 (최대 300자까지만 변환됩니다 / 긴 글 복붙 환영!)",
    height=120, 
    max_chars=1000,
    key="input_text",  # 💡 2. 입력창을 위 세션 상태와 연결
)

# --- 3. 버튼 동작 및 안전장치 로직 ---

# 💡 3. 초기화(지우기) 버튼을 눌렀을 때 실행될 함수
def clear_text():
    st.session_state.input_text = ""
    st.session_state.result_text = ""

# 버튼 영역을 4:1 비율로 나란히 배치
btn_col1, btn_col2 = st.columns([4, 1])

with btn_col1:
    submit_btn = st.button("🚀 이모티콘 듬뿍 넣기", use_container_width=True)
with btn_col2:
    st.button("🔄 지우기", on_click=clear_text, use_container_width=True)

# 기존 st.button 부분 대신 submit_btn을 확인
if submit_btn:
    safe_box = st.container(height=120, border=False)
    
    current_time = time.time()
    time_passed = current_time - st.session_state.last_submit_time
    cooldown_seconds = 5

    clean_input = user_input.strip()

    if time_passed < cooldown_seconds:
        remaining_time = int(cooldown_seconds - time_passed)
        alert_msg = safe_box.error(f"🚨 앗! 변환 후 {cooldown_seconds}초가 지나야 합니다. ({remaining_time}초 남음)")
        time.sleep(2)
        alert_msg.empty()
        
    elif not clean_input:
        warning_msg = safe_box.warning("문장을 입력해주세요!")
        time.sleep(2)
        warning_msg.empty()
        
    else:
        if len(clean_input) > 300:
            len_warning = safe_box.warning("🚨 300자가 넘는 텍스트는 앞부분만 잘라서 변환합니다!")
            clean_input = clean_input[:300]
            time.sleep(2)
            len_warning.empty()
            
        with safe_box:
            with st.spinner("✨ 찰떡같은 이모지를 고르는 중..."):
                new_result = process_full_sentence(clean_input)
                st.session_state["result_area"] = new_result
                st.session_state.result_text = new_result
                
        st.session_state.last_submit_time = time.time()