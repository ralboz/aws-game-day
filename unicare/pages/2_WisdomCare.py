import boto3
import s3fs
import streamlit as st

# Set up Streamlit page configuration
st.set_page_config(
    page_title="WisdomCare",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS styles
st.markdown("""
    <style>
    .block-container {padding-top: 1rem;padding-bottom: 0rem;padding-left: 5rem;padding-right: 5rem}
    h1 {text-align: center;}
    MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
    
# Your Multimodal Knowledge Base ID
knowledge_base_id='TODO'


fs = s3fs.S3FileSystem(anon=False)


# Retrieve from multimodal knowledge base
def retrieve_from_knowledge_base(query, knowledge_base_id):
    bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
    
    promptTemplate = """
    \n\nhuman: I will provide you with a set of search results and a user's question. Your job is to answer the user's question using only information from the search results
    \n\nHere are the search results: $search_results$
    \n\nHere is the user's question: 
    <question>
    $query$
    </question>
    $output_format_instructions$
    \n\nassistant: 
    """

    try:
        response = bedrock_agent_runtime.retrieve_and_generate(
            input={
                'text': query
            },
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'generationConfiguration': {
                        'promptTemplate': {
                            'textPromptTemplate': promptTemplate
                        }
                    },
                    'knowledgeBaseId': knowledge_base_id,
                    'modelArn': 'us.amazon.nova-lite-v1:0',
                    'retrievalConfiguration': {
                        'vectorSearchConfiguration': {
                            'numberOfResults': 5
                        }
                    }
                }
            }
        )
        
        
        answer = response['output']['text']
        citation = response['citations'][0]['retrievedReferences'][0]['metadata'].get('x-amz-bedrock-kb-source-uri', None) 
        sourceimage = response['citations'][0]['retrievedReferences'][0]['metadata'].get('x-amz-bedrock-kb-byte-content-source', None)
        
        return answer, citation, sourceimage

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None, None, None
        


if __name__ == "__main__":
    
    st.title(":rainbow[UniCare Generative AI]")
    st.header(":medical_symbol: :rainbow[WisdomCare]")
    st.subheader("_Multimodal Knowledge Base_", divider='rainbow')
    container = st.container(border=True)
    container.write("""
    Explore public health information. Here are some sample queries:
    - How is the progression of clade Ib monkeypox virus infection?
    - Which municipality has the lowest number of dengue cases?
    - What was the daily percentage of wildfire related encounters in LA?
    - What are the characteristics of ED and urgent care encounters and hospitalization for COVID-19 like illnesses?
    - What are the characteristics of Idiopathic pulmonary fibrosis decedents?
    """)
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    
    if prompt := st.chat_input("Ask me a question"):
        with st.chat_message("human"):
            st.markdown(prompt)
                
        st.session_state.messages.append({"role": "human", "content": prompt})
            
        with st.chat_message("assistant"):
            with st.spinner('Processing...'):
                message_placeholder = st.empty()
                answer, citation, sourceimage = retrieve_from_knowledge_base(prompt, knowledge_base_id)
                message_placeholder.markdown(answer)
                if sourceimage:
                    st.image(fs.open(sourceimage, mode='rb').read())
                    st.write(f"**Source image:** `{fs.unstrip_protocol(sourceimage)}`")
                if citation:
                    st.write(f"**Citation:** `{citation}`")
        st.session_state.messages.append({"role": "assistant", "content": answer, "citation": citation, "source image": sourceimage})
        
