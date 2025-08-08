import { Duration } from "aws-cdk-lib";
import {
  AuthorizationType,
  LambdaIntegration,
  type CognitoUserPoolsAuthorizer,
  type IResource,
  type MethodOptions,
  type RestApi,
} from "aws-cdk-lib/aws-apigateway";
import {
  Code,
  DockerImageCode,
  DockerImageFunction,
  Function,
  LayerVersion,
  Runtime,
} from "aws-cdk-lib/aws-lambda";
import { fileURLToPath } from "node:url";
import { Construct } from "constructs";
import { dirname, join } from "path";
import type { Queue } from "aws-cdk-lib/aws-sqs";
import { PolicyStatement } from "aws-cdk-lib/aws-iam";
import { Platform } from "aws-cdk-lib/aws-ecr-assets";

const dir = dirname(fileURLToPath(import.meta.url));

interface EndpointsProps {
  api: RestApi;
  stage: string;
  processingQueue: Queue;
}

export class Endpoints extends Construct {
  readonly api: RestApi;
  readonly stage: string;
  // readonly pythonLayer: LayerVersion;
  readonly processingQueue: Queue;
  constructor(scope: Construct, id: string, props: EndpointsProps) {
    super(scope, id);

    this.api = props.api;
    this.stage = props.stage;
    this.processingQueue = props.processingQueue;
    // this.pythonLayer = this.createLambdaLayer();

    const ingest = this.api.root.addResource("ingest");

    const ingestHandler = this.createLambda({
      id: "IngestHandler",
      handler: "handlers.ingest_lambda_handler",
      envs: {
        STAGE: this.stage,
        QUEUE_URL: this.processingQueue.queueUrl,
      },
    });
    ingestHandler.addToRolePolicy(
      new PolicyStatement({
        actions: ["sqs:SendMessage"],
        resources: [this.processingQueue.queueArn],
      })
    );

    this.addIntegration({
      resource: ingest,
      method: "POST",
      lambda: ingestHandler,
    });
  }

  createLambda(options: {
    id: string;
    handler: string;
    envs?: Record<string, string>;
  }) {
    const func = new DockerImageFunction(this, options.id, {
      code: DockerImageCode.fromImageAsset(join(dir, "../../api"), {
        exclude: ["**/__pycache__/**", "**/node_modules/**"],
        file: "Dockerfile.lambda",
        platform: Platform.LINUX_AMD64,
      }),
      environment: options.envs,
      memorySize: 512,
      timeout: Duration.seconds(900),
    });

    func.addEnvironment("LAMBDA_HANDLER", options.handler);

    return func;
  }

  addIntegration({
    resource,
    method,
    lambda,
    authorizer,
    scopes = [],
  }: {
    resource: IResource;
    method: string;
    lambda: Function;
    authorizer?: CognitoUserPoolsAuthorizer;
    scopes?: string[];
  }) {
    const methodOptions: MethodOptions = {
      authorizationScopes: scopes,
      apiKeyRequired: true,
    };

    if (authorizer) {
      const newMethodOptions = {
        ...methodOptions,
        authorizer,
        authorizationType: AuthorizationType.COGNITO,
      };

      resource.addMethod(
        method,
        new LambdaIntegration(lambda),
        newMethodOptions
      );
    } else {
      resource.addMethod(method, new LambdaIntegration(lambda), methodOptions);
    }
  }

  // createLambdaLayer() {
  //   return new LayerVersion(this, "PythonLayer", {
  //     code: Code.fromAsset(join(dir, "../../api"), {
  //       exclude: ["**/__pycache__/**", "**/node_modules/**"],
  //       bundling: {
  //         image: Runtime.PYTHON_3_12.bundlingImage,
  //         command: [
  //           "bash",
  //           "-c",
  //           [
  //             "pip install --platform manylinux2014_x86_64 --only-binary=:all: -r requirements.txt -t /asset-output/python/lib/python3.12/site-packages/",
  //             "cp -r . /asset-output/python/lib/python3.12/site-packages/",
  //           ].join(" && "),
  //         ],
  //       },
  //     }),
  //     compatibleRuntimes: [Runtime.PYTHON_3_12],
  //     description: "Python dependencies for Reco API Lambda functions",
  //   });
  // }
}
