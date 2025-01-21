from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from trigger import GitHubActionManager, ImageArgs
from loguru import logger

app = FastAPI(title="Docker Image Pusher API")


class TriggerRequest(BaseModel):
    source: str
    target: str | None = None
    command: str = "fork"  # "fork" or "pull"
    workflow: str | None = None
    test_mode: bool = False


@app.post("/trigger")
async def trigger_workflow(request: TriggerRequest):
    action_trigger = GitHubActionManager()

    # Get workflows
    workflows = action_trigger.get_workflows()
    if not workflows:
        raise HTTPException(status_code=404, detail="No workflows found")

    workflow_names = [w.name for w in workflows.workflows]

    if request.workflow and request.workflow not in workflow_names:
        raise HTTPException(
            status_code=400,
            detail=f"Workflow {request.workflow} not found in {workflow_names}",
        )

    # Get selected workflow
    selected_workflow = request.workflow or next(
        (w for w in workflows.workflows if w.name == settings.default_workflow_name),
        None,
    )

    if not selected_workflow:
        raise HTTPException(status_code=404, detail="Default workflow not found")

    # Create image args
    image_args = ImageArgs(source=request.source, target=request.target)

    logger.info(f"Trigger request: {image_args=}, {request=}")

    if request.command == "fork":
        success = action_trigger.fork_image(
            image_args=image_args, test_mode=request.test_mode
        )
        if not success:
            raise HTTPException(status_code=500, detail="Fork image failed")
        return {"status": "success", "message": "Image fork triggered"}

    elif request.command == "pull":
        success = action_trigger.fork_and_pull(
            image_args=image_args, test_mode=request.test_mode
        )
        if not success:
            raise HTTPException(status_code=500, detail="Fork and pull image failed")
        return {"status": "success", "message": "Image fork and pull triggered"}

    raise HTTPException(status_code=400, detail="Invalid command")


@app.get("/workflows")
async def list_workflows():
    action_trigger = GitHubActionManager()
    workflows = action_trigger.get_workflows()

    if not workflows:
        raise HTTPException(status_code=404, detail="No workflows found")

    return {
        "total": workflows.total_count,
        "workflows": [
            {
                "id": w.id,
                "name": w.name,
                "state": w.state,
                "created_at": w.created_at,
                "updated_at": w.updated_at,
            }
            for w in workflows.workflows
        ],
    }


@app.get("/workflow/{workflow_id}/runs")
async def get_workflow_runs(
    workflow_id: int, status: str | None = None, per_page: int = 3, page: int = 1
):
    action_trigger = GitHubActionManager()
    runs = action_trigger.get_workflow_runs(
        workflow_id=workflow_id, status=status, per_page=per_page, page=page
    )
    return runs


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
