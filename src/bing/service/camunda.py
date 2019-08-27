from typing import List, Tuple, Union

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
