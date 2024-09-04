import argparse

from config import settings
from trigger import GitHubActionTrigger
from loguru import logger
from rich.console import Console
from rich.table import Table


def main():
    # Initialize argument parser
    parser = argparse.ArgumentParser(description="Trigger GitHub Action Workflow")
    parser.add_argument("source", type=str, nargs="?", help="Source Image URL")
    parser.add_argument(
        "target", type=str, nargs="?", help="Destination Image URL"
    )
    parser.add_argument(
        "--workflow", type=str, help="workflow name to trigger", default=None
    )
    parser.add_argument(
        "--list_workflows", "-l", action="store_true", help="List all workflows"
    )

    # Parse arguments
    args = parser.parse_args()

    # Show help if no arguments are provided
    if not any(vars(args).values()):
        parser.print_help()
        return

    # Initialize GitHubActionTrigger
    action_trigger = GitHubActionTrigger()

    # Get workflows
    workflows = action_trigger.get_workflows()
    if not workflows:
        logger.info("workflows not exist")
        return

    if args.list_workflows:
        show_workflows(workflows)
        return

    workflow_names = [_.name for _ in workflows.workflows]

    if args.workflow and args.workflow not in workflow_names:
        logger.error(f"{args.workflow} not exist in {workflow_names=}")
        return

    selected_workflow = args.workflow or next(
        (_ for _ in workflows.workflows if _.name == settings.default_workflow_name),
        None,
    )
    logger.info(f"Selected Workflow: {selected_workflow.name}")

    # Create trigger args
    trigger_args = action_trigger.WorkflowTriggerArgs(
        source=args.source,
        target=args.target,
    )
    logger.info(f"{trigger_args=}")
    action_trigger.fork_image(trigger_args=trigger_args)


def show_workflows(workflows):
    console = Console()
    table = Table(title="GitHub Workflows")
    table.add_column("ID", justify="right", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column("State", style="green")
    table.add_column("Created At", style="yellow")
    table.add_column("Updated At", style="yellow")
    for workflow in workflows.workflows:
        table.add_row(
            str(workflow.id),
            workflow.name,
            workflow.state,
            str(workflow.created_at),
            str(workflow.updated_at),
        )
    console.print(table)


if __name__ == "__main__":
    main()
