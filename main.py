import streamlit as st
from trigger import GitHubActionTrigger
from loguru import logger
from config import settings

# Initialize GitHubActionTrigger
WORKFLOW_NAME = settings.default_workflow_name

# Streamlit page title
st.title("GitHub Action Workflow Trigger")

action_trigger = GitHubActionTrigger()


# Cache the get_workflows function
@st.cache_data
def cached_get_workflows():
    logger.info("Getting workflows")
    return action_trigger.get_workflows("leowzz", "docker_image_pusher")


workflows = cached_get_workflows()
selected_workflow = next(
    (_ for _ in workflows.workflows if _.name == WORKFLOW_NAME), None
)
if not selected_workflow:
    st.error(f"Workflow `{WORKFLOW_NAME}` not found, please check the workflow name and `restart` the app")
    st.stop()
st.write(f"Selected Workflow: `{selected_workflow.name}`")

# Input fields for source and destination image
origin_image = st.text_input("源镜像", "python:3.10.14-slim-bullseye")
self_repo_image = st.text_input("私有仓库镜像", "python_self:3.10.14-slim-bullseye")

# Button to trigger the workflow
if st.button("开始复制"):

    # Get workflows from cache
    trigger_args = action_trigger.WorkflowTriggerArgs(
        origin_image=origin_image,
        self_repo_image=self_repo_image,
    )
    # Trigger the workflow
    trigger_ok = action_trigger.create_workflow_dispatch_event(
        "leowzz", "docker_image_pusher", selected_workflow, trigger_args=trigger_args
    )
    if trigger_ok:
        st.balloons()
        st.toast(f"trigger success", icon='✨')
    else:
        st.toast("trigger failed", icon='😱')
