import streamlit as st
import importlib.util


# Set page config once at the start of app.py
st.set_page_config(
    page_title="Option Visualization",
    page_icon="🦸‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        html, body, [class*="css"]  {
            font-size: 22px;
        }
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        .stButton>button {
            height: 3em;
            font-size: 1.2em;
        }
        .stMetric {
            font-size: 1.5em;
        }
        .metric-container .delta {
            display: inline-block !important;
            margin-left: 10px;
            font-size: 1.2em;
        }
    </style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("MENU")

# Main pages
main_page = st.sidebar.selectbox(
    "  ", 
    ["Profiles", "BlackScholes", "PNL"]
)

if main_page == "Profiles":
    profiles_page = st.sidebar.radio(
        "Profiles Pages",
        ["AppProfile", 'AppProfile2X', "Butterfly", "Condor", "Spread", 'allCallSPX', 'allPutSPX']
    )
elif main_page == "BlackScholes":
    blackscholes_page = st.sidebar.radio(
        "BlackScholes Pages",
        ["BlackScholes", "BlackScholesIndex"]
    )
elif main_page == "PNL":
    xsens_page = st.sidebar.radio(
        "PNL Pages",
        ["PNL", "PNLIndex", "PNLHistory"]
    )


# Display content in the main area based on selection
if main_page == "Profiles":
    if profiles_page == "AppProfile":
        # Load 'AppProfile.py' content
        spec = importlib.util.spec_from_file_location("AppProfile", "pages/Profiles/AppProfile.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    elif profiles_page == "AppProfile2X":
        # Load 'AppProfile2X.py' content
        spec = importlib.util.spec_from_file_location("AppProfile2X", "pages/Profiles/AppProfile2X.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    elif profiles_page == "Butterfly":
        # Load 'Butterfly.py' content
        spec = importlib.util.spec_from_file_location("Butterfly", "pages/Profiles/Butterfly.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    elif profiles_page == "Condor":
        # Load 'Condor.py' content
        spec = importlib.util.spec_from_file_location("Condor", "pages/Profiles/Condor.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    elif profiles_page == "Spread":
        # Load 'Spread.py' content
        spec = importlib.util.spec_from_file_location("Spread", "pages/Profiles/Spread.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    elif profiles_page == "allCallSPX":
        # Load 'allCallSpx.py' content
        spec = importlib.util.spec_from_file_location("allCallSpx", "pages/Profiles/allCallSpx.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    elif profiles_page == "allPutSPX":
        # Load 'allPutSpx.py' content
        spec = importlib.util.spec_from_file_location("allPutSpx", "pages/Profiles/allPutSpx.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
elif main_page == "BlackScholes":
    if blackscholes_page == "BlackScholes":
        # Load 'BlackScholes.py' content
        spec = importlib.util.spec_from_file_location("BlackScholes", "pages/BlackScholes/BlackScholes.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    elif blackscholes_page == "BlackScholesIndex":
        # Load 'BlackScholesIndex.py' content
        spec = importlib.util.spec_from_file_location("BlackScholesIndex", "pages/BlackScholes/BlackScholesIndex.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

elif main_page == "PNL":
    if xsens_page == "PNL":
        # Load 'PNL.py' content
        spec = importlib.util.spec_from_file_location("PNL", "pages/PNL/PNL.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    elif xsens_page == "PNLIndex":
        # Load 'PNLIndex.py' content
        spec = importlib.util.spec_from_file_location("PNLIndex", "pages/PNL/PNLIndex.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    elif xsens_page == "PNLHistory":
        # Load 'PNLHistory.py' content
        spec = importlib.util.spec_from_file_location("PNLHistory", "pages/PNL/PNLHistory.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    