from langgraph.graph import StateGraph,START,END
from langgraph.checkpoint.sqlite import SqliteSaver
from app.tools.code_tools import save_code,run_code
from app.agents.state import GenerateState
from langgraph.types import interrupt
from app.core.models import call_llm
from dotenv import load_dotenv
import sqlite3
import os
load_dotenv()


connection=sqlite3.connect(os.getenv('CHECKPOINT_DB','checkpoints.db'),check_same_thread=False)
checkpointer=SqliteSaver(connection)


def generate(state:GenerateState):

    request=state['request']
    error=state.get('error','')
    attempts=state.get('attempts',0)+1
    old_code=state.get('code','')

    if error=='':
        prompt=f'''
        You are a Python code generator.
        Write a complete, runnable Python script for this request:

        {request}

        Rules:
        - Return ONLY the code. No explanation, no comments outside the code.
        - Do not use input(). The script must run without user interaction.
        - Do not read or write files outside the current folder.
        - Print the final result so the output is visible.
'''
    else :
        prompt=f'''
            You are a Python code generator.
            The code below failed. Fix it.
        
            Original request:
            {request}
        
            Old_Code:
            {old_code}
        
            Error:
            {error}
        
            Rules:
            - Return the full corrected script, not just the changed lines.
            - Return ONLY the code. No explanation.
            - Do not use input(). The script must run without user interaction.
            - Do not read or write files outside the current folder.
            - Print the final result so the output is visible.
            ''' 

    model_used,code=call_llm(prompt)

    return {'model_used':model_used, 
            'code':code,
            'attempts':attempts}



def run(state:GenerateState):
    code=state['code']
    run_dir=state['run_dir']

    #   Save the code using save_code funtion :
    path=save_code(code,run_dir)

    #   Run the code using run_code function :
    result=run_code(path)

    if result[0]!=0:
        return {'error':result[1],
                'output':result[2]}
    return {'error':'',
            'output':result[2]}



def retry_condition(state:GenerateState):
    attempt=state.get('attempts',0)
    error=state.get('error','')

    if attempt<3 and error!='':
        return 'Retry'
    else:
        return 'Done'



def approval(state:GenerateState):
    code=state.get('code','')
    output=state.get('output','')
    error=state.get('error','')
    model_used=state.get('model_used','')

    human_response=interrupt({
        'output': f'{output}',
        'error':f'{error}',
        'model_used':f'{model_used}',
        'code':f'{code}'
    })

    if human_response=='Approve':
        return {'decision':'Approve'}
    else:
        return {'decision':'Reject'}




builder=StateGraph(GenerateState)

builder.add_node('generate',generate)
builder.add_node('run',run)
builder.add_node('approval',approval)

builder.add_edge(START,'generate')
builder.add_edge('generate','run')
builder.add_conditional_edges('run',retry_condition,{
                                'Retry': 'generate',
                                'Done': 'approval' })
builder.add_edge('approval',END)

graph=builder.compile(checkpointer=checkpointer)


