import os
import hashlib
import json
import subprocess
from logger import log_highlight, log_to_sublog
from config.config import ProjectConfig

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
                log_to_sublog(self.project_dir, "file_tracking.log", "No previous commit record found - processing all files for fresh build")
                # Get all tracked files that match extensions, respecting .gitignore
                all_files = subprocess.check_output(
                    ["git", "ls-files"],
                    cwd=self.project_dir,
                    encoding="utf-8"
                ).splitlines()
                
                # Filter by extensions and respect hierarchical .gitignore
                result = []
                for file_path in all_files:
                    if file_path.endswith(tuple(extensions)):
                        abs_path = os.path.join(self.project_dir, file_path)
                        if os.path.isfile(abs_path) and not self._should_ignore_file(abs_path):
                            result.append(abs_path)
                        else:
                            log_to_sublog(self.project_dir, "file_tracking.log", f"Skipping gitignored file: {file_path}")
                
                log_to_sublog(self.project_dir, "file_tracking.log",
                              f"Git-detected all files (fresh build): {len(result)} files")
                return result
            
            if last_commit == current_commit:
                log_to_sublog(self.project_dir, "file_tracking.log", "No files changed since last indexing (git).")
                return []
            
            # Get files that have changed between the last processed commit and current commit
            changed_files = []
            
            try:
                # Get files changed between commits
                commit_changed_files = subprocess.check_output(
                    ["git", "diff", "--name-only", f"{last_commit}..{current_commit}"],
                    cwd=self.project_dir,
                    encoding="utf-8"
                ).splitlines()
                
                log_to_sublog(self.project_dir, "file_tracking.log", f"Git diff command: git diff --name-only {last_commit}..{current_commit}")
                log_to_sublog(self.project_dir, "file_tracking.log", f"Raw git diff output: {commit_changed_files}")
                
                # Convert to absolute paths and filter by extensions
                for file_path in commit_changed_files:
                    if file_path.endswith(tuple(extensions)):
                        abs_path = os.path.join(self.project_dir, file_path)
                        if os.path.isfile(abs_path) and not self._should_ignore_file(abs_path):
                            changed_files.append(abs_path)
                
                log_to_sublog(self.project_dir, "file_tracking.log",
                              f"Git commit diff detected {len(changed_files)} changed files between {last_commit[:8]} and {current_commit[:8]}")
                
            except subprocess.CalledProcessError as e:
                log_to_sublog(self.project_dir, "file_tracking.log",
                              f"Failed to get commit diff: {e}, falling back to working directory changes")
                # Fallback to working directory changes if commit diff fails
                pass
            
            # Also check for untracked and modified files in working directory
            try:
                working_dir_changed = subprocess.check_output(
                    ["git", "ls-files", "--others", "--modified", "--exclude-standard"],
                    cwd=self.project_dir,
                    encoding="utf-8"
                ).splitlines()
                
                log_to_sublog(self.project_dir, "file_tracking.log", f"Working directory changes: {working_dir_changed}")
                
                for file_path in working_dir_changed:
                    if file_path.endswith(tuple(extensions)):
                        abs_path = os.path.join(self.project_dir, file_path)
                        if os.path.isfile(abs_path) and not self._should_ignore_file(abs_path):
                            if abs_path not in changed_files:  # Avoid duplicates
                                changed_files.append(abs_path)
                
                log_to_sublog(self.project_dir, "file_tracking.log",
                              f"Git working directory changes detected {len(working_dir_changed)} files")
                
            except subprocess.CalledProcessError as e:
                log_to_sublog(self.project_dir, "file_tracking.log",
                              f"Failed to get working directory changes: {e}")
            
            # Log total changed files
            log_to_sublog(self.project_dir, "file_tracking.log",
                          f"Total Git-detected changed files: {len(changed_files)} files")
            return changed_files
        except Exception as e:
            log_to_sublog(self.project_dir, "file_tracking.log",
                          f"[WARN] Git tracking failed: {e}; falling back to content-hash.")
            return self._get_content_hash_changed_files(extensions)

