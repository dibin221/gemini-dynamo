from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import YoutubeLoader
from langchain_google_vertexai import VertexAI
from vertexai.generative_models import GenerativeModel
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
import logging , json ,re
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger=logging.getLogger(__name__)
pattern = r"\[([\s\S]*?)\]"

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

    def count_total_tokens(self,docs:list):
        temp_model=GenerativeModel("gemini-1.0-pro")
        total=0
        logger.info("Counting total billable characters....")
        for doc in tqdm(docs):
            total+=temp_model.count_tokens(doc.page_content).total_billable_characters
        return total

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

                                        Respond in the following format as a JSON object without backticks separating each concept with a comma:
                                        [{{"term":<concept>,"definition":<definition>"}},{{"term":<concept>,"definition":<definition>"}},....]
                                        """,
                                        input_variables=["text"])

    def find_key_concepts (self,documents:list,sample_size:int=0,verbose=False):
        if sample_size>len(documents):
            raise ValueError("Group size cannot be greater than the number of documents")

        # Optimize sample_size
        if sample_size==0:
            sample_size=len(documents) // 5
            if verbose:
                logger.info(f"No sample size specified, setting no of documents per sample as 5. Sample size: {sample_size}")

        # FInd no of documents in each group
        num_docs_per_group = len(documents) // sample_size + (len(documents) % sample_size > 0)

        # check threshold for response quality
        if num_docs_per_group>=10:
            raise ValueError("""Each group has more than 10 documents and putput quality will be degraded.
                             Increase the sample_size parameter to reduce no of documets per group.""")
        elif num_docs_per_group>5:
            logger.warn("Each group has more than 5 documents and output quality is likely to be degraded")

        document_subgroups =[]
        # Split the documents into group of size num_docs_per_group
        for i in range(0,len(documents),num_docs_per_group):
            document_subgroups.append(documents[i:i+sample_size])
        logger.info("Finding key concepts....")
        batch_concepts=[]
        for group in tqdm(document_subgroups):
            content=" ".join(doc.page_content for doc in group)

            chain= self.prompt | self.gemini_processor.model

            concept = chain.invoke({"text": content})
            try:
                concept_=concept
                # concept=concept.replace(
                #     "Here's a JSON object containing the key concepts and their definitions from the provided text:",""
                #     ).replace("```json", "").replace("```", "")
                concept="["+re.findall(pattern, concept)[0]+"]"
                batch_concepts.extend(json.loads(concept))
            except Exception as e:
                logger.error(f"error : {e}")
                logger.info(f"concept_ : {concept_}")
                logger.info(f"concept : {concept}")

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

            total_billable_characters=self.gemini_processor.count_total_tokens(results)

            if verbose:
                logger.info(f"{author}\n{length}\n{title}\n{total_size}\n{total_billable_characters}")

        except Exception as e:
            print(e)
            return {"status":"error","message":str(e)}
        return results

