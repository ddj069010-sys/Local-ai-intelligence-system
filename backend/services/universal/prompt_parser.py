import re
from typing import List, Tuple
from .doc_registry import doc_registry

class PromptParser:
    @staticmethod
    def extract_refs(text: str) -> Tuple[List[str], bool]:
        """
        Extract document references from text.
        Returns: (list of doc_ids, is_all_docs)
        """
        if "@all_docs" in text:
            return doc_registry.get_all_ids(), True
        
        # Find all @word patterns, avoiding emails by using negative lookbehind
        refs = re.findall(r"(?<!\S)@([a-z0-9_]+)", text.lower())
        doc_ids = []
        for ref in refs:
            doc_id = doc_registry.get_id_by_name(ref)
            if doc_id:
                doc_ids.append(doc_id)
        
        return list(set(doc_ids)), False

    @staticmethod
    def clean_query(text: str) -> str:
        """Remove @ references from the query for cleaner search/reasoning."""
        text = text.replace("@all_docs", "")
        text = re.sub(r"@[a-z0-9]+", "", text)
        return text.strip()

    @staticmethod
    def extract_flags(text: str) -> Tuple[str, dict]:
        """
        Extract configuration flags like --web, --deep, --style=concise from query.
        Returns the cleaned query and a dictionary of extracted flags.
        """
        flags = {}
        # Match boolean flags like --web
        bool_flags = re.findall(r"(?<!\S)--([a-z0-9_-]+)(?!\S|=)", text.lower())
        for flag in bool_flags:
            flags[flag] = True
            
        # Match value flags like --style=concise
        val_flags = re.findall(r"(?<!\S)--([a-z0-9_-]+)=([a-z0-9_.-]+)", text.lower())
        for key, val in val_flags:
            flags[key] = val
            
        # Clean flags from text
        cleaned_text = re.sub(r"(?<!\S)--[a-z0-9_=-]+", "", text, flags=re.IGNORECASE).strip()
        return cleaned_text, flags

    @staticmethod
    def extract_system_commands(text: str) -> Tuple[str, List[str]]:
        """
        Extract slash commands like /clear, /analyze, /search 
        Returns the cleaned query and list of extracted commands.
        """
        commands = re.findall(r"(?<!\S)/([a-z0-9_-]+)", text.lower())
        cleaned_text = re.sub(r"(?<!\S)/[a-z0-9_-]+", "", text, flags=re.IGNORECASE).strip()
        return cleaned_text, commands

    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """Robustly extract all URLs from the text prompt for external processing."""
        return re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*', text)

    @staticmethod
    def extract_hashtags(text: str) -> List[str]:
        """Extract explicit topic hashtags like #machinelearning"""
        return re.findall(r"(?<!\S)#([a-zA-Z0-9_]+)", text)

