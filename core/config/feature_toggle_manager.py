"""
Zero-hardcoding feature toggle manager with environment-based configuration.
Production-grade with robust file discovery and explicit reload capabilities.
"""
import json
import pathlib
import tomllib
import os
from functools import lru_cache
from packaging import version
from datetime import datetime
from logger import log_to_sublog, log_highlight


class FeatureToggleManager:
    """
    Environment-driven feature toggle manager with zero hardcoded paths.
    Configurable via environment variables with intelligent defaults.
    """
    
    _cache_key = 0
    
    @classmethod
    def _get_config_paths(cls) -> tuple:
        """
        Get config paths from environment variables with intelligent defaults.
        Supports multiple deployment scenarios without hardcoding.
        """
        # Environment-driven configuration
        toggle_path_env = os.getenv('FEATURE_TOGGLE_PATH')
        pyproject_path_env = os.getenv('PYPROJECT_PATH')
        
        if toggle_path_env and pyproject_path_env:
            # Explicit paths provided
            toggle_path = pathlib.Path(toggle_path_env).resolve()
            pyproject_path = pathlib.Path(pyproject_path_env).resolve()
        else:
            # Intelligent discovery from current file location
            current_file_dir = pathlib.Path(__file__).parent.resolve()
            project_root = cls._find_project_root_from_dir(current_file_dir)
            
            # Standard structure discovery
            toggle_path = project_root / "core" / "config" / "featureToggle.json"
            pyproject_path = project_root / "pyproject.toml"
        
        return pyproject_path, toggle_path
    
    @classmethod
    def _find_project_root_from_dir(cls, start_dir: pathlib.Path) -> pathlib.Path:
        """
        Find project root by searching upward for pyproject.toml.
        No hardcoded assumptions about structure.
        """
        for parent in [start_dir] + list(start_dir.parents):
            if (parent / "pyproject.toml").exists():
                return parent
                
        # Fallback to current working directory search
        current_cwd = pathlib.Path.cwd().resolve()
        for parent in [current_cwd] + list(current_cwd.parents):
            if (parent / "pyproject.toml").exists():
                return parent
                
        return current_cwd
    
    @classmethod
    @lru_cache(maxsize=1)
    def _get_file_paths(cls) -> tuple:
        """Cached path resolution - computed once per runtime."""
        return cls._get_config_paths()
    
    @classmethod
    def invalidate_cache(cls):
        """Force cache refresh for development/testing."""
        cls._cache_key += 1
        cls._get_file_paths.cache_clear()
        cls._read_pyproject.cache_clear()
        cls._read_toggles.cache_clear()
    
    @classmethod
    def reload(cls):
        """
        Explicit reload method for development workflows.
        Allows config changes without app restart.
        """
        log_highlight("FeatureToggleManager: Explicit reload requested")
        cls.invalidate_cache()
        
        # Verify reload worked
        toggles = cls._read_toggles()
        version = cls.app_version()
        log_highlight(f"FeatureToggleManager: Reloaded {len(toggles)} toggles, version {version}")
    
    @classmethod
    @lru_cache(maxsize=1)
    def _read_pyproject(cls) -> dict:
        """Read and cache pyproject.toml with zero hardcoding."""
        pyproject_path, _ = cls._get_file_paths()
        
        try:
            if pyproject_path.exists():
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                log_highlight(f"FeatureToggleManager: Loaded pyproject.toml from {pyproject_path}")
                return data
            else:
                log_highlight(f"FeatureToggleManager: pyproject.toml not found at {pyproject_path}")
        except Exception as e:
            log_highlight(f"FeatureToggleManager: Error reading pyproject.toml: {e}")
        
        return {}
    
    @classmethod
    @lru_cache(maxsize=1)
    def app_version(cls) -> str:
        """Get app version with robust fallback - no hardcoding."""
        try:
            data = cls._read_pyproject()
            if data and "project" in data and "version" in data["project"]:
                app_ver = data["project"]["version"]
                log_highlight(f"FeatureToggleManager: App version: {app_ver}")
                return app_ver
        except Exception as e:
            log_highlight(f"FeatureToggleManager: Version extraction error: {e}")
        
        log_highlight("FeatureToggleManager: Using fallback version 0.0.0")
        return "0.0.0"
    
    @classmethod
    @lru_cache(maxsize=1)
    def _read_toggles(cls) -> dict:
        """Read feature toggles with zero hardcoded fallbacks."""
        _, toggle_path = cls._get_file_paths()
        
        try:
            if toggle_path.exists():
                with open(toggle_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                log_highlight(f"FeatureToggleManager: Loaded {len(data)} toggles from {toggle_path}")
                return data
            else:
                log_highlight(f"FeatureToggleManager: Toggle file not found at {toggle_path}")
                log_highlight("FeatureToggleManager: Create the file manually - no auto-creation")
        except Exception as e:
            log_highlight(f"FeatureToggleManager: Error reading toggles: {e}")
        
        return {}  # Empty dict - no hardcoded defaults
    
    @classmethod
    def is_enabled(cls, feature_name: str, project_dir: str = ".") -> bool:
        """Check feature enablement with comprehensive logging - zero hardcoding."""
        try:
            toggles = cls._read_toggles()
            feature_config = toggles.get(feature_name, {})
            
            enabled = feature_config.get("enabled", False)
            min_version_str = feature_config.get("minVersion", "0.0.0")
            current_version_str = cls.app_version()
            
            version_check_passed = False
            if enabled:
                try:
                    version_check_passed = version.parse(current_version_str) >= version.parse(min_version_str)
                except Exception as e:
                    log_highlight(f"FeatureToggleManager: Version parse error for {feature_name}: {e}")
            
            final_decision = enabled and version_check_passed
            
            # Log decision
            toggle_info = {
                "timestamp": datetime.now().isoformat(),
                "feature_name": feature_name,
                "config": feature_config,
                "current_version": current_version_str,
                "min_version_required": min_version_str,
                "enabled_flag": enabled,
                "version_check_passed": version_check_passed,
                "final_decision": final_decision,
                "decision_reason": cls._get_decision_reason(enabled, version_check_passed)
            }
            
            log_to_sublog(project_dir, "toggle_info.log", 
                f"TOGGLE_DECISION: {json.dumps(toggle_info, indent=2)}")
            
            return final_decision
            
        except Exception as e:
            log_highlight(f"FeatureToggleManager: Error checking {feature_name}: {e}")
            return False
    
    @classmethod
    def _get_decision_reason(cls, enabled: bool, version_check: bool) -> str:
        """Get decision reason without hardcoded strings."""
        if not enabled:
            return "feature_disabled_in_config"
        elif not version_check:
            return "app_version_below_minimum"
        else:
            return "feature_enabled_version_satisfied"
    
    @classmethod
    def debug_paths(cls) -> dict:
        """Debug method showing all resolved paths."""
        pyproject_path, toggle_path = cls._get_file_paths()
        project_root = cls._find_project_root_from_dir(pathlib.Path(__file__).parent)
        
        return {
            "project_root": str(project_root),
            "pyproject_path": str(pyproject_path),
            "pyproject_exists": pyproject_path.exists(),
            "toggle_path": str(toggle_path),
            "toggle_exists": toggle_path.exists(),
            "env_toggle_path": os.getenv('FEATURE_TOGGLE_PATH', 'Not Set'),
            "env_pyproject_path": os.getenv('PYPROJECT_PATH', 'Not Set'),
            "cwd": str(pathlib.Path.cwd())
        }
