import os
import zipfile
from pathlib import Path

def get_unique_zip_path(base_zip_path: Path) -> Path:
    counter = 1
    zip_path = base_zip_path
    while zip_path.exists():
        zip_path = base_zip_path.with_name(f"{base_zip_path.stem}_{counter}{base_zip_path.suffix}")
        counter += 1
    return zip_path


def zip_github_repo(repo_dir_name: str, exclude_dirs=None):
    if exclude_dirs is None:
        exclude_dirs = ['.venv', 'venv']

    repo_path = Path.cwd() / repo_dir_name
    base_zip_path = Path.cwd() / f"{repo_dir_name}.zip"
    if not repo_path.exists() or not repo_path.is_dir():
        raise FileNotFoundError(f"Repository directory '{repo_dir_name}' does not exist in {Path.cwd()}")
    zip_path = get_unique_zip_path(base_zip_path)

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(repo_path):
            # Exclude specified directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(repo_path)
                zipf.write(file_path, arcname)
    return zip_path


if __name__ == "__main__":
    import argparse
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    parser = argparse.ArgumentParser(description="Zip a GitHub repo by folder name, excluding .venv directory.")
    parser.add_argument("repo_dir_name", help="Name of the GitHub repository folder (in current directory)")
    args = parser.parse_args()
    try:
        zip_file = zip_github_repo(args.repo_dir_name)
        logging.info(f"Repository zipped successfully to {zip_file}")
    except Exception as e:
        logging.error(f"Failed to zip repository: {e}")
        exit(1)