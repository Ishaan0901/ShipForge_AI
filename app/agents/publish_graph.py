from langgraph.graph import StateGraph,START,END
from app.agents.state import PublishState
from app.tools.github_tools import scan_secrets,ensure_readme,push_to_github,make_repo_name
import os


#   Node-1:
def scan(state:PublishState):
    run_dir=state.get('run_dir')

    findings=scan_secrets(run_dir)

    return {'secrets_found':findings,
            'status':'scanned'}


#   Node-2:
def gen_readme(state:PublishState):
    run_dir=state.get('run_dir')
    request=state.get('request')
    code=state.get('code')

    ensure_readme(run_dir,request,code)

    return {'status':'readme_done'}


#   Node-3: 
def push(state:PublishState):
    run_id=state.get('run_id')
    request=state.get('request')
    run_dir=state.get('run_dir')
    secrets_found=state.get('secrets_found') or []

    token=os.getenv('GITHUB_TOKEN')

    repo_name=make_repo_name(request,run_id)

    repo_url=push_to_github(run_dir,repo_name,token,secrets_found)

    return {'repo_url':repo_url,
            'status':'pushed'}



builder=StateGraph(PublishState)

builder.add_node('scan',scan)
builder.add_node('gen_readme',gen_readme)
builder.add_node('push',push)

builder.add_edge(START,'scan')
builder.add_edge('scan','gen_readme')
builder.add_edge('gen_readme','push')
builder.add_edge('push',END)

publish_graph=builder.compile()