"""Pull request creation feature for GitWise."""

import subprocess
from typing import List, Dict, Tuple
from gitwise.llm import generate_pr_description
from gitwise.gitutils import get_commit_history
from gitwise.features.pr_enhancements import enhance_pr_description

def pr_command(
    use_labels: bool = False,
    use_checklist: bool = False,
    skip_general_checklist: bool = False
) -> None:
    """Create a pull request with AI-generated description.
    
    Args:
        use_labels: Add labels to the PR (default: False).
        use_checklist: Add checklist to the PR description (default: False).
        skip_general_checklist: Skip general checklist items (default: False).
    """
    try:
        # Get commit history
        commits = get_commit_history()
        if not commits:
            print("No commits found between current branch and remote tracking branch.")
            print("Make sure you have committed your changes and pushed them.")
            return

        # Generate PR description
        title, description = generate_pr_description(commits)
        
        # Enhance PR description with labels and checklist if requested
        enhanced_description, labels = enhance_pr_description(
            commits, 
            description,
            use_labels=use_labels,
            use_checklist=use_checklist,
            skip_general_checklist=skip_general_checklist
        )
        
        # Show preview
        print("\n=== PR Preview ===")
        print(f"Title: {title}")
        print("\nDescription:")
        print(enhanced_description)
        if use_labels:
            print("\nLabels to be applied:", ", ".join(labels) if labels else "None")
        
        # Confirm PR creation
        if input("\nCreate pull request? (y/N) ").lower() != 'y':
            print("PR creation cancelled.")
            return

        # Create PR using GitHub CLI
        try:
            # Create PR with title and description
            result = subprocess.run(
                ["gh", "pr", "create", 
                 "--title", title,
                 "--body", enhanced_description],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                pr_url = result.stdout.strip()
                print(f"\n✅ Pull request created: {pr_url}")
                
                # Add labels if enabled and available
                if use_labels and labels:
                    subprocess.run(
                        ["gh", "pr", "edit", pr_url, "--add-label", ",".join(labels)],
                        capture_output=True
                    )
                    print(f"Added labels: {', '.join(labels)}")
            else:
                print("\n❌ Failed to create pull request.")
                print("Error:", result.stderr)
                print("\nYou can create the PR manually with:")
                print(f"gh pr create --title '{title}' --body '{enhanced_description}'")
                
        except FileNotFoundError:
            print("\n❌ GitHub CLI (gh) not found.")
            print("Please install GitHub CLI or create the PR manually with:")
            print(f"Title: {title}")
            print(f"\nDescription:\n{enhanced_description}")
            if use_labels and labels:
                print(f"\nLabels: {', '.join(labels)}")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("Please try again or create the PR manually.") 