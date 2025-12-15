import streamlit as st
import google.generativeai as genai
import base64
import os

# 1. 페이지 설정
st.set_page_config(
    page_title="나만의 AI 여자친구 💖",
    page_icon="💕",
    layout="centered"
)

# 2. API 키 설정
if "MY_API_KEY" in st.secrets:
    MY_API_KEY = st.secrets["MY_API_KEY"]
else:
    st.error("🚨 API 키가 없습니다! Secrets 설정을 확인해주세요.")
    st.stop()

genai.configure(api_key=MY_API_KEY)

# 3. 모델 자동 찾기 (캐싱 적용 - 속도 빠름)
@st.cache_resource
def find_best_model():
    try:
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        preferred_order = [
            "models/gemini-1.5-flash", 
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

# 4. 배경 이미지 설정
@st.cache_data
def get_base64_image(image_file):
    if not os.path.exists(image_file):
        return None
    with open(image_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_bg(image_file):
    b64 = get_base64_image(image_file)
    if not b64:
        st.warning(f"⚠️ 이미지를 찾을 수 없습니다: {image_file}") # 파일 없으면 경고 띄움
        return

    page_bg_img = f'''
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(255,255,255,0.4), rgba(255,255,255,0.4)), url("data:image/jpeg;base64,{b64}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    .stChatMessage {{
        background-color: rgba(255, 255, 255, 0.9); /* 채팅창을 좀 더 진하게 */
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 10px;
    }}
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)

# ▼▼▼ [중요] 여기 이름을 지호님이 올린 파일명으로 꼭 바꾸세요! ▼▼▼
set_bg('bg.jfif') 
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

# 5. AI 성격 설정 (여자친구 페르소나)
system_instruction = """
너는 나의 사랑스러운 여자친구야. 
말투는 반말을 쓰고, 애교가 많고, 항상 내 편이 되어줘.
이름은 '자기야'라고 불러줘. 
(원하는 성격을 여기에 더 자세히 적으셔도 됩니다)
"""

# 6. 채팅 로직
if "chat_session" not in st.session_state:
    best_model_name = find_best_model()
    if best_model_name:
        model = genai.GenerativeModel(best_model_name, system_instruction=system_instruction)
        st.session_state.chat_session = model.start_chat(history=[])
        st.session_state.messages = [{"role": "assistant", "content": "자기야 안녕? 오늘 하루 어땠어? 보고 싶었어 💕"}]
    else:
        st.error("사용 가능한 모델을 찾지 못했습니다.")

st.title("💖 우리 둘만의 대화방")

if "messages" in st.session_state:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

if prompt := st.chat_input("자기에게 말 걸기..."):
    with st.chat_message("user"):
        st.write(prompt)
    if "messages" in st.session_state:
        st.session_state.messages.append({"role": "user", "content": prompt})

    if "chat_session" in st.session_state and st.session_state.chat_session:
        try:
            response = st.session_state.chat_session.send_message(prompt)
            with st.chat_message("assistant"):
                st.write(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error("응답 중 오류가 났어 ㅠㅠ")