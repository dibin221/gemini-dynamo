from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import YoutubeLoader
from langchain_google_vertexai import VertexAI
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
import logging , json
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger=logging.getLogger(__name__)


class GeminiProcessor:
    """Initialize GeminiProcessor with VertexAI with passed model name , project and location."""
    def __init__(self,model_name:str, project:str, location:str) -> None:
        self.model=VertexAI(model_name=model_name,project=project,location=location)

    def generate_document_summary(self,documents:list, verbose:str):
        chain_type="stuff"
        if len(documents)>10:
            chain_type="map_reduce"
        chain = load_summarize_chain(self.model, chain_type=chain_type)
        docs=chain.run(documents)
        return docs

class YoutubeProcessor:

    def __init__(self,gemini_processor:GeminiProcessor) -> None:
            """
            Initializes the YoutubeProcessor with a text_splitter as RecursiveCharacterTextSplitter.
            """
            self.text_splitter =RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=0,
            length_function=len,
            is_separator_regex=False,
            )
            self.gemini_processor=gemini_processor
            self.prompt =PromptTemplate(template="""
                                        Find and define key concepts or terms found in the text:
                                        {text}

                                        Respond in the following format as a string separating each concept with a comma:
                                        "concept": "definition"
                                        """,
                                        input_variables=["text"])

    def find_key_concepts (self,documents:list,group_size:int=2):
        if group_size>len(documents):
            raise ValueError("Group size cannot be greater than the number of documents")

        # FInd no of documents in each group
        num_docs_per_group = len(documents) // group_size + (len(documents) % group_size > 0)
        document_subgroups =[]
        # Split the documents into group of size num_docs_per_group
        for i in range(0,len(documents),num_docs_per_group):
            document_subgroups.append(documents[i:i+group_size])
        logger.info("Finding key concepts....")
        batch_concepts=[]
        for group in tqdm(document_subgroups):
            content=" ".join(doc.page_content for doc in group)

            chain= self.prompt | self.gemini_processor.model

            concept = chain.invoke({"text": content})
            batch_concepts.append(concept)

        return batch_concepts


    def retrieve_youtube_documents(self,video_url:str,verbose=False):

        try:
            loader = YoutubeLoader.from_youtube_url(video_url,add_video_info=True)
            docs =loader.load()
            results=self.text_splitter.split_documents(docs)

            author=results[0].metadata['author']
            length=results[0].metadata['length']
            title=results[0].metadata['title']
            total_size=len(results)
            if verbose:
                logger.info(f"{author}\n{length}\n{title}\n{total_size}")

        except Exception as e:
            print(e)
            return {"status":"error","message":str(e)}
        return results

