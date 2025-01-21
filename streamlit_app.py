import streamlit as st
from dock_worker.trigger import GitHubActionManager, ImageArgs
from loguru import logger
from dock_worker.core import config

# Initialize GitHubActionTrigger
WORKFLOW_NAME = config.default_workflow_name

# Streamlit page title
st.title("GitHub Action Workflow Trigger")

action_trigger = GitHubActionManager()


# Cache the get_workflows function
@st.cache_data
def cached_get_workflows():
    logger.info("Getting workflows")
    return action_trigger.get_workflows()


workflows = cached_get_workflows()
selected_workflow = next(
    (_ for _ in workflows.workflows if _.name == WORKFLOW_NAME), None
)
if not selected_workflow:
    st.error(
        f"Workflow `{WORKFLOW_NAME}` not found, please check the workflow name and `restart` the app"
    )
    st.stop()
st.write(f"Selected Workflow: `{selected_workflow.name}`")

# Input fields for source and destination image
source = st.text_input("源镜像", "ubuntu:20.04")
target = st.text_input("私有仓库镜像", "ubuntu:20.04")

# Button to trigger the workflow
if st.button("开始复制"):

    # Get workflows from cache
    image_args = ImageArgs(
        source=source,
        target=target,
    )
    # Trigger the workflow
    trigger_ok = action_trigger.create_workflow_dispatch_event(
        selected_workflow, image_args=image_args
    )
    if trigger_ok:
        st.balloons()
        st.toast(f"trigger success", icon="✨")
    else:
        st.toast("trigger failed", icon="😱")
