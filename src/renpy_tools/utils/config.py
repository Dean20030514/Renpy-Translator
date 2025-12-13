"""
Configuration management system for Renpy汉化工具.
Inspired by MTool's fakeLocalStorage.json pattern.
"""

import json
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class TranslationConfig:
    """Translation configuration settings."""
    
    # Ollama settings
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"
    ollama_timeout: int = 300
    
    # Processing settings
    workers: int = 8
    chunk_size: int = 100
    max_tokens: int = 4000
    
    # Quality settings
    skip_has_zh: bool = True
    ignore_ui_punct: bool = True
    require_ph_count_eq: bool = True
    require_newline_eq: bool = True
    
    # GPU settings
    enable_cuda: bool = True
    cuda_visible_devices: str = "0"
    
    # UI settings
    language: str = "zh_CN"
    theme: str = "default"
    auto_save: bool = True
    
    # Recent projects
    last_project_root: Optional[str] = None
    recent_projects: list[str] = None
    
    def __post_init__(self):
        if self.recent_projects is None:
            self.recent_projects = []


class ConfigManager:
    """Manage application configuration with automatic save/load."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize config manager.
        
        Args:
            config_path: Path to config file. Defaults to workspace_root/config.json
        """
        if config_path is None:
            workspace_root = Path(__file__).parent.parent.parent.parent
            self.config_path = workspace_root / "config.json"
        else:
            self.config_path = Path(config_path)
        
        self.config = self.load()
    
    def load(self) -> TranslationConfig:
        """Load configuration from file."""
        if not self.config_path.exists():
            return TranslationConfig()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert dict to dataclass
            return TranslationConfig(**data)
        except Exception as e:
            print(f"⚠️  Failed to load config: {e}, using defaults")
            return TranslationConfig()
    
    def save(self) -> bool:
        """Save configuration to file."""
        try:
            # Convert dataclass to dict
            data = asdict(self.config)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"❌ Failed to save config: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return getattr(self.config, key, default)
    
    def set(self, key: str, value: Any, auto_save: bool = True) -> bool:
        """Set configuration value."""
        if not hasattr(self.config, key):
            print(f"⚠️  Unknown config key: {key}")
            return False
        
        setattr(self.config, key, value)
        
        if auto_save:
            return self.save()
        
        return True
    
    def add_recent_project(self, project_path: str, max_recent: int = 10) -> bool:
        """Add project to recent list."""
        # Remove if already exists
        if project_path in self.config.recent_projects:
            self.config.recent_projects.remove(project_path)
        
        # Add to front
        self.config.recent_projects.insert(0, project_path)
        
        # Keep only max_recent items
        self.config.recent_projects = self.config.recent_projects[:max_recent]
        
        # Update last project
        self.config.last_project_root = project_path
        
        return self.save()
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to default values."""
        self.config = TranslationConfig()
        return self.save()


# Global config instance
_config_manager: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get global config manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


if __name__ == "__main__":
    # Test config management
    config = get_config()
    
    print("Current config:")
    print(f"  Ollama model: {config.get('ollama_model')}")
    print(f"  Workers: {config.get('workers')}")
    print(f"  CUDA enabled: {config.get('enable_cuda')}")
    
    # Test setting values
    config.set('ollama_model', 'qwen2.5-abliterate:7b')
    config.set('workers', 16)
    
    # Test recent projects
    config.add_recent_project("E:\\Games\\TheTyrant")
    config.add_recent_project("E:\\Games\\AnotherGame")
    
    print("\nUpdated config:")
    print(f"  Ollama model: {config.get('ollama_model')}")
    print(f"  Workers: {config.get('workers')}")
    print(f"  Recent projects: {config.config.recent_projects}")
    
    print(f"\n✅ Config saved to: {config.config_path}")
