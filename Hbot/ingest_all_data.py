# ingest_all_data.py
import os
import pandas as pd
from langchain.docstore.document import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings

# --- Configuration ---
DATA_PATH = "data/"
DISEASE_SYMPTOMS_FILE = os.path.join(DATA_PATH, "dataset.csv")
DISEASE_DESCRIPTION_FILE = os.path.join(DATA_PATH, "symptom_Description.csv")
DISEASE_PRECAUTIONS_FILE = os.path.join(DATA_PATH, "symptom_precaution.csv")
VACCINATION_STATS_FILE = os.path.join(DATA_PATH, "Baby_Vaccination_India_2021.xlsx")

def process_disease_data():
    """Loads, merges, and formats all disease-related information."""
    try:
        symptoms_df = pd.read_csv(DISEASE_SYMPTOMS_FILE)
        description_df = pd.read_csv(DISEASE_DESCRIPTION_FILE)
        precautions_df = pd.read_csv(DISEASE_PRECAUTIONS_FILE)
    except FileNotFoundError as e:
        print(f"Error: {e}. Make sure your CSV files are in the 'data/' folder and named correctly.")
        return []

    symptom_cols = [col for col in symptoms_df.columns if 'Symptom' in col]
    symptoms_agg = symptoms_df.groupby('Disease')[symptom_cols].apply(
        lambda x: x.stack().dropna().unique().tolist()
    ).to_dict()

    precaution_cols = [col for col in precautions_df.columns if 'Precaution' in col]
    precautions_agg = precautions_df.groupby('Disease')[precaution_cols].apply(
        lambda x: x.stack().dropna().unique().tolist()
    ).to_dict()

    all_diseases = description_df.set_index('Disease')['Description'].to_dict()
    
    disease_docs = []
    for disease, description in all_diseases.items():
        symptoms = symptoms_agg.get(disease, [])
        precautions = precautions_agg.get(disease, [])
        
        content = (
            f"Information about {disease}:\n\n"
            f"Description: {description}\n\n"
            f"Common Symptoms: {', '.join(symptoms) if symptoms else 'Not specified'}\n\n"
            f"Recommended Precautions: {', '.join(precautions) if precautions else 'Not specified'}"
        )
        
        doc = Document(page_content=content, metadata={"source": "disease_database", "disease": disease})
        disease_docs.append(doc)
        
    print(f"Processed {len(disease_docs)} unique diseases.")
    return disease_docs


def process_vaccination_stats():
    """
    Loads and transforms vaccination statistics, skipping the malformed header.
    """
    print("Processing vaccination stats with a robust method...")
    try:
        # header=None: We are telling pandas there's no header.
        # skiprows=3: We skip the first 3 lines. Adjust this if your data starts on a different row.
        # Example: if data starts on row 5, use skiprows=4
        stats_df = pd.read_csv(
            VACCINATION_STATS_FILE,
            encoding='latin1',
            header=None,
            skiprows=3 
        )
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to parse {VACCINATION_STATS_FILE}. Error: {e}")
        print("Please open the CSV file and confirm which line the data starts on.")
        return []

    # Let's manually provide the correct headers based on your image
    headers = [
        "States/UTs", "Area", "Children fully vaccinated (recall)", 
        "Children fully vaccinated (card)", "Received BCG", "Received 3 doses polio", 
        "Received 3 doses DPT", "Received 1 dose measles", "Received 2 doses measles", 
        "Received 3 doses rotavirus", "Received 3 doses hepatitis B", "Received vitamin A", 
        "Received vaccinations in public facility", "Received vaccinations in private facility"
    ]
    
    # We need to make sure the number of headers matches the number of columns pandas found
    if len(headers) != len(stats_df.columns):
        print(f"WARNING: Mismatch in column count. Expected {len(headers)} headers but file has {len(stats_df.columns)} columns.")
        # We will truncate or pad headers to match the dataframe
        stats_df = stats_df.iloc[:, :len(headers)] # Use the first N columns
        stats_df.columns = headers[:len(stats_df.columns)]
    else:
        stats_df.columns = headers

    stats_df.dropna(how='all', inplace=True) # Drop fully empty rows

    stat_docs = []
    for index, row in stats_df.iterrows():
        location = row['States/UTs']
        area = row['Area']
        
        for col_name, value in row.items():
            if col_name not in ['States/UTs', 'Area'] and pd.notna(value):
                content = f"In {location} ({area}), the statistic for '{col_name}' is {value}%."
                doc = Document(
                    page_content=content,
                    metadata={"source": VACCINATION_STATS_FILE, "location": f"{location} ({area})"}
                )
                stat_docs.append(doc)

    print(f"Successfully created {len(stat_docs)} documents from vaccination statistics.")
    return stat_docs


if __name__ == "__main__":
    print("Starting data ingestion from all sources...")
    
    disease_documents = process_disease_data()
    vaccination_documents = process_vaccination_stats()
    all_documents = disease_documents + vaccination_documents
    
    if not all_documents:
        print("No documents were created. Halting ingestion.")
        exit()

    print("Initializing embedding model...")
    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    print("Creating vector store... This may take a few minutes.")
    vectorstore = Chroma.from_documents(
        documents=all_documents,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )

    print(f"\nSuccessfully created vector store with {len(all_documents)} documents.")