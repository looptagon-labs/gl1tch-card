from pathlib import Path
import re
import shutil
import tempfile
import os
from git import Repo, Actor
from github import Github


class GithubService:
    def __init__(self, github_token: str):
        self.github_token = github_token
        self.gh = Github(github_token)
        self.user = self.gh.get_user()

    def get_user(self):
        return self.user.login

    def update_readme(self, gif_path: str):
        try:
            if not self.github_token:
                raise ValueError("GitHub token is required")

            source_gif = Path(gif_path).expanduser().resolve()
            if not source_gif.is_file():
                raise FileNotFoundError(f"GIF not found: {source_gif}")

            login = self.user.login
            repo_full_name = f"{login}/{login}"

            repo_url = f"https://{self.github_token}@github.com/{repo_full_name}.git"

            with tempfile.TemporaryDirectory(prefix="readme-gif-") as clone_tmp:
                clone_dir = Path(clone_tmp)

                # Clone repository
                repo = Repo.clone_from(repo_url, to_path=str(clone_dir))

                # Ensure assets directory and copy GIF
                assets_dir = clone_dir / "assets"
                assets_dir.mkdir(parents=True, exist_ok=True)
                target_gif = assets_dir / "gl1tch-card.gif"
                shutil.copy2(str(source_gif), str(target_gif))

                try:
                    readme = self.gh.get_repo(repo_full_name).get_readme()
                    readme_path = os.path.join(clone_dir, readme.path)
                    print(readme_path)
                except Exception as e:
                    print(f"Error getting readme: {e}")
                    exit(1)
                try:
                    with open(readme_path, "r") as f:
                        readme_content = f.read()
                    print(readme_content)
                except Exception as e:
                    print(f"Error getting readme content: {e}")
                    exit(1)

                start_comment = "<!--START_SECTION:gl1tch-card-->"
                end_comment = "<!--END_SECTION:gl1tch-card-->"
                img_md = "![GIF](assets/gl1tch-card.gif)"
                new_section = f"{start_comment}\n{img_md}\n{end_comment}"
                pattern = re.compile(
                    re.escape(start_comment) + r"[\s\S]*?" + re.escape(end_comment),
                    flags=re.MULTILINE,
                )

                if start_comment in readme_content and end_comment in readme_content:
                    new_readme = pattern.sub(new_section, readme_content)
                else:
                    raise ValueError("Gl1tch card section not found in README")

                with open(readme_path, "w") as f:
                    f.write(new_readme)

                repo.git.add(
                    [
                        readme.path,
                        str(target_gif.relative_to(clone_dir)),
                    ]
                )
                if repo.is_dirty(untracked_files=True):
                    actor = Actor(
                        "hello-bot",
                        "41898282+github-actions[bot]@users.noreply.github.com",
                    )
                    repo.index.commit(
                        "docs: update gl1tch card", author=actor, committer=actor
                    )
                    repo.remotes.origin.push()
        except Exception as e:
            print(f"Error updating readme: {e}")
            exit(1)


if __name__ == "__main__":

    github_token = ""
    svc = GithubService(github_token)
    result_path = svc.update_readme("demo.gif")
    print(f"Updated README at: {result_path}")
