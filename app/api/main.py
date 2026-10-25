from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from app.core.run_manager import create_run
from app.agents.generate_graph import graph
from app.agents.publish_graph import publish_graph
from langgraph.types import Command
from dotenv import load_dotenv
load_dotenv()


class GenerateRequest(BaseModel):
    request:str

class Decision(BaseModel):
    run_id:str


app=FastAPI()


@app.post('/generate')
def create_new_run(state:GenerateRequest):
    run_id,run_dir=create_run()


    initial_state={
    'request':state.request,
    'run_id':run_id,
    'run_dir':run_dir,
    'attempts':0,
    }


    config={
        'configurable':{
            'thread_id':run_id
        }
    }

    result=graph.invoke(initial_state,config)

    value=result['__interrupt__'][0].value

    return {'value':value,
            'run_id':run_id}


@app.post('/approve')
def approve_request(state:Decision):

    config={
        'configurable':{
            'thread_id':state.run_id
        }
    }

    check_next=graph.get_state(config).next

    if check_next:
        result=graph.invoke(Command(resume='Approve'),config)
        decision=result['decision']        


        values=graph.get_state(config).values
        repo_url = None
        publish_dict={'run_id':values.get('run_id'),
                      'run_dir':values.get('run_dir'),
                      'request':values.get('request'),
                      'code':values.get('code')}

        
        if decision == 'Approve' and not values.get('error'):
            publish_result=publish_graph.invoke(publish_dict)
            repo_url = publish_result['repo_url']


        return {'run_id':state.run_id,
                'decision':decision,
                'repo_url':repo_url}

    else :
        raise HTTPException(404,'Run Not Found or Either Run is completed !!')




@app.post('/reject')
def reject_request(state:Decision):

    config={
        'configurable':{
            'thread_id':state.run_id
        }
    }

    check_next=graph.get_state(config).next

    if check_next:
        result=graph.invoke(Command(resume='Reject'),config)
        decision=result['decision']        

        return {'run_id':state.run_id,
                'decision':decision}

    else :
        raise HTTPException(404,'Run Not Found or Either Run is completed !!')


@app.get('/status/{run_id}')
def check_status(run_id:str):
    config={
        'configurable':{
            'thread_id': run_id
        }
    }


    state=graph.get_state(config)
    current_state=state.values
    further_state=state.next


    if current_state=={} and further_state==():
        raise HTTPException(404,'Run not found')
    elif current_state!={} and further_state==():
        status='finished'
    elif further_state:
        status='waiting'

    return {'run_id':current_state.get('run_id'),
            'model_used':current_state.get('model_used'),
            'decision':current_state.get('decision'),
            'attempts':current_state.get('attempts'),
            'status':status
            }