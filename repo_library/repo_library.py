# Copyright 2025 RDK Management
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from pathlib import Path
import shutil
import subprocess

from git import Repo

logger = logging.getLogger(__name__)

class RepoLibrary:
    """Helper functions for googles git-repo tool."""
    @staticmethod
    def init(
            uri: str | None = None,
            branch: str | None = None,
            directory: str | Path = Path.cwd(),
            manifest: str | None = None,
            mirror: bool = False,
            reference: str | Path | None = None,
            archive: bool = False,
            groups: str | None = None,
            repo_url: str | None = None,
            repo_rev: str | None = None,
            no_repo_verify: bool = False,
            verify: bool = False,
            quiet: bool = False
        ):
        """
        Installs git-repo in a chosen directory or the current working directory.

        This function runs the `repo init` command with various options to configure
        the repository. This will create a .repo folder with the git-repo source code
        and manifest files.

        Args:
            uri (str): The URL of the remote repository containing the manifest.
            branch (str): The branch of the repository to initialize.
                Defaults to None.
            directory (str | Path): The directory where the repository
                should be initialized. Defaults to current working directory.
            manifest (str): The name of the manifest file to use.
                Defaults to None.
            mirror (bool): If True, initializes the repository as a mirror.
                Defaults to False.
            reference (str | Path): The location of the mirror directory.
            archive (bool): If True, enables archive mode, storing working files
                in compressed format. Defaults to False.
            groups (str): A comma-separated list of groups to filter which projects
                are initialized. Defaults to None.
            repo_url (str): The URL of the Git repository to use for `repo init`.
                Defaults to None.
            no_repo_verify (bool): If True, disables verification of the remote
                repository. Defaults to False.
            verify (bool): If True, run hooks without asking user for verification.
                Defaults to False.
            quiet (bool): Run quietly. Defaults to False.

        Raises:
            subprocess.CalledProcessError: If the `repo init` command fails.
        """
        directory = Path(directory)

        cmd = ['repo', 'init']
        if uri:
            cmd.extend(['-u', uri])
        if branch:
            cmd.extend(['-b', branch])
        if manifest:
            cmd.extend(['-m', manifest])
        if mirror:
            cmd.append('--mirror')
        if reference:
            cmd.append(f'--reference={reference}')
        if archive:
            cmd.append('--archive')
        if groups:
            cmd.append(f'-g {groups}')
        if repo_url:
            cmd.append(f'--repo-url={repo_url}')
        if repo_rev:
            cmd.append(f'--repo-rev={repo_rev}')
        if no_repo_verify:
            cmd.append('--no-repo-verify')
        if verify:
            cmd.append('--verify')
        if quiet:
            cmd.append('-q')

        logger.info(f'In {str(directory)}: {" ".join(cmd)}')
        try:
            subprocess.run(cmd, cwd=directory, check=True)
        except subprocess.CalledProcessError:
            #Clean up .repo dir on failure
            repo_dir = directory / '.repo'
            if repo_dir.exists() and repo_dir.is_dir():
                shutil.rmtree(repo_dir)
            raise

    @staticmethod
    def sync(
            directory: str | Path = Path.cwd(),
            force_sync: bool = False,
            force_checkout: bool = False,
            jobs: int | None = None,
            current_branch: bool = False,
            detach: bool = False,
            no_prune: bool = False,
            verify: bool = False
        ):
        """Synchronize all repositories in a repo project.

        Args:
            directory (str): Directory to run the repo sync command in. Defaults to
                the current working directory.
            force_sync (bool): Overwrite git directory even if the remote has changed
                in the manifest. Defaults to False.
            force_checkout (bool): Force checkout even if it results in throwing away
                uncommited modifications. Defaults to False.
            jobs (int): How many tasks can be executed simultaneously. Defaults to None.
            current_branch (bool): Fetch only the branch given in the manifest. Defaults
                to False.
            detach (bool): Remove any project not listed in the manifest. Defaults to
                False.
            no-prune (bool): Don't delete references to objects that don't exist on
                the remote. Defaults to False.
            verify (bool): Run post-sync hooks without prompting. Not natively supported.
                Defaults to false.
        """
        cmd = ['repo', 'sync']
        if force_sync:
            cmd.append('--force-sync')
        if force_checkout:
            cmd.append('--force-checkout')
        if jobs:
           cmd.append(f'-j{jobs}')
        if current_branch:
            cmd.append('-c')
        if detach:
            cmd.append('-d')
        if no_prune:
            cmd.append('--no-prune')
        if verify:
            cmd.append('--verify')

        logger.info(f'In {str(directory)}: {" ".join(cmd)}')
        subprocess.run(cmd, cwd=directory, check=True)

    @staticmethod
    def forall(command: str, directory: str | Path = Path.cwd()):
        """Run a shell command in all repositories in your manifest.

        Args:
            command (str): The shell command to run.
            directory (str | Path | None): Directory to run the repo forall command
                should be in a repo folder. Defaults to current dir.
        """
        cmd = ['repo', 'forall', '-c'].extend(command.split(" "))

        logger.info(f'In {str(directory)}: {" ".join(cmd)}')
        subprocess.run(cmd, cwd=directory, check=True)

    @staticmethod
    def get_repo_root_dir(
            directory: str | Path = Path.cwd()
        ) -> Path | None:
        """Returns the first .repo found in directories above.

        Args:
            directory: The directory to search upward from. Defaults to
                current working directory.
        """
        path = Path(directory).resolve()
        while path != path.parent:
            candidate = path / '.repo'
            if candidate.is_dir():
                return candidate
            path = path.parent
        return None

    @staticmethod
    def get_manifest_branch(directory: Path | str) -> str:
        """Get the current manifest branch.

        Repo renames the manifest branch to default after using repo init, however
        sc commands can change this to a normal branch name so we need a different
        way of dealing with this whether branch is called default or not.

        Args:
            directory (Path | str): A directory inside a repo project.

        Returns:
            str: The current manifest branch.
        """
        repo_root = RepoLibrary.get_repo_root_dir(directory)
        if repo_root == None:
            raise RuntimeError("Tried to get manifest branch but not in a repo project!")
        manifests_repo = Repo(repo_root / 'manifests')
        if manifests_repo.active_branch.name != "default":
            return manifests_repo.active_branch.name
        else:
            # Should return refs/heads/<branch>
            ref = manifests_repo.git.config('branch.default.merge')
            return ref.removeprefix('refs/heads/')


    @staticmethod
    def status(directory: Path | str):
        """Show the working tree status."""
        subprocess.run(
            ["repo","status"],
            cwd = directory,
            text = True,
        )
