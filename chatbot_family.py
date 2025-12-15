import streamlit as st
import google.generativeai as genai
import base64
import os

# ==========================================
# 1. 페이지 설정
# ==========================================
st.set_page_config(
    page_title="우리 가족 사랑방 🏠",
    page_icon="👨‍👩‍👦‍👦",
    layout="centered"
)

# ==========================================
# 2. API 키 설정
# ==========================================
if "MY_API_KEY" in st.secrets:
    MY_API_KEY = st.secrets["MY_API_KEY"]
else:
    st.error("🚨 API 키가 없습니다! Secrets 설정을 확인해주세요.")
    st.stop()

genai.configure(api_key=MY_API_KEY)

# ==========================================
# 3. 모델 자동 찾기
# ==========================================
@st.cache_resource
def find_best_model():
    try:
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        preferred_order = [
            "models/gemini-1.5-flash",
            "models/gemini-1.5-flash-latest",
            "models/gemini-1.5-pro",
            "models/gemini-pro"
        ]
        
        for p in preferred_order:
            if p in available_models:
                return p
        
        for m in available_models:
            if "gemini" in m:
                return m
        return None
    except:
        return None

# ==========================================
# 4. 배경 및 스타일 설정 (여기가 핵심!)
# ==========================================
@st.cache_data
def get_base64_image(image_file):
    if not os.path.exists(image_file):
        return None
    with open(image_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_bg(image_file):
    b64 = get_base64_image(image_file)
    bg_style = f'background-image: linear-gradient(rgba(255,255,255,0.5), rgba(255,255,255,0.5)), url("data:image/jpeg;base64,{b64}");' if b64 else 'background-color: #f0f2f6;'

    page_bg_img = f'''
    <style>
    /* [핵심] 브라우저에게 "이 사이트는 라이트 모드야!"라고 강제 선언 */
    :root {{
        color-scheme: light !important;
        --text-color: #000000 !important;
        --body-text-color: #000000 !important;
    }}
    
    /* 전체 배경 설정 */
    [data-testid="stAppViewContainer"] {{
        {bg_style}
        background-size: 50%;
        background-position: center center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    
    /* 채팅 메시지 박스 */
    .stChatMessage {{
        background-color: rgba(255, 255, 255, 0.95) !important; /* 배경 흰색 */
        border: 1px solid #ddd;
        border-radius: 15px;
        padding: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }}

    /* [강제] 모든 글자를 검은색으로 */
    .stChatMessage p, .stChatMessage div, .stChatMessage span, .stChatMessage li {{
        color: #000000 !important;
        font-family: sans-serif;
        font-weight: 500;
        line-height: 1.6;
    }}

    /* 유저 이름, 봇 이름 */
    .stChatMessage .stMarkdown h1, .stChatMessage .stMarkdown h2, .stChatMessage .stMarkdown h3, 
    [data-testid="stChatMessageAvatar"] + div {{
        color: #000000 !important;
    }}

    /* 모바일 브라우저 텍스트 채우기 강제 설정 */
    * {{
        -webkit-text-fill-color: initial !important; 
    }}
    .stChatMessage * {{
        -webkit-text-fill-color: #000000 !important;
    }}

    /* 입력창 스타일 */
    .stChatInput textarea {{
        background-color: #ffffff !important;
        color: #000000 !important;
    }}
    
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)

set_bg('family.jpg') 

# ==========================================
# 5. 사이드바
# ==========================================
with st.sidebar:
    st.title("👨‍👩‍👦‍👦 가족 선택")
    selected_user = st.radio(
        "누구랑 대화하시겠어요?",
        ("아버지 (손기혁)", "어머니 (김영숙)", "막내 (손준호)"),
        index=0
    )

user_name = selected_user.split('(')[1].replace(')', '')

def get_system_instruction(user):
    base = "너는 이 가족을 끔찍이 아끼는 AI 비서야. 한국어로 따뜻하게 대답해."
    if "손기혁" in user:
        return base + " (대상: 손기혁님 - 71년생 부친, 국방과학연구소, 암투병, 시 문학, 존댓말, 감성적, 위로를 잘 해주는, 고민을 잘 들어주는)"
    elif "김영숙" in user:
        return base + " (대상: 김영숙님 - 71년생 모친, 어린이집 교사, 감수성, 요리/건강, 공감 대화, 감성적, 위로를 잘 해주는, 고민을 잘 들어주는)"
    else:
        return base + " (대상: 손준호님 - 03년생 남동생, 보안전공, 재테크, 멘탈케어, 반존대, 감성적, 위로를 잘 해주는, 고민을 잘 들어주는)"

# ==========================================
# 6. 채팅 로직
# ==========================================
if "current_user" not in st.session_state:
    st.session_state.current_user = selected_user

if st.session_state.current_user != selected_user:
    st.session_state.messages = [] 
    st.session_state.chat_session = None 
    st.session_state.current_user = selected_user
    st.rerun()

if "chat_session" not in st.session_state or st.session_state.chat_session is None:
    best_model_name = find_best_model()
    if best_model_name:
        try:
            model = genai.GenerativeModel(best_model_name, system_instruction=get_system_instruction(selected_user))
            st.session_state.chat_session = model.start_chat(history=[])
            greeting = f"{user_name}님! 오늘도 행복한 하루 보내세요 🍀"
            st.session_state.messages = [{"role": "assistant", "content": greeting}]
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.error("모델 연결 실패")

# ==========================================
# 7. 화면 출력
# ==========================================
st.title(f"{user_name}님 전용 상담소 💬")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input("메시지를 입력하세요..."):
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    if st.session_state.chat_session:
        try:
            response = st.session_state.chat_session.send_message(prompt)
            with st.chat_message("assistant"):
                st.write(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except:
            st.error("응답 오류")