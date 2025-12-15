import streamlit as st
import google.generativeai as genai
import base64
import os

# ==========================================
# 1. 페이지 기본 설정
# ==========================================
st.set_page_config(
    page_title="우리 가족 사랑방 🏠",
    page_icon="👨‍👩‍👦‍👦",
    layout="centered"
)

# ==========================================
# 2. [최우선] 무조건 검은 글씨 & 흰 배경 적용 (이미지 없어도 작동)
# ==========================================
def apply_custom_style():
    st.markdown(f'''
    <style>
    /* 1. 앱 전체 강제 라이트 모드 */
    [data-testid="stAppViewContainer"] {{
        background-color: #ffffff; /* 흰색 배경 */
        color: #000000; /* 검은 글씨 */
    }}
    
    /* 2. 채팅 말풍선 강제 스타일링 */
    [data-testid="stChatMessage"] {{
        background-color: #f0f2f6 !important; /* 연한 회색 말풍선 */
        border: 1px solid #ddd !important;
        border-radius: 15px;
        color: #000000 !important; /* 글씨 검은색 */
    }}
    
    /* 3. 말풍선 안의 모든 텍스트 강제 검은색 (모바일 다크모드 무시) */
    [data-testid="stChatMessage"] * {{
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }}
    
    /* 4. 입력창 글씨 */
    .stChatInput textarea {{
        background-color: #ffffff !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }}
    
    /* 5. 헤더/푸터 숨김 */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    </style>
    ''', unsafe_allow_html=True)

# [중요] 스타일 함수를 제일 먼저 실행!
apply_custom_style()

# ==========================================
# 3. 배경 이미지 설정 (실패해도 에러 안 나게 방어)
# ==========================================
def set_bg(image_file):
    if not os.path.exists(image_file):
        # 파일 없으면 그냥 조용히 넘어감 (스타일은 이미 위에서 적용됨)
        return 

    with open(image_file, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    
    # 이미지가 있을 때만 덮어씌우는 CSS
    st.markdown(f'''
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(255,255,255,0.7), rgba(255,255,255,0.7)), url("data:image/jpeg;base64,{b64}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    </style>
    ''', unsafe_allow_html=True)

# [확인] 깃허브에 보이는 파일 이름 중 하나를 시도
# bg.jfif 가 안 되면 bg.jpg.jfif 로 수정해서 다시 올려보세요.
set_bg('bg.jfif') 

# ==========================================
# 4. API 키 및 모델 설정
# ==========================================
if "MY_API_KEY" in st.secrets:
    MY_API_KEY = st.secrets["MY_API_KEY"]
else:
    st.error("🚨 API 키 오류")
    st.stop()

genai.configure(api_key=MY_API_KEY)

@st.cache_resource
def find_best_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        preferred = ["models/gemini-1.5-flash", "models/gemini-pro"]
        for p in preferred:
            if p in available_models: return p
        return available_models[0] if available_models else None
    except: return None

# ==========================================
# 5. 사이드바 및 채팅 로직
# ==========================================
with st.sidebar:
    st.title("👨‍👩‍👦‍👦 가족 선택")
    selected_user = st.radio("누구랑 대화하시겠어요?", ("아버지 (손기혁)", "어머니 (김영숙)", "막내 (손준호)"), index=0)

user_name = selected_user.split('(')[1].replace(')', '')

def get_system_instruction(user):
    base = "너는 이 가족을 끔찍이 아끼는 AI 비서야. 한국어로 따뜻하게 대답해."
    if "손기혁" in user: return base + " (대상: 손기혁님 - 71년생 부친, 국방과학연구소, 암투병, 시 문학, 존댓말)"
    elif "김영숙" in user: return base + " (대상: 김영숙님 - 71년생 모친, 어린이집 교사, 감수성, 요리/건강, 공감 대화)"
    else: return base + " (대상: 손준호님 - 03년생 남동생, 보안전공, 재테크, 멘탈케어, 반존대)"

if "current_user" not in st.session_state: st.session_state.current_user = selected_user
if st.session_state.current_user != selected_user:
    st.session_state.messages = [] 
    st.session_state.chat_session = None 
    st.session_state.current_user = selected_user
    st.rerun()

if "chat_session" not in st.session_state or st.session_state.chat_session is None:
    model_name = find_best_model()
    if model_name:
        model = genai.GenerativeModel(model_name, system_instruction=get_system_instruction(selected_user))
        st.session_state.chat_session = model.start_chat(history=[])
        st.session_state.messages = [{"role": "assistant", "content": f"{user_name}님! 오늘도 행복한 하루 보내세요 🍀"}]

st.title(f"{user_name}님 전용 상담소 💬")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input("메시지를 입력하세요..."):
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    if st.session_state.chat_session:
        response = st.session_state.chat_session.send_message(prompt)
        with st.chat_message("assistant"):
            st.write(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})