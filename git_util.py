import os
import subprocess
import tempfile

def clone_repo_using_ssh_key(repo_url: str, deploy_key: str, clone_dir: str = "./cloned_repo", branch: str | None = None):
    """Clone a private Git repository using a deploy key without relying on any existing SSH keys."""
    with tempfile.TemporaryDirectory() as tmpdir:
        key_path = os.path.join(tmpdir, "id_rsa")

        # Write the deploy key to a temporary file
        with open(key_path, "w") as f:
            f.write(deploy_key)
        os.chmod(key_path, 0o600)

        # Use GIT_SSH_COMMAND to ensure ONLY this key is used, ignoring SSH agent or default keys
        env = os.environ.copy()
        env["GIT_SSH_COMMAND"] = (
            f"ssh -i {key_path} -o IdentitiesOnly=yes -o StrictHostKeyChecking=no"
        )

        # Build git clone command
        cmd = ["git", "clone", "--single-branch"]
        if branch:
            cmd += ["--branch", branch]
        cmd += [repo_url, clone_dir]

        # Run git clone
        subprocess.run(cmd, check=True, env=env)

    print(f"✅ Repository cloned to: {clone_dir}")
    if branch:
        print(f"🌿 Checked out branch: {branch}")


def pull_latest_changes_using_ssh_key(repo_dir: str, deploy_key: str, branch: str | None = None):
    """
    Pull the latest changes from a Git repository directory using the deploy key,
    without relying on any existing SSH keys or agents.
    """
    if not os.path.isdir(os.path.join(repo_dir, ".git")):
        raise FileNotFoundError(f"{repo_dir} is not a valid Git repository.")

    with tempfile.TemporaryDirectory() as tmpdir:
        key_path = os.path.join(tmpdir, "id_rsa")

        # Write the deploy key to a temporary file
        with open(key_path, "w") as f:
            f.write(deploy_key)
        os.chmod(key_path, 0o600)

        # Use GIT_SSH_COMMAND to ensure ONLY this key is used
        env = os.environ.copy()
        env["GIT_SSH_COMMAND"] = (
            f"ssh -i {key_path} -o IdentitiesOnly=yes -o StrictHostKeyChecking=no"
        )

        # Fetch and pull the latest changes
        subprocess.run(["git", "-C", repo_dir, "fetch", "--all"], check=True, env=env)
        if branch:
            subprocess.run(["git", "-C", repo_dir, "pull", "origin", branch], check=True, env=env)
        else:
            subprocess.run(["git", "-C", repo_dir, "pull"], check=True, env=env)

    print(f"🔄 Pulled latest changes in: {repo_dir}")
    if branch:
        print(f"🌿 Updated branch: {branch}")


def list_branches_using_ssh_key(repo_url: str, deploy_key: str) -> list[str]:
    """
    List all remote branches of a Git repository using the deploy key,
    without relying on any existing SSH keys or agents.

    Args:
        repo_url: SSH URL of the Git repository (e.g., git@github.com:user/repo.git)
        deploy_key: The private SSH key as a string

    Returns:
        List of branch names (strings)
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        key_path = os.path.join(tmpdir, "id_rsa")

        # Write deploy key
        with open(key_path, "w") as f:
            f.write(deploy_key)
        os.chmod(key_path, 0o600)

        # Set SSH command
        env = os.environ.copy()
        env["GIT_SSH_COMMAND"] = (
            f"ssh -i {key_path} -o IdentitiesOnly=yes -o StrictHostKeyChecking=no"
        )

        # List remote branches directly
        result = subprocess.run(
            ["git", "ls-remote", "--heads", repo_url],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )

        branches = [
            line.split("\t")[1].replace("refs/heads/", "")
            for line in result.stdout.strip().splitlines()
            if line
        ]
        return branches


from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import os

def generate_ssh_keypair(save_dir: str | None = None):
    """
    Generate a new Ed25519 SSH key pair.

    Args:
        save_dir (str | None): Directory to save 'id_ed25519' and 'id_ed25519.pub'.
                               If None, keys are returned as strings.

    Returns:
        dict: {"private_key": str, "public_key": str}
    """
    # Generate private key
    private_key = ed25519.Ed25519PrivateKey.generate()

    # Serialize private key to OpenSSH format
    private_key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # Generate public key
    public_key = private_key.public_key()
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    )

    private_key_str = private_key_bytes.decode("utf-8")
    public_key_str = public_key_bytes.decode("utf-8")

    # Optionally save to disk
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        priv_path = os.path.join(save_dir, "id_ed25519")
        pub_path = os.path.join(save_dir, "id_ed25519.pub")

        with open(priv_path, "w") as f:
            f.write(private_key_str)
        os.chmod(priv_path, 0o600)

        with open(pub_path, "w") as f:
            f.write(public_key_str + "\n")

        print(f"🔐 Keys saved to:\n  {priv_path}\n  {pub_path}")

    return {"private_key": private_key_str, "public_key": public_key_str}
