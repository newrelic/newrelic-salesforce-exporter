from requests import Session


from . import \
    api as mod_api, \
    pipeline


class Instance:
    def __init__(
        self,
        name: str,
        api: mod_api.Api,
        pipeline: pipeline.Pipeline,
    ):
        self.name = name
        self.api = api
        self.pipeline = pipeline

    def harvest(
        self,
        session: Session,
    ) -> None:
        self.api.authenticate(session)
        self.pipeline.execute(session)
