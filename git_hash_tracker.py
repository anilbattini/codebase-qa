import os
import hashlib
import json
import subprocess
from logger import log_highlight, log_to_sublog
from config import ProjectConfig

class FileHashTracker:
    """
    Tracks changed/new files between RAG runs using either Git commit state or a content-based hash map.
    All logs are project-local via logger.py.
    """

    def __init__(self, project_dir, tracking_dir):
        self.project_dir = os.path.abspath(project_dir)
        self.project_config = ProjectConfig(project_dir=project_dir)
        self.tracking_dir = tracking_dir or self.project_config.get_db_dir()
        self.hash_file = self.project_config.get_hash_file()
        self.git_commit_file = self.project_config.get_git_commit_file()
        self.project_config.create_directories()

    def get_changed_files(self, extensions):
        """Returns list of changed/new files for processing."""
        log_highlight("FileHashTracker.get_changed_files")
        method = self._detect_tracking_method()
        if method == "git":
            changes = self._get_git_changed_files(extensions)
        else:
            changes = self._get_content_hash_changed_files(extensions)
        return changes

    def _detect_tracking_method(self):
        # Prefer git if .git present and accessible, else content-hash
        if os.path.isdir(os.path.join(self.project_dir, ".git")):
            try:
                subprocess.check_output(["git", "status"], cwd=self.project_dir)
                return "git"
            except Exception:
                pass
        return "content-hash"

    def _get_git_changed_files(self, extensions):
        """Get changed and untracked files via Git."""
        try:
            current_commit = self._get_current_git_commit()
            last_commit = self._load_last_commit()
            
            # If no previous commit record exists, process all files (fresh build)
            if not last_commit:
                log_to_sublog(self.project_config.get_logs_dir(), "file_tracking.log", "No previous commit record found - processing all files for fresh build")
                # Get all tracked files that match extensions
                all_files = subprocess.check_output(
                    ["git", "ls-files"],
                    cwd=self.project_dir,
                    encoding="utf-8"
                ).splitlines()
                
                # Filter by extensions and respect .gitignore
                gitignore_patterns = self._get_gitignore_patterns()
                result = []
                for file_path in all_files:
                    if file_path.endswith(tuple(extensions)):
                        abs_path = os.path.join(self.project_dir, file_path)
                        if os.path.isfile(abs_path) and not self._matches_gitignore_patterns(abs_path, gitignore_patterns):
                            result.append(abs_path)
                
                log_to_sublog(self.project_config.get_logs_dir(), "file_tracking.log",
                              f"Git-detected all files (fresh build): {len(result)} files")
                return result
            
            if last_commit == current_commit:
                log_to_sublog(self.project_config.get_logs_dir(), "file_tracking.log", "No files changed since last indexing (git).")
                return []
            
            # List all changed/untracked files
            changed_files = subprocess.check_output(
                ["git", "ls-files", "--others", "--modified", "--exclude-standard"],
                cwd=self.project_dir,
                encoding="utf-8"
            ).splitlines()
            changed_files = [os.path.join(self.project_dir, f) for f in changed_files]
            result = [f for f in changed_files if f.endswith(tuple(extensions)) and os.path.isfile(f)]
            # Log absolute paths for debugging (logs are system-specific)
            log_to_sublog(self.project_config.get_logs_dir(), "file_tracking.log",
                          f"Git-detected changed files: {len(result)} files")
            return result
        except Exception as e:
            log_to_sublog(self.project_config.get_logs_dir(), "file_tracking.log",
                          f"[WARN] Git tracking failed: {e}; falling back to content-hash.")
            return self._get_content_hash_changed_files(extensions)

    def _get_content_hash_changed_files(self, extensions):
        """Fallback: compare file hashes to previous run."""
        old_hashes = self._load_hash_file()
        new_hashes = {}
        changed_files = []
        
        # If no previous hash file exists, process all files (fresh build)
        if not old_hashes:
            log_to_sublog(self.project_config.get_logs_dir(), "file_tracking.log", "No previous hash file found - processing all files for fresh build")
        
        # Get gitignore patterns to respect them
        gitignore_patterns = self._get_gitignore_patterns()
        
        for root, dirs, files in os.walk(self.project_dir):
            # Skip directories that match gitignore patterns
            dirs[:] = [d for d in dirs if not self._matches_gitignore_patterns(os.path.join(root, d), gitignore_patterns)]
            
            for fname in files:
                if fname.endswith(tuple(extensions)):
                    path = os.path.join(root, fname)
                    
                    # Skip files that match gitignore patterns
                    if self._matches_gitignore_patterns(path, gitignore_patterns):
                        continue
                    
                    try:
                        h = self._file_hash(path)
                        new_hashes[path] = h
                        # If no previous hashes (fresh build) or hash changed, include file
                        if not old_hashes or old_hashes.get(path) != h:
                            changed_files.append(path)
                    except Exception as e:
                        log_to_sublog(self.project_config.get_logs_dir(), "file_tracking.log", f"Failed to hash {path}: {e}")
        # Log absolute paths for debugging (logs are system-specific)
        log_to_sublog(self.project_config.get_logs_dir(), "file_tracking.log",
                      f"Content-hash changed files: {len(changed_files)} files")
        return changed_files
    
    def _get_gitignore_patterns(self):
        """Get gitignore patterns from .gitignore file."""
        gitignore_path = os.path.join(self.project_dir, ".gitignore")
        patterns = []
        
        if os.path.exists(gitignore_path):
            try:
                with open(gitignore_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            patterns.append(line)
            except Exception as e:
                log_to_sublog(self.project_config.get_logs_dir(), "file_tracking.log", f"Failed to read .gitignore: {e}")
        
        return patterns
    
    def _matches_gitignore_patterns(self, path, patterns):
        """Check if path matches any gitignore pattern."""
        import fnmatch
        
        # Convert to relative path from project root
        rel_path = os.path.relpath(path, self.project_dir)
        
        for pattern in patterns:
            if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(os.path.basename(path), pattern):
                return True
        
        return False

    def update_tracking_info(self, files_processed):
        """Update hash/cache after indexing."""
        method = self._detect_tracking_method()
        if method == "git":
            self._update_git_tracking(files_processed)
        else:
            self._update_custom_tracking(files_processed)
        log_to_sublog(self.project_config.get_logs_dir(), "file_tracking.log",
                      f"Tracking info updated ({method}) for {len(files_processed)} files.")
    
    def _update_git_tracking(self, processed_files):
        """Update Git-based tracking metadata."""
        import time
        import json
        
        # Load existing metadata
        metadata = {}
        git_tracking_file = os.path.join(self.tracking_dir, "git_tracking.json")
        if os.path.exists(git_tracking_file):
            try:
                with open(git_tracking_file, 'r') as f:
                    metadata = json.load(f)
            except Exception:
                pass
        
        # Get current Git info
        current_commit = self._get_current_git_commit()
        current_hashes = self._get_git_file_hashes()
        
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
        with open(git_tracking_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _update_custom_tracking(self, processed_files):
        """Update custom hash-based tracking metadata."""
        import time
        import json
        
        # Load existing metadata
        metadata = {}
        custom_tracking_file = os.path.join(self.tracking_dir, "file_hashes.json")
        if os.path.exists(custom_tracking_file):
            try:
                with open(custom_tracking_file, 'r') as f:
                    metadata = json.load(f)
            except Exception:
                pass
        
        # Update with new hashes
        for file_path in processed_files:
            current_hash = self._file_hash(file_path)
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
        with open(custom_tracking_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _get_git_file_hashes(self):
        """Get Git blob SHA for each tracked file."""
        if not self._detect_tracking_method() == "git":
            return {}
        
        try:
            output = subprocess.check_output(
                ["git", "ls-files", "-s"],
                cwd=self.project_dir,
                encoding="utf-8"
            )
            
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
        except Exception:
            return {}

    def get_tracking_status(self):
        """Returns current status, either git or content hash mode."""
        method = self._detect_tracking_method()
        status = {"tracking_method": method}
        if method == "git":
            status["current_commit"] = self._get_current_git_commit()
        else:
            status["file_count"] = len(self._load_hash_file())
        return status

    def _file_hash(self, file_path):
        """Return SHA256 for file."""
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()

    def _load_hash_file(self):
        if os.path.isfile(self.hash_file):
            with open(self.hash_file, "r") as f:
                return json.load(f)
        return {}

    def _save_hash_file(self, hashes):
        with open(self.hash_file, "w") as f:
            json.dump(hashes, f, indent=2)

    def _get_current_git_commit(self):
        try:
            commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=self.project_dir,
                encoding="utf-8"
            ).strip()
            return commit
        except Exception:
            return None

    def _load_last_commit(self):
        if os.path.isfile(self.git_commit_file):
            with open(self.git_commit_file, "r") as f:
                d = json.load(f)
                return d.get("commit")
        return None

    def _save_current_git_commit(self):
        commit = self._get_current_git_commit()
        if commit:
            with open(self.git_commit_file, "w") as f:
                json.dump({"commit": commit}, f)

# --------------- CODE CHANGE SUMMARY ---------------
# REMOVED
# - All in-method print statements and ad-hoc logging; now routed exclusively through logger.py for DRY, centralized logging.
# - Old/duplicated fallback logic for file changes, reduced by clearer try/fallback structure.
# ADDED
# - log_highlight/log_to_sublog used for tracking/git/content-hash logs.
# - Unified status/caching logic for both git and non-git contexts.
# - Clean entrypoint for downstream code to query tracking method, changed files, update state.
