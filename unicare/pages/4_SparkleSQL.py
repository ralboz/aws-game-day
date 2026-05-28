import os
import re
import json
import boto3
import sagemaker
import streamlit as st
import pandas as pd
import mysql.connector
from langchain_aws import ChatBedrockConverse
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import AmazonTextractPDFLoader

# Set up Streamlit page configuration
st.set_page_config(
    page_title="Sparkle SQL",
    page_icon=":🦄",
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


class AuroraManager:
    def __init__(self, cluster_identifier):
        self.region_name = os.environ.get("AWS_REGION") 
        self.rds = boto3.client('rds', region_name=self.region_name)
        self.cluster_identifier = cluster_identifier
        self.host, self.user, self.password, self.database = self.get_connection_details()
        self.connection = self.connect_to_database()

    def get_connection_details(self):
        db_host = self.rds.describe_db_clusters(DBClusterIdentifier=self.cluster_identifier)
        endpoint = db_host['DBClusters'][0]['Endpoint']
        return endpoint, "UnicornAdmin", "UnicornsRock!", "healthdb"

    def connect_to_database(self):
        try:
            db = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            return db
        except mysql.connector.Error as err:
            st.error(f"Error connecting to database: {err}")
            return None
    
    def get_health(self):
        if self.connection:
            cursor = self.connection.cursor()
            try:
                cursor.execute("SELECT * FROM health LIMIT 10")
                health_data = cursor.fetchall()
                return health_data
            except mysql.connector.Error as err:
                st.error(f"Error fetching data: {err}")
                return []
        else:
            return []
            
    def execute_sql(self, query):
        if self.connection:
            cursor = self.connection.cursor()
            try:
                results = cursor.execute(query)
                results = cursor.fetchall()
                return results
            except mysql.connector.Error as err:
                st.error(f"Error fetching data: {err}")
                return []
        else:
            return []

llm = ChatBedrockConverse(model="us.amazon.nova-lite-v1:0") 
#llm = ChatBedrockConverse(model="us.amazon.nova-pro-v1:0") 

# Connect to the Amazon Aurora MySQL database
cluster_identifier = 'healthdb'
aurora_manager = AuroraManager(cluster_identifier)

# Get SQL query from LLM
def get_sql(question):
        
    template = """
    
    Given the database description and schema in the database and schema, write a SQL statement to answer the question provided by the user. 
    The database engine is Aurora MySQL so ensure that all functions are MySQL compatible.  
    If the question is not related to the provided database information, respond that the question is not relevant and wrap the response. 
    If the question is ambiguously worded ask for clarification. Return only a valid SQL query and nothing else.
    
    database_name='healthdb'
    table_name= 'health'
    column_names= [
    'YearCol', 'StateAbbr', 'StateDesc', 'LocationName', 'Category', 'Measure',
    'Data_Value_Unit', 'Data_Value_Type', 'Data_Value', 'Low_Confidence_Limit',
    'High_Confidence_Limit', 'TotalPopulation', 'TotalPop18plus', 'LocationID',
    'CategoryID', 'MeasureId', 'DataValueTypeID', 'Short_Question_Text', 'Latitude', 'Longitude'
    ]
        
    For example:
    question: Which state has the highest count of stroke
    SQL Query:
        SELECT StateAbbr, SUM(Data_Value) AS TotalStrokeCount
        FROM health
        WHERE Measure LIKE 'stroke'
        GROUP BY StateAbbr
        ORDER BY TotalStrokeCount DESC
        LIMIT 1;
        
    question: Filter latitude and longitude for prevention category in Florida
    SQL Query:
        SELECT Latitude, Longitude, LocationName, Measure
        FROM health
        WHERE Category = 'Prevention' AND StateDesc = 'Florida';
        
    question: What state has the highest cholesterol measure in 2021
    SQL Query:
        SELECT StateAbbr, SUM(Data_Value) AS TotalCholesterol
        FROM health
        WHERE Measure LIKE '%cholesterol%' AND YearCol = 2021
        GROUP BY StateAbbr
        ORDER BY TotalCholesterol DESC
        LIMIT 1;
        
    your turn: 
    question: {question}
    SQL query: 
    
    Write the SQL query inside <output></output>
    
    """

    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm 
    
    response = chain.invoke({
        "question": question
    })
    
    # Extract SQL query
    response_content = response.content
    generated_query = re.sub(r'<[^>]+>', '', response_content)
 
    st.markdown("**Generated SQL query:**")
    st.write(generated_query)
    return generated_query
        
 
# Summarize the results
def generate_response(question, result):
    
    print("\nQuery Result:", result)
    
    template = """
    
    Using the provided context write a brief explanation of the SQL query logic. 
    Then briefly summarize the {result} in a way that best answers the provided {question}. If the dataset provided contains no data say so.
    
    question: {question},
    "result": {result}
        
    
    """

    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm 
    
    response = chain.invoke({
        "question": question,
        "result": result
    })
    
    return response.content
    
    
if __name__ == "__main__":
    
    st.title(":rainbow[UniCare Generative AI]")
    st.header(":gear: :rainbow[Sparkle SQL]")
    st.subheader("_Text-to-SQL Generator_", divider='rainbow')
    
    
    
    option = st.selectbox(
        "Select a sample question and SparkleSQL will generate a SQL query for you. Here is a preview of the database:", 
        (
            "Summarize health category in Georgia", 
            "What are the key measures in 2021 by states?", 
            "What are the types of disability measure and which state shows the highest priority for each measure?",
            "What state has the lowest rate of heart related measure in 2022?",
            "What is the trend of prevention category by measure throughout 2021 and 2022?",
            "Summarize the location name by latitude and longitude for asthma in New York"
        ),
        index=None,
        placeholder="Select a sample question...",
    )
    
    st.write("You selected:", option)
    
    
    # Display local health data
    healthdata = aurora_manager.get_health()
    if healthdata:
        health_data = pd.DataFrame(healthdata, columns=['YearCol', 'StateAbbr', 'StateDesc','LocationName', 'Category', 'Measure', 'Data_Value_Unit', 'Data_Value_Type', 'Data_Value', 'Low_Confidence_Limit', 'High_Confidence_Limit', 'TotalPopulation', 'TotalPop18plus', 'LocationID', 'CategoryID', 'MeasureId', 'DataValueTypeID', 'Short_Question_Text', 'Latitude', 'Longitude'])
    else:
        st.write("No data available.")
    st.dataframe(health_data, use_container_width=True, hide_index=True)
    
    if option:
        user_query = get_sql(option)
    
        model_result = aurora_manager.execute_sql(user_query)
    
        final_response = generate_response(option, model_result)
        
        container = st.container(border=True)
        container.write(final_response)

