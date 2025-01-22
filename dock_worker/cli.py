import argparse

from loguru import logger
from rich.console import Console
from rich.table import Table

cli_desc = """
Github Action Workflow Trigger.
"""


def main():
    # Initialize argument parser
    parser = argparse.ArgumentParser(description=cli_desc)
    parser.add_argument("source", type=str, nargs="?", help="Source Image URL")
    parser.add_argument(
        "target", type=str, nargs="?", help="Destination Image URL", default=None
    )
    parser.add_argument(
        "--command", "-c", "--cmd",
        type=str,
        choices=["fork", "pull"],
        help="Command to execute",
        default="fork",
    )
    parser.add_argument(
        "--workflow", type=str, help="workflow name to trigger", default=None
    )
    parser.add_argument(
        "--list_workflows", "-l", action="store_true", help="List all workflows"
    )
    parser.add_argument(
        "--test_mode", "-t", action="store_true", help="是否以测试模式运行"
    )

    # Parse arguments
    args = parser.parse_args()

    # Show help if no arguments are provided
    if not args.source:
        parser.print_help()
        return

    from dock_worker.trigger import ImageArgs, action_trigger
    # Get workflows
    workflows = action_trigger.workflows
    if not workflows:
        logger.info("workflows not exist")
        return

    if args.list_workflows:
        show_workflows(workflows)
        return

    if args.command in ["fork", "pull"]:
        # Create trigger args
        image_args = ImageArgs(
            source=args.source,
            target=args.target,
        )
        logger.info(f"{image_args=}, {args=}")
        if args.command == "fork":
            if not (job_info := action_trigger.fork_image(image_args=image_args, test_mode=args.test_mode)):
                logger.error("Fork image failed")
            action_trigger.wait_for_workflow_complete(job_info)
        elif args.command == "pull":
            if not action_trigger.fork_and_pull(image_args=image_args, test_mode=args.test_mode):
                logger.error("Fork and pull image failed")


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
