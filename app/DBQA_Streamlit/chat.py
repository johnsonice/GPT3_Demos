### chat functionalities 

#%%
import os,json
#import chromadb
import langchain
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
#from langchain.llms import OpenAI
from langchain import OpenAI, VectorDBQA,VectorDBQAWithSourcesChain

#%%
def load_json(f_path):
    with open(f_path) as f:
        data = json.load(f)
    
    return data

class DBQA(object):
    def __init__(self,Index_Save_Path,api_key,
                 top_k=4,
                 temperature=0.0,
                 chain_type="stuff"):
        self.Index_Save_Path = Index_Save_Path
        self.openai_api_key = api_key
        self.temperature=temperature
        self.chain_type = chain_type
        self.top_k = top_k
        self.embed = OpenAIEmbeddings(
                        document_model_name='text-embedding-ada-002',
                        query_model_name='text-embedding-ada-002',        ## you can set different model to embed queries 
                        openai_api_key=self.openai_api_key 
                    )
        self.vectordb = Chroma(persist_directory=Index_Save_Path, 
                               embedding_function=self.embed)
            
        # completion llm
        self.llm = OpenAI(
                        openai_api_key=self.openai_api_key,
                        model_name='gpt-3.5-turbo',
                        temperature=temperature
                    )
        self.qa_with_sources = VectorDBQAWithSourcesChain.from_chain_type(
                                llm=self.llm,
                                chain_type=self.chain_type,#only work with small context 
                                vectorstore=self.vectordb,
                                k=self.top_k,
                                return_source_documents=True)
    @staticmethod
    def _format_response(res_obj):
        references = [d.page_content for d in res_obj['source_documents']] 
        sources = [d.metadata['source'].split('/')[-1] for d in res_obj['source_documents']] 

        ref_list = []
        for i in range(len(references)):
            ref_list.append("Reference {}; Source {}:".format(i,sources[i]))
            ref_list.append(references[i])
        ref_str = "\n\n".join(ref_list)

        res_str = "Bot Response : \n\n{}\n\n------------------\n{}".format(res_obj['answer'],ref_str)

        return res_str
    
    def get_response(self,Q,format_response=True):
        if isinstance(Q,str) and len(Q)>0:
            pass
        else:
            return ""
        
        res = self.qa_with_sources(Q)
        
        if format_response:
            res = self._format_response(res)
        
        return res
    

    

#%%
if __name__ == "__main__":
    openai_key = load_json('/home/chuang/Dev/Keys/openai_key.json') 
    key = openai_key['ChatGPT']['API_KEY']
    # Loading from a directory
    Index_Save_Path = '/data/chuang/QA_LangChan/KB_Index/chroma'
    
    QA_agent = DBQA(Index_Save_Path,key )

    Q = "what is our macro economic forecast for 2022" 
    print(QA_agent.get_response(Q))

# %%
