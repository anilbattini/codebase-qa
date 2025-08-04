import os
from rag_manager import RagManager
from config import ProjectConfig

# Test the rebuild logic
rag_manager = RagManager()
project_dir = ".."
project_type = "android"
force_rebuild = False

print(f"Testing rebuild logic for:")
print(f"  Project dir: {project_dir}")
print(f"  Project type: {project_type}")
print(f"  Force rebuild: {force_rebuild}")

# Check if SQLite database exists
project_config = ProjectConfig(project_type=project_type, project_dir=project_dir)
db_dir = project_config.get_db_dir()
chroma_db_path = os.path.join(db_dir, "chroma.sqlite3")
print(f"  SQLite DB exists: {os.path.exists(chroma_db_path)}")

# Check if git tracking file exists
git_tracking_file = os.path.join(db_dir, "git_tracking.json")
print(f"  Git tracking exists: {os.path.exists(git_tracking_file)}")

# Test the should_rebuild_index method
should_rebuild = rag_manager.should_rebuild_index(project_dir, force_rebuild, project_type)
print(f"  Should rebuild: {should_rebuild}") 