#!/usr/bin/env python3
"""
Bitbucket Commit Analyzer

This script analyzes commits in a Bitbucket branch, focusing on initial and merge commits.
It reports statistics for each commit including author, lines added/removed, and net change.
"""

import argparse
import logging
import sys
import os
import requests
from requests.auth import HTTPBasicAuth
from typing import Dict, List, Tuple, Optional, Any
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bitbucket_analyzer.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("BitbucketAnalyzer")


class BitbucketClient:
    """
    Client for interacting with the Bitbucket on-premise server API.

    This class handles all API communication including authentication and error handling.
    """

    def __init__(self, base_url: str, project: str, repository: str, username: str, password: str):
        """
        Initialize the Bitbucket client.

        Args:
            base_url (str): The base URL of the Bitbucket server, e.g., 'https://bitbucket.example.com'
            project (str): The Bitbucket project key
            repository (str): The repository name
            username (str): Username for Bitbucket authentication
            password (str): Password or token for Bitbucket authentication
        """
        self.base_url = base_url.rstrip('/')
        self.project = project
        self.repository = repository
        self.auth = HTTPBasicAuth(username, password)
        self.api_base = f"{self.base_url}/rest/api/1.0/projects/{project}/repos/{repository}"
        logger.info(f"Initialized BitbucketClient for {project}/{repository}")

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Make an API request to Bitbucket.

        Args:
            endpoint (str): The API endpoint to call
            params (Dict, optional): Query parameters to include in the request

        Returns:
            Dict: The JSON response from the API

        Raises:
            Exception: If the API call fails
        """
        url = f"{self.api_base}{endpoint}"
        logger.debug(f"Making API request to: {url}")

        try:
            response = requests.get(url, auth=self.auth, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise Exception(f"Failed to make API request: {e}")

    def get_file_change(self, current_commit_id: str, previous_commit_id: str, file_path: str) -> dict:
        params = {
            "since": previous_commit_id,
            "until": current_commit_id,
        }

        return self._make_request(f"/diff/{file_path}", params)

    def get_commits(self, branch: str) -> List[Dict]:
        """
        Get all commits in a branch.

        Args:
            branch (str): The branch name

        Returns:
            List[Dict]: List of commit objects
        """
        all_commits = []
        start = 0
        limit = 100
        is_last_page = False

        logger.info(f"Fetching commits for branch: {branch}")

        while not is_last_page:
            params = {
                "until": branch,
                "start": start,
                "limit": limit
            }

            response = self._make_request("/commits", params)

            if "values" in response:
                all_commits.extend(response["values"])

            is_last_page = response.get("isLastPage", True)
            start = response.get("nextPageStart", 0)

            if not is_last_page:
                logger.debug(f"Fetched page of commits, next page starts at: {start}")

        logger.info(f"Retrieved {len(all_commits)} commits from branch: {branch}")
        return all_commits

    def get_commit_changes(self, current_commit_id: str, previous_commit_id: str) -> List[Dict]:
        """
        Get changes between two commits.

        Args:
            current_commit_id (str): The ID of the current commit
            previous_commit_id (str): The ID of the previous commit

        Returns:
            List[Dict]: List of changes between the commits
        """
        all_changes = []
        start = 0
        limit = 1000  # Using the recommended limit from instructions
        is_last_page = False

        logger.info(f"Fetching changes between commits: {previous_commit_id} and {current_commit_id}")

        while not is_last_page:
            params = {
                "since": previous_commit_id,
                "start": start,
                "limit": limit
            }

            endpoint = f"/commits/{current_commit_id}/changes"
            response = self._make_request(endpoint, params)

            if "values" in response:
                all_changes.extend(response["values"])

            is_last_page = response.get("isLastPage", True)
            start = response.get("nextPageStart", 0)

            if not is_last_page:
                logger.debug(f"Fetched page of changes, next page starts at: {start}")

        logger.info(f"Retrieved {len(all_changes)} changes between commits")
        return all_changes




class CommitAnalyzer:
    """
    Analyzes commits and their changes to generate statistics.
    """

    def __init__(self, bitbucket_client: BitbucketClient):
        """
        Initialize the commit analyzer.

        Args:
            bitbucket_client (BitbucketClient): An initialized Bitbucket client
        """
        self.client = bitbucket_client
        logger.info("Initialized CommitAnalyzer")

    def is_merge_commit(self, commit: Dict) -> bool:
        """
        Determine if a commit is a merge commit.

        Args:
            commit (Dict): The commit object

        Returns:
            bool: True if the commit is a merge commit, False otherwise
        """
        # A merge commit typically has more than one parent
        return len(commit.get("parents", [])) > 1

    def is_initial_commit(self, commit: Dict) -> bool:
        """
        Determine if a commit is an initial commit.

        Args:
            commit (Dict): The commit object

        Returns:
            bool: True if the commit is an initial commit, False otherwise
        """
        # An initial commit has no parents
        return len(commit.get("parents", [])) == 0

    def filter_significant_commits(self, commits: List[Dict]) -> List[Dict]:
        """
        Filter commits to only include initial and merge commits.

        Args:
            commits (List[Dict]): List of all commits

        Returns:
            List[Dict]: Filtered list containing only initial and merge commits
        """
        filtered_commits = []

        for commit in commits:
            if self.is_initial_commit(commit) or self.is_merge_commit(commit):
                filtered_commits.append(commit)

        logger.info(f"Filtered {len(filtered_commits)} significant commits from {len(commits)} total commits")
        return filtered_commits

    def should_include_file(self, file_path: str, excluded_extensions: List[str] = None) -> bool:
        """
        Determine if a file should be included in the analysis based on its extension.

        Args:
            file_path (str): The file path
            excluded_extensions (List[str], optional): List of file extensions to exclude

        Returns:
            bool: True if the file should be included, False otherwise
        """
        if not excluded_extensions:
            return True

        # Get the file extension (lowercase)
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        # Check if the extension is in the excluded list
        return ext not in excluded_extensions

    def analyze_commit_changes(self, current_commit: Dict, previous_commit_id: Optional[str] = None,
                               excluded_extensions: List[str] = None) -> Dict:
        """
        Analyze changes between the current commit and a previous commit.

        Args:
            current_commit (Dict): The current commit object
            previous_commit_id (str, optional): The ID of the previous commit.
                                               If None, uses the first parent of the current commit.
            excluded_extensions (List[str], optional): List of file extensions to exclude

        Returns:
            Dict: Analysis results including lines added, removed, and net change
        """
        current_commit_id = current_commit["id"]

        # If previous_commit_id is not provided, use the first parent
        if previous_commit_id is None and not self.is_initial_commit(current_commit):
            previous_commit_id = current_commit["parents"][0]["id"]
            logger.debug(f"Using parent commit {previous_commit_id} as previous commit")

        # Get changes between commits
        changes = self.client.get_commit_changes(current_commit_id, previous_commit_id)

        # Initialize counters
        lines_added = 0
        lines_removed = 0
        files_changed = 0

        # Process each changed file
        for change in changes:
            files_changed += 1

            # Initialize file change info
            file_change_info = {
                "path": change.get("path", "Unknown"),
                "type": change.get("type", "Unknown"),
                "lines_added": 0,
                "lines_removed": 0,
                "net_change": 0,
                "src_executable": change.get("srcExecutable", False),
                "executable": change.get("executable", False)
            }

            # Extract line counts from the change
            if "type" in change:
                data = self.client.get_file_change(previous_commit_id=previous_commit_id,
                                                   current_commit_id=current_commit_id,
                                                   file_path=change["path"]['toString'],)
                for diff in data.get('diffs', []):
                    for hunk in diff.get('hunks', []):
                        for segment in hunk.get('segments', []):
                            if segment.get('type') == 'ADDED':
                                lines_added += len(segment.get('lines', []))
                            elif segment.get('type') == 'REMOVED':
                                lines_removed += len(segment.get('lines', []))

        net_change = lines_added - lines_removed

        logger.info(f"Analyzed commit changes {current_commit_id[:7]}, lines added: {lines_added}, lines removed: {lines_removed}, net change: {net_change}")

        return {
            "analyzed_commit": current_commit_id,
            "author": current_commit.get("author", {}).get("name", "Unknown"),
            "date": current_commit.get("authorTimestamp", 0),
            "files_changed": files_changed,
            "lines_added": lines_added,
            "lines_removed": lines_removed,
            "net_change": net_change
        }



    def analyze_branch(self, branch: str, excluded_extensions: List[str] = None) -> List[Dict]:
        """
        Analyze all significant commits in a branch.

        Args:
            branch (str): The branch name
            excluded_extensions (List[str], optional): List of file extensions to exclude

        Returns:
            List[Dict]: Analysis results for each significant commit
        """
        logger.info(f"Starting analysis of branch: {branch}")

        # Get all commits in the branch
        all_commits = self.client.get_commits(branch)

        if not all_commits:
            logger.warning(f"No commits found in branch: {branch}")
            return []

        # Filter to only include initial and merge commits
        significant_commits = self.filter_significant_commits(all_commits)

        if not significant_commits:
            logger.warning(f"No significant commits found in branch: {branch}")
            return []

        # Analyze each significant commit
        results = []
        previous_commit_id = None

        # Process commits from oldest to newest
        for commit in reversed(significant_commits):
            analysis = self.analyze_commit_changes(commit, previous_commit_id, excluded_extensions)
            results.append(analysis)
            previous_commit_id = commit["id"]

        logger.info(f"Completed analysis of {len(results)} significant commits")
        return results


class Reporter:
    """
    Generates reports based on commit analysis results.
    """

    @staticmethod
    def format_timestamp(timestamp: int) -> str:
        """
        Format a Unix timestamp as a human-readable date.

        Args:
            timestamp (int): Unix timestamp in milliseconds

        Returns:
            str: Formatted date string
        """
        if not timestamp:
            return "Unknown date"

        # Convert milliseconds to seconds
        dt = datetime.fromtimestamp(timestamp / 1000)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def generate_text_report(analysis_results: List[Dict], show_files: bool = True,
                             show_cumulative: bool = False) -> str:
        """
        Generate a text report from commit analysis results.

        Args:
            analysis_results (List[Dict]): List of commit analysis results
            show_files (bool, optional): Whether to show detailed file changes
            show_cumulative (bool, optional): Whether to show cumulative changes

        Returns:
            str: Formatted text report
        """
        if not analysis_results:
            return "No results to report."

        report_lines = ["Bitbucket Commit Analysis Report", "=" * 30, ""]
        if show_cumulative:
            cumulative_data: dict = {}
            for result in analysis_results:
                if result['author'] not in cumulative_data.keys():
                    cumulative_data[result['author']] = {
                        'files_changed': 0,
                        'lines_added': 0,
                        'lines_removed': 0,
                        'net_change': 0,
                    }
                    cumulative_data[result['author']]['files_changed'] += result['files_changed']
                    cumulative_data[result['author']]['lines_added'] += result['lines_added']
                    cumulative_data[result['author']]['lines_removed'] += result['lines_removed']
                    cumulative_data[result['author']]['net_change'] += result['net_change']

            report_lines = cumulative_data
        else:
            for result in analysis_results:
                commit_type = "Initail Commit" if result['is_initial'] else "Merge Commit"
                report_lines.append(f"Commit: {result['analyzed_commit'][:7]} ({commit_type})")
                report_lines.append(f"Author: {result['author']}")
                report_lines.append(f"Date: {Reporter.format_timestamp(result['date'])}")
                report_lines.append(f"Files Changed: {result['files_changed']}")
                report_lines.append(f"Lines Added: {result['lines_added']}")
                report_lines.append(f"Lines Removed: {result['lines_removed']}")
                report_lines.append(f"Net Change: {result['net_change']}")
                report_lines.append("-" * 30)
                report_lines.append("")

            # Add summary
            total_added = sum(r["lines_added"] for r in analysis_results)
            total_removed = sum(r["lines_removed"] for r in analysis_results)
            total_net = sum(r["net_change"] for r in analysis_results)
            report_lines.append(f"Total Files Changed: {sum(r['files_changed'] for r in analysis_results)}")
            report_lines.append(f"Total Lines Added: {total_added}")
            report_lines.append(f"Total Lines Removed: {total_removed}")
            report_lines.append(f"Total Net Change: {total_net}")


        return "\n".join(report_lines)

    @staticmethod
    def generate_json_report(analysis_results: List[Dict], show_cumulative: bool = True) -> str:
        """
        Generate a JSON report from commit analysis results.

        Args:
            analysis_results (List[Dict]): List of commit analysis results
            show_cumulative (bool, optional): Whether to include cumulative changes

        Returns:
            str: JSON formatted report
        """
        if not analysis_results:
            return json.dumps({"error": "No results to report."})

        # Calculate summary
        summary = {
            "total_commits": len(analysis_results),
            "total_files_changed": sum(r["files_changed"] for r in analysis_results),
            "total_lines_added": sum(r["lines_added"] for r in analysis_results),
            "total_lines_removed": sum(r["lines_removed"] for r in analysis_results),
            "total_net_change": sum(r["net_change"] for r in analysis_results)
        }

        # Add cumulative data if requested
        if show_cumulative:
            cumulative_added = 0
            cumulative_removed = 0
            cumulative_net = 0
            cumulative_files = 0

            for result in analysis_results:
                # Update cumulative values
                cumulative_added += result["lines_added"]
                cumulative_removed += result["lines_removed"]
                cumulative_net += result["net_change"]
                cumulative_files += result["files_changed"]

                # Add cumulative data to the result
                result["cumulative_files_changed"] = cumulative_files
                result["cumulative_lines_added"] = cumulative_added
                result["cumulative_lines_removed"] = cumulative_removed
                result["cumulative_net_change"] = cumulative_net

        # Format the results
        report_data = {
            "summary": summary,
            "commits": analysis_results
        }

        return json.dumps(report_data, indent=2)


def main():
    """
    Main entry point for the Bitbucket analyzer script.
    """
    parser = argparse.ArgumentParser(description="Analyze commits in a Bitbucket branch")

    parser.add_argument("--url", required=True, help="Bitbucket server URL")
    parser.add_argument("--project", required=True, help="Bitbucket project key")
    parser.add_argument("--repo", required=True, help="Repository name")
    parser.add_argument("--branch", required=True, help="Branch to analyze")
    parser.add_argument("--username", required=True, help="Bitbucket username")
    parser.add_argument("--password", required=True, help="Bitbucket password or token")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format (text or json)")
    parser.add_argument("--output", help="Output file (if not specified, prints to stdout)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--exclude", nargs="+", help="File extensions to exclude (e.g., .jpg .png)")
    parser.add_argument("--no-files", action="store_true", help="Don't show individual file changes in the report")
    parser.add_argument("--file-details", action="store_true", help="Get detailed information for each file (slower)")
    parser.add_argument("--file-content", action="store_true", help="Include file content in the report (JSON only)")
    parser.add_argument("--no-cumulative", action="store_true",
                        help="Don't include cumulative changes in the report")

    args = parser.parse_args()

    # Set logging level based on verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Process excluded extensions
    excluded_extensions = None
    if args.exclude:
        excluded_extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in args.exclude]
        logger.info(f"Excluding file extensions: {', '.join(excluded_extensions)}")

    try:
        # Initialize the Bitbucket client
        client = BitbucketClient(
            base_url=args.url,
            project=args.project,
            repository=args.repo,
            username=args.username,
            password=args.password
        )

        # Initialize the analyzer
        analyzer = CommitAnalyzer(client)

        # Analyze the branch
        results = analyzer.analyze_branch(args.branch, excluded_extensions)

        # Determine if cumulative changes should be shown
        show_cumulative = not args.no_cumulative

        # Generate the report
        if args.format == "json":
            report = Reporter.generate_json_report(results, show_cumulative)
        else:
            # Only show file details in text report if requested
            show_files = not args.no_files
            report = Reporter.generate_text_report(results, show_files, show_cumulative)

        # Output the report
        if args.output:
            with open(args.output, "w") as f:
                f.write(report)
            logger.info(f"Report written to {args.output}")
        else:
            print(report)

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()