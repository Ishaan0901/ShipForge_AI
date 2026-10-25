from dotenv import load_dotenv
import uuid
import os
load_dotenv()

def create_run():

    #   Create a unique ID
    unique_id = str(uuid.uuid4())

    #   create a folder (runs)
    path=f'{os.getenv("RUNS_DIR","runs")}/{unique_id}'
    os.makedirs(path)

    #   Return the path and unique id
    return unique_id,path