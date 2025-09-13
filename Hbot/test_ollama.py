# test_ollama.py
from langchain_community.llms import Ollama

print("Attempting to connect to Ollama...")

try:
    # This connects to your running Ollama application
    llm = Ollama(model="llama3.1")
    
    print("Connection successful. Asking a simple question...")
    
    # This sends a request to the Llama 3.1 model
    response = llm.invoke("Why is the sky blue?")
    
    print("\n--- Ollama's Response ---")
    print(response)
    print("\nSUCCESS: Your connection to Ollama is working correctly!")

except Exception as e:
    print("\n--- TEST FAILED ---")
    print(f"An error occurred: {e}")
    print("\nTroubleshooting:")
    print("1. Is the Ollama desktop application running?")
    print("2. Did you successfully run 'ollama run llama3.1' in a terminal before?")
    print("3. Is there a firewall blocking the connection?")