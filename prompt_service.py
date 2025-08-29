import requests
import logging
from typing import Optional, Dict, Any, List
import json

logger = logging.getLogger(__name__)

class PromptService:
    """
    Service class for fetching prompts from SnowX API.
    """
    
    def __init__(self, base_url: str = "https://snowx.ai/api-beta/api/chat-template"):
        """
        Initialize the PromptService.
        
        Args:
            base_url: Base URL for the SnowX API
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Aider-API-Client/1.0'
        })
    
    def get_prompt(self, group_name: str, key: str) -> Optional[str]:
        """
        Get a specific prompt by group name and key.
        
        Args:
            group_name: The group name (e.g., "AIDER_API")
            key: The message name/key to filter by (e.g., "TEST", "BASE_RULES")
            
        Returns:
            The text content of the prompt if found, None otherwise
        """
        try:
            # Construct the API URL
            url = f"{self.base_url}/{group_name}"
            
            logger.info(f"Fetching prompt from: {url}")
            
            # Make the API request
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse the JSON response
            data = response.json()
            
            logger.debug(f"API Response: {json.dumps(data, indent=2)}")
            
            # Validate response structure
            if not isinstance(data, dict) or 'data' not in data:
                logger.error(f"Invalid response structure: {data}")
                return None
            
            # Search for the prompt with the specified key
            for item in data.get('data', []):
                if not isinstance(item, dict) or 'messages' not in item:
                    continue
                
                # Check if this item matches the group name
                if item.get('type') != group_name:
                    continue
                
                # Search through messages for the specified key
                for message in item.get('messages', []):
                    if not isinstance(message, dict):
                        continue
                    
                    # Check if message name matches the key
                    if message.get('name') == key:
                        # Extract the text content
                        content = message.get('content', '')
                        if isinstance(content, str):
                            logger.info(f"Found prompt for {group_name}.{key}: {len(content)} characters")
                            return content
            
            logger.warning(f"Prompt not found for group: {group_name}, key: {key}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error fetching prompt {group_name}.{key}: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {group_name}.{key}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching prompt {group_name}.{key}: {str(e)}")
            return None
    
    def get_all_prompts(self, group_name: str) -> Dict[str, str]:
        """
        Get all prompts from a specific group.
        
        Args:
            group_name: The group name (e.g., "AIDER_API")
            
        Returns:
            Dictionary mapping prompt keys to their text content
        """
        try:
            url = f"{self.base_url}/{group_name}"
            
            logger.info(f"Fetching all prompts from: {url}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not isinstance(data, dict) or 'data' not in data:
                logger.error(f"Invalid response structure: {data}")
                return {}
            
            prompts = {}
            
            for item in data.get('data', []):
                if not isinstance(item, dict) or 'messages' not in item:
                    continue
                
                if item.get('type') != group_name:
                    continue
                
                for message in item.get('messages', []):
                    if not isinstance(message, dict):
                        continue
                    
                    key = message.get('name')
                    if not key:
                        continue
                    
                    content = message.get('content', [])
                    if isinstance(content, list) and len(content) > 0:
                        first_content = content[0]
                        if isinstance(first_content, dict) and first_content.get('type') == 'text':
                            text = first_content.get('text')
                            if text:
                                prompts[key] = text
            
            logger.info(f"Found {len(prompts)} prompts in group {group_name}")
            return prompts
            
        except Exception as e:
            logger.error(f"Error fetching all prompts from {group_name}: {str(e)}")
            return {}
    
    def list_available_keys(self, group_name: str) -> List[str]:
        """
        List all available prompt keys in a group.
        
        Args:
            group_name: The group name (e.g., "AIDER_API")
            
        Returns:
            List of available prompt keys
        """
        try:
            url = f"{self.base_url}/{group_name}"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not isinstance(data, dict) or 'data' not in data:
                return []
            
            keys = []
            
            for item in data.get('data', []):
                if not isinstance(item, dict) or 'messages' not in item:
                    continue
                
                if item.get('type') != group_name:
                    continue
                
                for message in item.get('messages', []):
                    if isinstance(message, dict) and message.get('name'):
                        keys.append(message['name'])
            
            return keys
            
        except Exception as e:
            logger.error(f"Error listing keys from {group_name}: {str(e)}")
            return []
    
    def close(self):
        """Close the session."""
        if self.session:
            self.session.close()


# Global instance for easy access
_prompt_service = None

def get_prompt_service() -> PromptService:
    """
    Get or create a global PromptService instance.
    
    Returns:
        PromptService instance
    """
    global _prompt_service
    if _prompt_service is None:
        _prompt_service = PromptService()
    return _prompt_service

def get_prompt(group_name: str, key: str) -> Optional[str]:
    """
    Convenience function to get a prompt using the global service instance.
    
    Args:
        group_name: The group name (e.g., "AIDER_API")
        key: The message name/key to filter by
        
    Returns:
        The text content of the prompt if found, None otherwise
    """
    service = get_prompt_service()
    return service.get_prompt(group_name, key)


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create service instance
    service = PromptService()
    
    # Example: Get a specific prompt
    prompt_text = service.get_prompt("AIDER_API", "BASE_RULES")
    if prompt_text:
        print(f"Found prompt: {prompt_text}")
    else:
        print("Prompt not found")
    
    # Example: Get all prompts from a group
    all_prompts = service.get_all_prompts("AIDER_API")
    print(f"All prompts: {all_prompts}")
    
    # Example: List available keys
    keys = service.list_available_keys("AIDER_API")
    print(f"Available keys: {keys}")
    
    # Example using convenience function
    prompt_text = get_prompt("AIDER_API", "TEST")
    print(f"Prompt via convenience function: {prompt_text}")
