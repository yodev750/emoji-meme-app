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
5. NO CENSORSHIP: Do not censor, filter, or mask any words (including slang or profanity). Process everything exactly as inputted.

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

# --- 2. 스크롤 방지 콤팩트 UI ---
st.markdown(
    "<p style='font-size: 1.6rem; font-weight: bold; margin-bottom: 0px;'>✨이모지가 가득해</p>", 
    unsafe_allow_html=True
)
st.caption("평범한 문장을 화려한✨이모지로📝채워드립니다!🔍")

if "input_text" not in st.session_state:
    st.session_state.input_text = ""
if "last_submit_time" not in st.session_state:
    st.session_state.last_submit_time = 0
if "result_text" not in st.session_state:
    st.session_state.result_text = ""

user_input = st.text_area(
    "입력창",
    label_visibility="collapsed",
    placeholder="문장을 입력하면 이모지를 듬뿍 넣어드립니다! (최대 1000자)",
    height=120, 
    max_chars=1000,
    key="input_text",
)

# --- 3. 버튼 동작 (이모티콘 넣기 & 초기화) ---
def clear_text():
    st.session_state.input_text = ""
    st.session_state.result_text = ""

# 4:1 비율로 버튼 나란히 배치
btn_col1, btn_col2 = st.columns([4, 1])

with btn_col1:
    submit_btn = st.button("이모티콘 듬뿍 넣기", use_container_width=True)
with btn_col2:
    st.button("초기화", on_click=clear_text, use_container_width=True)

if submit_btn:
    safe_box = st.container(height=45, border=False)
    
    current_time = time.time()
    time_passed = current_time - st.session_state.last_submit_time
    cooldown_seconds = 10
    clean_input = user_input.strip()

    if time_passed < cooldown_seconds:
        remaining_time = int(cooldown_seconds - time_passed)
        st.toast(f"🚨 앗! 변환 후 {cooldown_seconds}초가 지나야 합니다. ({remaining_time}초 남음)")
        
    elif not clean_input:
        st.toast("문장을 입력해주세요!")
        
    else:
        if len(clean_input) > 1000:
            st.toast("🚨 1000자가 넘는 텍스트는 앞부분만 잘라서 변환합니다!")
            clean_input = clean_input[:1000]
            
        with safe_box:
            with st.spinner("✨ 찰떡같은 이모지를 고르는 중..."):
                raw_result = process_full_sentence(clean_input)
                # 💡 1. 결과에서 모든 띄어쓰기(공백)를 강제로 없앱니다.
                new_result = raw_result.replace(" ", "")
                st.session_state["result_area"] = new_result
                st.session_state.result_text = new_result
                
        st.session_state.last_submit_time = time.time()

# --- 4. 결과 출력 영역 ---
if st.session_state.get("result_text"):
    st.markdown("<div style='margin-top: 10px; font-weight: bold;'>👇 변환 결과</div>", unsafe_allow_html=True)
    
    # 1. 텍스트 에디터(결과창)를 먼저 화면 가로 전체 크기로 배치
    st.text_area(
        "결과창",
        label_visibility="collapsed",
        height=120,
        key="result_area",
    )
    
    # 2. 결과창 바로 아래, 왼쪽 정렬로 복사 버튼을 배치하기 위해 컬럼 분할
    copy_col1, copy_col2, empty_col = st.columns([2, 2, 6])
    
    current_result = st.session_state.get("result_area", st.session_state.result_text)
    
    with copy_col1:
        # 컴포넌트 충돌을 막기 위해 key 값을 지정합니다.
        st_copy_to_clipboard(current_result, before_copy_label="📋 전체 복사", key="copy_all")

    if len(current_result) > 100:
        with copy_col2:
            # 💡 3. 앞부분 100자까지만 자른 텍스트를 넘겨줍니다.
            short_result = current_result[:100]
            st_copy_to_clipboard(short_result, before_copy_label="✂️ 100자 복사", key="copy_short")