from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import logging
load_dotenv()


#   Models to be used:
MODEL_PRIMARY='openai/gpt-oss-20b'
MODEL_FALLBACK_1='openai/gpt-oss-120b'
MODEL_FALLBACK_2='qwen/qwen3.8-27b'
MODEL_FALLBACK_3='gemini-3.1-flash-lite'



#   Setting up the models:
model_1=ChatGroq(
    model=MODEL_PRIMARY,
    temperature=0.3
)

model_2=ChatGroq(
    model=MODEL_FALLBACK_1,
    temperature=0.3
)

model_3=ChatGroq(
    model=MODEL_FALLBACK_2,
    temperature=0.3
)

model_4=ChatGoogleGenerativeAI(
    model=MODEL_FALLBACK_3,
    temperature=0.3
)



#   Fallback:
llm=model_1.with_fallbacks([model_2,model_3,model_4])



#   Function:
logging.basicConfig(level=logging.INFO)

def call_llm(query):
    response=llm.invoke(query)

    model_name=response.response_metadata.get('model_name','unknown')
    model_answer=response.text

    logging.info(f'Answered by: {model_name}')

    return model_name,model_answer