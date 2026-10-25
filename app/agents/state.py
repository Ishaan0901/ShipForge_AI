from typing import List, TypedDict,Literal

class GenerateState(TypedDict):
    request:str     
    run_id:str      
    run_dir:str     
    code:str
    error:str
    attempts:int
    model_used:str
    output:str
    decision:Literal['Approve','Reject']



class PublishState(TypedDict):
    run_id:str
    run_dir:str
    request:str
    code:str
    secrets_found:List[dict]
    repo_url:str
    status:Literal['scanned','pushed','failed','readme_done']