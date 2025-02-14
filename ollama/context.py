import requests
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='ollama_chat.log'
)

class OllamaChat:
    def __init__(self, ip: str = "192.168.1.17", model: str = "tinyllama", max_retries: int = 3):
        self.base_url = f"http://{ip}:11434"
        self.model = model
        self.max_retries = max_retries
        self.conversation_history: List[Dict[str, str]] = []
        
    def _make_request(self, endpoint: str, data: dict, stream: bool = False) -> Optional[requests.Response]:
        """Make HTTP request with retry logic"""
        url = f"{self.base_url}/{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        logging.info(f"Making request to: {url}")
        logging.info(f"Request data: {json.dumps(data, indent=2)}")
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(url, headers=headers, json=data, stream=stream)
                response.raise_for_status()
                if not stream:
                    logging.info(f"Response status: {response.status_code}")
                    logging.info(f"Response content: {response.text[:500]}...")
                return response
            except requests.exceptions.RequestException as e:
                logging.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)

    def chat(self, prompt: str, stream: bool = False) -> str:
        """Send a message and get response"""
        data = {
            "model": self.model,
            "prompt": prompt,  # Using prompt instead of messages for /api/generate
            "stream": stream
        }
        
        try:
            if stream:
                return self._handle_streaming_response(data)
            else:
                return self._handle_normal_response(data)
        except Exception as e:
            logging.error(f"Error in chat: {str(e)}")
            raise

    def _handle_normal_response(self, data: dict) -> str:
        """Handle normal (non-streaming) response"""
        response = self._make_request("api/generate", data)  # Changed to api/generate
        result = response.json()
        
        message = result.get('response', '')
        self.conversation_history.append(
            {"role": "user", "content": data["prompt"]},
            {"role": "assistant", "content": message}
        )
        
        return message

    def _handle_streaming_response(self, data: dict) -> str:
        """Handle streaming response"""
        full_response = []
        response = self._make_request("api/generate", data, stream=True)  # Changed to api/generate
        
        for line in response.iter_lines():
            if line:
                try:
                    json_response = json.loads(line)
                    logging.debug(f"Streaming response chunk: {json_response}")
                    if 'response' in json_response:
                        chunk = json_response['response']
                        print(chunk, end='', flush=True)
                        full_response.append(chunk)
                    
                    if json_response.get('done', False):
                        print()
                        break
                except json.JSONDecodeError as e:
                    logging.error(f"Error decoding JSON: {str(e)}, Line: {line}")
        
        message = ''.join(full_response)
        self.conversation_history.append(
            {"role": "user", "content": data["prompt"]},
            {"role": "assistant", "content": message}
        )
        return message

# Example usage
if __name__ == "__main__":
    try:
        # Initialize chat
        chat = OllamaChat()
        
        # Test connection first
        print("Testing connection to Ollama...")
        test_response = requests.get(f"{chat.base_url}/api/tags")
        print(f"Connection test response: {test_response.status_code}")
        print(f"Available models: {test_response.json()}")
        
        # Example conversation
        prompts = [
            "What is Python?",
            "Can you provide some example code?",
            "What are its main advantages?"
        ]
        
        for prompt in prompts:
            print(f"\nUser: {prompt}")
            print("Assistant:", end=" ")
            try:
                response = chat.chat(prompt, stream=True)
                if not response:
                    print("No response received")
            except Exception as e:
                print(f"Error getting response: {str(e)}")
            
    except Exception as e:
        logging.error(f"Main program error: {str(e)}")
        print(f"An error occurred: {str(e)}")