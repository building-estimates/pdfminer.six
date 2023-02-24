from aws_cdk import Stack, SecretValue
from constructs import Construct
from aws_cdk import aws_codepipeline as codepipeline
from aws_cdk import aws_codepipeline_actions as codepipeline_actions
from aws_cdk import aws_codebuild as codebuild
import aws_cdk.aws_s3 as s3


class CondaBuildCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, resource_names: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        source_artifact = codepipeline.Artifact()
        source_action = codepipeline_actions.GitHubSourceAction(
            action_name="GitHub",
            output=source_artifact,
            oauth_token=SecretValue.secrets_manager("codepipelines-inference-repos-pat"),
            owner=resource_names["repo_owner"],
            repo=resource_names["repo_name"],
            branch=resource_names["repo_branch"]
        )
        project = codebuild.PipelineProject(
            self,
            resource_names["project_name"],
            environment={
                "build_image": codebuild.LinuxBuildImage.from_asset(
                    self,
                    resource_names["project_name"] + "DockerImage",
                    directory="../",
                    file=resource_names["dockerfile_name"]
                ),
                "privileged": True,
                "compute_type": codebuild.ComputeType.LARGE
            },
            environment_variables={
                'ssh_key': codebuild.BuildEnvironmentVariable(
                    value="github_id_rsa",
                    type=codebuild.BuildEnvironmentVariableType.PARAMETER_STORE
                ),
                'ssh_pub': codebuild.BuildEnvironmentVariable(
                    value="github_id_rsa.pub",
                    type=codebuild.BuildEnvironmentVariableType.PARAMETER_STORE
                ),
                'conda_channel_bucket': codebuild.BuildEnvironmentVariable(
                    value=resource_names['conda_channel_bucket'],
                    type=codebuild.BuildEnvironmentVariableType.PLAINTEXT
                ),
                'conda_channel_name': codebuild.BuildEnvironmentVariable(
                    value=resource_names['conda_channel_name'],
                    type=codebuild.BuildEnvironmentVariableType.PLAINTEXT
                )
            }
        )
        codepipeline.Pipeline(
            self,
            resource_names["project_name"] + "Pipeline",
            pipeline_name=resource_names["project_name"] + "Pipeline",
            stages=[
                codepipeline.StageProps(
                    stage_name="Source",
                    actions=[source_action]
                ),
                codepipeline.StageProps(
                    stage_name="Build",
                    actions=[
                        codepipeline_actions.CodeBuildAction(
                            action_name="Build",
                            project=project,
                            input=source_artifact,
                        )
                    ]
                ),
            ],
        )

        bucket = s3.Bucket.from_bucket_arn(
            self,
            "CondaChannelBucket",
            "arn:aws:s3:::"+resource_names['conda_channel_bucket']
        )

        bucket.grant_read_write(project.role)
