import requests
import json

def ask_ollama_stream(prompt, model="tinyllama", ip="192.168.1.17"):
    """
    Send a prompt to Ollama and stream the response
    """
    url = f"http://{ip}:11434/api/generate"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "prompt": prompt,
        "stream": True
    }
    
    try:
        with requests.post(url, headers=headers, json=data, stream=True) as response:
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    json_response = json.loads(line)
                    if 'response' in json_response:
                        print(json_response['response'], end='', flush=True)
                    
                    # Check if done
                    if json_response.get('done', False):
                        print()  # New line at the end
                        break
                        
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")

# Example usage
if __name__ == "__main__":
    prompt = "Write a short poem about Python programming"
    ask_ollama_stream(prompt)