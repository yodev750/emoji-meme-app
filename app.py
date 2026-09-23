import streamlit as st
from st_copy_to_clipboard import st_copy_to_clipboard
from google import genai
from google.genai import types

# 페이지 기본 설정
st.set_page_config(
    page_title="이모지가 가득해", page_icon="🎨", layout="centered"
)

# API 클라이언트 초기화
if "GEMINI_API_KEY" in st.secrets:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ API 키를 찾을 수 없습니다. .streamlit/secrets.toml 파일을 확인해주세요.")


# 1. 문장 전체를 한 번에 Gemini에게 맡기는 함수
def process_full_sentence(sentence: str) -> str:
    system_instruction = """
You are a strict word-by-word emoji appending tool. Your sole purpose is to receive a sentence and append exactly one highly relevant emoji immediately after EVERY word (separated by spaces).

[Rules]
1. EVERY WORD: You MUST append an emoji right after each word in the input sentence. Do not wait until the end of the sentence.
2. ZERO TRANSLATION: Do not translate the input into English or any other language. The original text must remain 100% intact.
3. ZERO MODIFICATION: Do not alter, delete, or reformat the original spelling or spacing. 
4. EMOTION RULE: For words that express emotions, feelings, or moods, prioritize facial expression emojis (e.g., 😀, 😭, 😡, 🥰, 😵).
5. OUTPUT FORMAT: Output ONLY the final original text with the emojis appended to each word. Absolutely no greetings, explanations, translations, or additional formatting.

[Examples]
Input: 오늘 진짜 너무 짜증나는 일이 있었어
Output: 오늘📅 진짜⁉️ 너무😤 짜증나는🤬 일이📄 있었어😔

Input: 점심에 마라탕 먹고 싶다
Output: 점심에🕛 마라탕🥘 먹고🤤 싶다🙏

Input: 피곤해서 일찍 잤어
Output: 피곤해서😵 일찍🏃‍♂️잤어💤
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
st.markdown("### ✨ 이모지가 가득해")
st.caption("평범한 문장을 화려한✨이모지로📝채워드립니다!🔍")

user_input = st.text_area(
    "입력창",
    label_visibility="collapsed",
    placeholder="변환할 문장을 입력하세요 (예: 오늘 너무 피곤해서 치킨 먹어야겠어)",
    height=68, 
    max_chars=200
)

if "result_text" not in st.session_state:
    st.session_state.result_text = ""

if st.button("🚀 이모티콘 듬뿍 넣기", use_container_width=True):
    # 세이프 박스 120px 유지
    safe_box = st.container(height=40, border=False)
    
    if user_input.strip():
        with safe_box:
            with st.spinner("✨ 찰떡같은 이모지를 고르는 중..."):
                new_result = process_full_sentence(user_input)
                st.session_state["result_area"] = new_result
                st.session_state.result_text = new_result
    else:
        safe_box.warning("문장을 입력해주세요!")

if st.session_state.get("result_text"):
    st.markdown("**👇 변환 결과**")
    
    col1, col2 = st.columns([5, 1])
    with col1:
        edited_text = st.text_area(
            "결과창",
            label_visibility="collapsed",
            height=100,
            key="result_area",
        )
    with col2:
        st_copy_to_clipboard(edited_text, before_copy_label="📋 복사")