# --------------- CODE CHANGE SUMMARY ---------------
# FIXED
# - Log path resolution: Changed all log_to_sublog calls from self.project_config.get_logs_dir() to self.project_dir
# - Centralized logging: All logs now use the centralized logger path resolution to prevent scattered log files
# - File tracking logs: file_tracking.log now created in the correct project-specific logs directory
# - Hierarchical .gitignore support: Each .gitignore file now applies only to its directory and subdirectories
# - Always ignore codebase-qa tool directories: Added automatic filtering of tool directories
# - Improved pattern matching: Fixed **/build, /build, and other complex gitignore patterns
# - Config ignore patterns integration: Added config ignore patterns to gitignore processing

    def _get_content_hash_changed_files(self, extensions):
        """Fallback: compare file hashes to previous run."""
        old_hashes = self._load_hash_file()
        new_hashes = {}
        changed_files = []
        
        # If no previous hash file exists, process all files (fresh build)
        if not old_hashes:
            log_to_sublog(self.project_dir, "file_tracking.log", "No previous hash file found - processing all files for fresh build")
        
        for root, dirs, files in os.walk(self.project_dir):
            # Skip directories that should be ignored
            dirs[:] = [d for d in dirs if not self._should_ignore_file(os.path.join(root, d))]
            
            for fname in files:
                if fname.endswith(tuple(extensions)):
                    path = os.path.join(root, fname)
                    
                    # Skip files that should be ignored
                    if self._should_ignore_file(path):
                        log_to_sublog(self.project_dir, "file_tracking.log", f"Skipping gitignored file: {os.path.relpath(path, self.project_dir)}")
                        continue
                    
                    try:
                        h = self._file_hash(path)
                        new_hashes[path] = h
                        # If no previous hashes (fresh build) or hash changed, include file
                        if not old_hashes or old_hashes.get(path) != h:
                            changed_files.append(path)
                    except Exception as e:
                        log_to_sublog(self.project_dir, "file_tracking.log", f"Failed to hash {path}: {e}")
        # Log absolute paths for debugging (logs are system-specific)
                    log_to_sublog(self.project_dir, "file_tracking.log",
                      f"Content-hash changed files: {len(changed_files)} files")
        return changed_files
    
    def _get_gitignore_patterns(self):
        """Get gitignore patterns from all .gitignore files in the project and config ignore patterns."""
        patterns = []
        
        # Find all .gitignore files in the project
        gitignore_files = []
        for root, dirs, files in os.walk(self.project_dir):
            if '.gitignore' in files:
                gitignore_files.append(os.path.join(root, '.gitignore'))
        
        # Also check the root .gitignore
        root_gitignore = os.path.join(self.project_dir, ".gitignore")
        if os.path.exists(root_gitignore) and root_gitignore not in gitignore_files:
            gitignore_files.append(root_gitignore)
        
        for gitignore_path in gitignore_files:
            try:
                with open(gitignore_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            patterns.append(line)
            except Exception as e:
                log_to_sublog(self.project_dir, "file_tracking.log", f"Failed to read {gitignore_path}: {e}")
        
        # Add config ignore patterns
        config_ignore_patterns = self.project_config.get_ignore_patterns()
        patterns.extend(config_ignore_patterns)
        
        # Always ignore codebase-qa tool directories
        patterns.extend([
            "codebase-qa",
            "codebase-qa_*",
            "**/codebase-qa",
            "**/codebase-qa_*"
        ])
        
        return patterns
    
    def _matches_gitignore_patterns(self, path, patterns):
        """Check if path matches any gitignore pattern using proper gitignore logic."""
        import fnmatch
        import re
        
        # Convert to relative path from project root
        rel_path = os.path.relpath(path, self.project_dir)
        
        for pattern in patterns:
            # Skip empty patterns
            if not pattern:
                continue
                
            # Handle different pattern types
            if pattern.startswith('/'):
                # Absolute pattern from root
                if rel_path == pattern[1:]:
                    return True
            elif pattern.endswith('/'):
                # Directory pattern
                dir_pattern = pattern[:-1]
                if rel_path.startswith(dir_pattern + '/') or rel_path == dir_pattern:
                    return True
            elif pattern.startswith('**/'):
                # Recursive pattern
                suffix = pattern[3:]
                if rel_path.endswith(suffix) or rel_path.endswith('/' + suffix):
                    return True
                # Also check if any part of the path matches the suffix
                path_parts = rel_path.split('/')
                for part in path_parts:
                    if fnmatch.fnmatch(part, suffix):
                        return True
            elif '**' in pattern:
                # Complex recursive pattern
                parts = pattern.split('**')
                if len(parts) == 2:
                    prefix, suffix = parts
                    if rel_path.startswith(prefix) and rel_path.endswith(suffix):
                        return True
            else:
                # Simple pattern
                if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(os.path.basename(path), pattern):
                    return True
                
                # Handle directory matching for patterns like "build", ".gradle"
                if '/' not in pattern and os.path.isdir(path):
                    if fnmatch.fnmatch(os.path.basename(path), pattern):
                        return True
        
        return False

    def _should_ignore_file(self, file_path):
        """Check if a file should be ignored based on hierarchical .gitignore rules."""
        import fnmatch
        
        # Convert to relative path from project root
        rel_path = os.path.relpath(file_path, self.project_dir)
        
        # Always ignore codebase-qa tool directories
        if 'codebase-qa' in rel_path:
            return True
        
        # Check hierarchical .gitignore files
        current_dir = os.path.dirname(file_path)
        while current_dir != self.project_dir and current_dir.startswith(self.project_dir):
            gitignore_path = os.path.join(current_dir, '.gitignore')
            if os.path.exists(gitignore_path):
                if self._matches_local_gitignore(file_path, gitignore_path):
                    return True
            current_dir = os.path.dirname(current_dir)
        
        # Check root .gitignore
        root_gitignore = os.path.join(self.project_dir, '.gitignore')
        if os.path.exists(root_gitignore):
            if self._matches_local_gitignore(file_path, root_gitignore):
                return True
        
        # Check config ignore patterns
        config_patterns = self.project_config.get_ignore_patterns()
        for pattern in config_patterns:
            if self._matches_pattern(rel_path, pattern):
                return True
        
        return False
    
    def _matches_local_gitignore(self, file_path, gitignore_path):
        """Check if file matches patterns in a specific .gitignore file."""
        try:
            with open(gitignore_path, 'r') as f:
                patterns = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            # Get relative path from the directory containing this .gitignore
            gitignore_dir = os.path.dirname(gitignore_path)
            rel_path = os.path.relpath(file_path, gitignore_dir)
            
            for pattern in patterns:
                if self._matches_pattern(rel_path, pattern):
                    return True
        except Exception:
            pass
        return False
    
    def _matches_pattern(self, rel_path, pattern):
        """Check if a relative path matches a gitignore pattern."""
        import fnmatch
        
        if not pattern:
            return False
        
        # Handle different pattern types
        if pattern.startswith('/'):
            # Absolute pattern from root
            if rel_path == pattern[1:]:
                return True
            # Also check if path starts with the pattern
            if rel_path.startswith(pattern[1:] + '/'):
                return True
            return False
        elif pattern.endswith('/'):
            # Directory pattern
            dir_pattern = pattern[:-1]
            return rel_path.startswith(dir_pattern + '/') or rel_path == dir_pattern
        elif pattern.startswith('**/'):
            # Recursive pattern
            suffix = pattern[3:]
            if rel_path.endswith(suffix) or rel_path.endswith('/' + suffix):
                return True
            # Check if any part of the path contains the suffix
            if '/' + suffix + '/' in rel_path or rel_path.startswith(suffix + '/'):
                return True
            # Also check if any part of the path matches the suffix
            path_parts = rel_path.split('/')
            for part in path_parts:
                if fnmatch.fnmatch(part, suffix):
                    return True
            return False
        elif '**' in pattern:
            # Complex recursive pattern
            parts = pattern.split('**')
            if len(parts) == 2:
                prefix, suffix = parts
                return rel_path.startswith(prefix) and rel_path.endswith(suffix)
        else:
            # Simple pattern
            return fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(os.path.basename(rel_path), pattern)
        
        return False

    def update_tracking_info(self, files_processed):
        """Update hash/cache after indexing."""
        method = self._detect_tracking_method()
        if method == "git":
            self._update_git_tracking(files_processed)
        else:
            self._update_custom_tracking(files_processed)
        log_to_sublog(self.project_dir, "file_tracking.log",
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
        
        # Save current commit for future comparison
        self._save_current_git_commit()
    
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
        """Save current git commit for future comparison."""
        current_commit = self._get_current_git_commit()
        if current_commit:
            with open(self.git_commit_file, "w") as f:
                json.dump({"commit": current_commit}, f, indent=2)

