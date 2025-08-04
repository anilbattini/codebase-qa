import os
from git_hash_tracker import FileHashTracker
from config import ProjectConfig

# Test git commit saving
project_config = ProjectConfig(project_type='android', project_dir='..')
tracker = FileHashTracker('..', project_config.get_db_dir())

print(f"Git commit file path: {tracker.git_commit_file}")
print(f"Current git commit: {tracker._get_current_git_commit()}")

# Try to save the current commit
tracker._save_current_git_commit()

# Check if file was created
if os.path.exists(tracker.git_commit_file):
    print(f"✅ Git commit file created: {tracker.git_commit_file}")
    with open(tracker.git_commit_file, 'r') as f:
        import json
        data = json.load(f)
        print(f"   Content: {data}")
else:
    print(f"❌ Git commit file not created") 