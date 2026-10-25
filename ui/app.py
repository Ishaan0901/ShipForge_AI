import streamlit as st
import requests

API = 'http://127.0.0.1:8000'

st.set_page_config(page_title='ShipForge AI', page_icon='🚀', layout='centered')


def call_api(endpoint, body):
    try:
        r = requests.post(f'{API}/{endpoint}', json=body, timeout=120)
    except requests.exceptions.RequestException:
        st.error('Could not reach the server. Is FastAPI running?')
        return None

    if r.status_code != 200:
        st.error(r.json().get('detail', 'Something went wrong.'))
        return None

    return r.json()


def decide(endpoint):
    result = call_api(endpoint, {'run_id': st.session_state['run_id']})
    if result:
        st.session_state['decision'] = result['decision']
        st.session_state['repo_url'] = result.get('repo_url')
        st.rerun()


# ---------- Sidebar ----------
with st.sidebar:
    st.header('🚀 ShipForge AI')
    st.caption('Generate. Review. Ship.')
    st.markdown('1. Describe your code\n2. Review the code and output\n3. Approve to push to GitHub')

# ---------- Header ----------
st.title('🚀 ShipForge AI')
st.caption('Human-in-the-loop coding agent')

# ---------- Input ----------
input_text = st.text_area(
    'What should I build?',
    placeholder='Example: Write a code to print "Hello World"',
    height=100,
)

if st.button('Generate', type='primary', use_container_width=True):
    if input_text.strip() == '':
        st.warning('Empty input not allowed !!')
    else:
        with st.spinner('Generating and testing code...'):
            result = call_api('generate', {'request': input_text})
        if result:
            st.session_state['run_id'] = result['run_id']
            st.session_state['value'] = result['value']
            st.session_state.pop('decision', None)
            st.session_state.pop('repo_url', None)

# ---------- Result ----------
if 'run_id' in st.session_state:
    value = st.session_state['value']

    st.divider()
    col1, col2 = st.columns(2)
    col1.caption(f'Run ID: {st.session_state["run_id"][:8]}')
    col2.caption(f'Model: {value.get("model_used")}')

    code_tab, output_tab = st.tabs(['Code', 'Output'])
    with code_tab:
        st.code(value.get('code'), language='python')
    with output_tab:
        output = (value.get('output') or '').strip()
        if output:
            st.code(output, language='text')
        else:
            st.caption('No output')

    if value.get('error'):
        st.error(value['error'])

    # ---------- Decision ----------
    st.divider()
    if 'decision' in st.session_state:
        decision = st.session_state['decision']
        repo_url = st.session_state.get('repo_url')
        if decision == 'Approve':
            st.success('Approved')
            if repo_url:
                st.link_button('Open repo on GitHub', repo_url, use_container_width=True)
            else:
                st.warning('Code failed, push skipped')
        else:
            st.error('Rejected')
    else:
        b1, b2 = st.columns(2)
        if b1.button('Approve', type='primary', use_container_width=True):
            with st.spinner('Pushing to GitHub...'):
                decide('approve')
        if b2.button('Reject', use_container_width=True):
            decide('reject')