# git_hash_tracker.py

import os
import subprocess
import hashlib
import json
import time
from typing import Dict, List, Optional, Tuple

class FileHashTracker:
    """Universal file tracking system with Git integration and fallback hashing."""
    
    def __init__(self, project_dir: str, metadata_dir: str):
        self.project_dir = project_dir
        self.metadata_dir = metadata_dir
        self.git_metadata_file = os.path.join(metadata_dir, "git_tracking.json")
        self.custom_metadata_file = os.path.join(metadata_dir, "file_hashes.json")
        self.is_git_repo = self._check_git_repo()
        
    def _check_git_repo(self) -> bool:
        """Check if the project directory is a Git repository."""
        git_dir = os.path.join(self.project_dir, '.git')
        return os.path.exists(git_dir) and self._git_command_available()
    
    def _git_command_available(self) -> bool:
        """Check if Git command is available."""
        try:
            subprocess.run(['git', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _run_git_command(self, args: List[str]) -> Optional[str]:
        """Run a Git command and return output."""
        try:
            result = subprocess.run(
                ['git'] + args,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
    
    def _compute_file_hash(self, filepath: str) -> Optional[str]:
        """Compute SHA-256 hash of file content."""
        try:
            with open(filepath, "rb") as f:
                content = f.read()
                return hashlib.sha256(content).hexdigest()
        except (IOError, OSError):
            return None
    
    def _get_git_file_hashes(self) -> Dict[str, str]:
        """Get Git blob SHA for each tracked file."""
        if not self.is_git_repo:
            return {}
        
        output = self._run_git_command(['ls-files', '-s'])
        if not output:
            return {}
        
        file_hashes = {}
        for line in output.split('\n'):
            if line.strip():
                # Format: <mode> <object> <stage> <file>
                parts = line.split('\t')
                if len(parts) == 2:
                    mode_info = parts[0].split()
                    if len(mode_info) >= 2:
                        blob_sha = mode_info[1]
                        rel_path = parts[1]
                        abs_path = os.path.join(self.project_dir, rel_path)
                        if os.path.exists(abs_path):
                            file_hashes[abs_path] = blob_sha
        
        return file_hashes
    
    def _get_current_commit(self) -> Optional[str]:
        """Get current Git commit SHA."""
        if not self.is_git_repo:
            return None
        return self._run_git_command(['rev-parse', 'HEAD'])
    
    def _get_git_tracked_files(self, extensions: Tuple[str, ...]) -> List[str]:
        """Get list of Git-tracked files with specified extensions."""
        if not self.is_git_repo:
            return []
        
        output = self._run_git_command(['ls-files'])
        if not output:
            return []
        
        tracked_files = []
        for line in output.split('\n'):
            if line.strip() and line.endswith(extensions):
                abs_path = os.path.join(self.project_dir, line.strip())
                if os.path.exists(abs_path):
                    tracked_files.append(abs_path)
        
        return tracked_files
    
    def _get_all_files_fallback(self, extensions: Tuple[str, ...]) -> List[str]:
        """Fallback file discovery using os.walk with .gitignore support."""
        from pathspec import PathSpec
        
        # Load .gitignore if exists
        ignore_spec = None
        gitignore_path = os.path.join(self.project_dir, ".gitignore")
        if os.path.exists(gitignore_path):
            try:
                with open(gitignore_path, 'r') as f:
                    ignore_spec = PathSpec.from_lines("gitwildmatch", f.readlines())
            except Exception:
                pass
        
        valid_files = []
        for root, _, files in os.walk(self.project_dir):
            for file in files:
                if file.endswith(extensions):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.project_dir)
                    
                    # Skip if matches .gitignore patterns
                    if ignore_spec and ignore_spec.match_file(rel_path):
                        continue
                    
                    valid_files.append(full_path)
        
        return valid_files
    
    def get_all_trackable_files(self, extensions: Tuple[str, ...]) -> List[str]:
        """Get all files that can be tracked, using Git or filesystem discovery."""
        if self.is_git_repo:
            return self._get_git_tracked_files(extensions)
        else:
            return self._get_all_files_fallback(extensions)
    
    def get_changed_files(self, extensions: Tuple[str, ...]) -> List[str]:
        """Get list of files that have changed since last tracking."""
        all_files = self.get_all_trackable_files(extensions)
        
        if self.is_git_repo:
            return self._get_changed_files_git(all_files)
        else:
            return self._get_changed_files_custom(all_files)
    
    def _get_changed_files_git(self, all_files: List[str]) -> List[str]:
        """Get changed files using Git tracking."""
        # Load existing Git metadata
        git_metadata = {}
        if os.path.exists(self.git_metadata_file):
            try:
                with open(self.git_metadata_file, 'r') as f:
                    git_metadata = json.load(f)
            except Exception:
                pass
        
        # Get current Git file hashes
        current_hashes = self._get_git_file_hashes()
        
        changed_files = []
        for file_path in all_files:
            current_hash = current_hashes.get(file_path)
            stored_info = git_metadata.get(file_path, {})
            stored_hash = stored_info.get('blob_sha')
            
            if current_hash and (not stored_hash or current_hash != stored_hash):
                changed_files.append(file_path)
        
        return changed_files
    
    def _get_changed_files_custom(self, all_files: List[str]) -> List[str]:
        """Get changed files using custom hashing."""
        # Load existing hash metadata
        hash_metadata = {}
        if os.path.exists(self.custom_metadata_file):
            try:
                with open(self.custom_metadata_file, 'r') as f:
                    hash_metadata = json.load(f)
            except Exception:
                pass
        
        changed_files = []
        for file_path in all_files:
            current_hash = self._compute_file_hash(file_path)
            stored_info = hash_metadata.get(file_path, {})
            stored_hash = stored_info.get('content_hash')
            
            if current_hash and (not stored_hash or current_hash != stored_hash):
                changed_files.append(file_path)
        
        return changed_files
    
    def update_tracking_info(self, processed_files: List[str]):
        """Update tracking information for successfully processed files."""
        os.makedirs(self.metadata_dir, exist_ok=True)
        
        if self.is_git_repo:
            self._update_git_tracking(processed_files)
        else:
            self._update_custom_tracking(processed_files)
    
    def _update_git_tracking(self, processed_files: List[str]):
        """Update Git-based tracking metadata."""
        # Load existing metadata
        metadata = {}
        if os.path.exists(self.git_metadata_file):
            try:
                with open(self.git_metadata_file, 'r') as f:
                    metadata = json.load(f)
            except Exception:
                pass
        
        # Get current Git info
        current_hashes = self._get_git_file_hashes()
        current_commit = self._get_current_commit()
        
        # Update with new information
        for file_path in processed_files:
            if file_path in current_hashes:
                metadata[file_path] = {
                    'blob_sha': current_hashes[file_path],
                    'commit_sha': current_commit,
                    'processed_at': time.time(),
                    'tracking_method': 'git'
                }
        
        # Save updated metadata
        with open(self.git_metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _update_custom_tracking(self, processed_files: List[str]):
        """Update custom hash-based tracking metadata."""
        # Load existing metadata
        metadata = {}
        if os.path.exists(self.custom_metadata_file):
            try:
                with open(self.custom_metadata_file, 'r') as f:
                    metadata = json.load(f)
            except Exception:
                pass
        
        # Update with new hashes
        for file_path in processed_files:
            current_hash = self._compute_file_hash(file_path)
            if current_hash:
                # Get file stats for additional tracking info
                try:
                    stat_info = os.stat(file_path)
                    metadata[file_path] = {
                        'content_hash': current_hash,
                        'size': stat_info.st_size,
                        'modified_time': stat_info.st_mtime,
                        'processed_at': time.time(),
                        'tracking_method': 'custom'
                    }
                except OSError:
                    metadata[file_path] = {
                        'content_hash': current_hash,
                        'processed_at': time.time(),
                        'tracking_method': 'custom'
                    }
        
        # Save updated metadata
        with open(self.custom_metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def get_tracking_status(self) -> Dict[str, any]:
        """Get current tracking status and statistics."""
        status = {
            'tracking_method': 'git' if self.is_git_repo else 'custom',
            'is_git_repo': self.is_git_repo,
            'project_dir': self.project_dir,
        }
        
        if self.is_git_repo:
            status['current_commit'] = self._get_current_commit()
            if os.path.exists(self.git_metadata_file):
                try:
                    with open(self.git_metadata_file, 'r') as f:
                        metadata = json.load(f)
                        status['tracked_files_count'] = len(metadata)
                        status['last_update'] = max([info.get('processed_at', 0) for info in metadata.values()], default=0)
                except Exception:
                    pass
        else:
            if os.path.exists(self.custom_metadata_file):
                try:
                    with open(self.custom_metadata_file, 'r') as f:
                        metadata = json.load(f)
                        status['tracked_files_count'] = len(metadata)
                        status['last_update'] = max([info.get('processed_at', 0) for info in metadata.values()], default=0)
                except Exception:
                    pass
        
        return status
