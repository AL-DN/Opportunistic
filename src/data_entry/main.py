# Author: Alden Sahi 
# Date: 09/27/2026
# Program Name: main
# Project Description: Main entry point for the data entry module


from summarize_commit import summarize_commit, summarize_all_commits
from summarize_project import summarize_project


def main() -> int:

    while True:
        print("\n Welcome to Summarization Menu :)")
        print("1. Summarize a single commit")
        print("2. Summarize all commits")
        print("3. Summarize a project")
        print("4. Exit\n")
        choice = input("Enter your choice: ")
        
        match choice:
            case "1":
                commit_sha = input("Enter the commit hash: ")
                print()
                summarize_commit(commit_sha)
            case "2":
                print()
                summarize_all_commits()
            case "3":
                project_id = input("Enter the project ID: ")
                print()
                summarize_project(project_id)
                
            case "4":
                print("Exiting...")
                break
            case _:
                print("Invalid choice, please try again.")
                print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())