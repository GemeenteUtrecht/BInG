import uuid
from typing import Any, Dict, List, Tuple, Union

from bing.camunda.client import Camunda
from bing.camunda.client_models import Task
from bing.config.models import BInGConfig
from bing.projects.models import Project


def get_aanvraag_tasks() -> List[Tuple[Union[Project, None], Task]]:
    """
    Fetch user tasks for the BInG aanvraag.
    """
    config = BInGConfig.get_solo()
    client = Camunda()

    response = client.request(
        "task", params={"processDefinitionKey": config.aanvraag_process_key}
    )

    tasks = [Task(**task_data) for task_data in response]

    # find the projects
    projects = {
        project.camunda_process_instance_id: project
        for project in Project.objects.filter(
            camunda_process_instance_id__in=[task.process_instance_id for task in tasks]
        )
    }

    return [(projects.get(str(task.process_instance_id)), task) for task in tasks]


def get_task(task_id: uuid.UUID) -> Task:
    client = Camunda()
    task_data = client.request(f"task/{task_id}")
    variables = client.request(
        f"task/{task_id}/variables", params={"deserializeValues": "false"}
    )
    return Task(variables=variables, **task_data)


def claim_task(task_id: uuid.UUID) -> None:
    client = Camunda()
    client.request(
        f"task/{task_id}/claim",
        method="POST",
        json={
            # FIXME: should be mapped to actual camunda users
            # BING _could_ create a service account user, or a user object
            # for the actual end-user in Camunda
            "userId": "demo"
        },
    )


def complete_task(task_id: uuid.UUID, variables: Dict[str, Any]) -> None:
    client = Camunda()

    # fetch the old state of variables
    client.request(
        f"task/{task_id}/complete",
        method="POST",
        json={
            "variables": {name: {"value": value} for name, value in variables.items()}
        },
    )
