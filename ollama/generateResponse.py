import requests
import json

def ask_ollama(prompt, model="tinyllama", ip="192.168.1.17"):
    """
    Send a prompt to Ollama and get the response
    
    Args:
        prompt (str): The question or prompt to send
        model (str): The model to use (default: tinyllama)
        ip (str): IP address of the Ollama server
    """
    url = f"http://127.0.0.1:11434/api/generate"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False  # Set to True if you want to stream the response
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        result = response.json()
        return result.get('response', 'No response received')
        
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")
        return None

# Example usage
if __name__ == "__main__":
    prompt = "What is the capital of Italy?"
    response = ask_ollama(prompt)
    
    if response:
        print(f"Question: {prompt}")
        print(f"Answer: {response}")