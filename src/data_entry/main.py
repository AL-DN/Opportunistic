# Author: Alden Sahi 
# Date: 09/27/2026
# Program Name: main
# Project Description: Main entry point for the data entry module


from data_entry.summarize_commit import summarize_commit, summarize_all_commits
from data_entry.summarize_project import summarize_project

def ask_yes_no(prompt: str) -> bool:
    """Prompts until the user answers y or n."""
    while True:
        match input(f"{prompt} (y/n): ").strip().lower():
            case "y" | "yes":
                return True
            case "n" | "no":
                return False
            case _:
                print("Please enter y or n.")
                
def main() -> int:

    while True:
        print("\n Welcome to Summarization Menu :)")
        
        # ENter repo root 
        
        
        print("1. Summarize a single commit")
        print("2. Summarize all commits")
        print("3. Summarize a project")
        print("4. Exit\n")
        choice = input("Enter your choice: ")
        
        match choice:
            case "1":
                commit_sha = input("Enter the commit hash: ")
                rewrite: bool = ask_yes_no("Rewrite exisiting summary if one exisits?")
                print()
                summarize_commit(rewrite, commit_sha)
            case "2":
                rewrite: bool = ask_yes_no("Rewrite exisiting commit summaries??")
                print()
                summarize_all_commits(rewrite)
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