from fastapi import FastAPI,Response,Request,status
from pydantic import BaseModel, HttpUrl
from langchain_community.document_loaders import YoutubeLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from fastapi.middleware.cors import CORSMiddleware
import json , os
from services.genai import YoutubeProcessor ,GeminiProcessor
from constants import VertexAIConfig

from dotenv import load_dotenv
load_dotenv()

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]=os.getenv("GOOGLE_APPLICATION_CREDENTIALS")



class VideoAnalysisRequest(BaseModel):
    youtube_link: HttpUrl


app=FastAPI()
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

@app.post("/analyze_video")
def analyze_video(request: VideoAnalysisRequest):
    try:
        summary=""
        gemini_processor=GeminiProcessor(**VertexAIConfig.LLM_CONFIG.value)
        youtube_processor=YoutubeProcessor(gemini_processor=gemini_processor)
        results=youtube_processor.retrieve_youtube_documents(str(request.youtube_link),verbose=True)
        key_concepts=youtube_processor.find_key_concepts(documents=results,group_size=2)
        #if results and len(results)>0:
        #    summary=gemini_processor.generate_document_summary(results,verbose=True)

    except Exception as e:
        print(e)
        return {"status":"error","message":str(e)}
    #return results[0].metadata if len(results)>0 else ""
    print({"key_concepts":key_concepts})
    return {"key_concepts":key_concepts}
