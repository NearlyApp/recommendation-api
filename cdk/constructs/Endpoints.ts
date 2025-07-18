import { Duration } from "aws-cdk-lib";
import {
  AuthorizationType,
  LambdaIntegration,
  type CognitoUserPoolsAuthorizer,
  type IResource,
  type MethodOptions,
  type RestApi,
} from "aws-cdk-lib/aws-apigateway";
import { Code, Function, LayerVersion, Runtime } from "aws-cdk-lib/aws-lambda";
import { fileURLToPath } from "node:url";
import { Construct } from "constructs";
import { dirname, join } from "path";

const dir = dirname(fileURLToPath(import.meta.url));

interface EndpointsProps {
  api: RestApi;
  stage: string;
}

export class Endpoints extends Construct {
  readonly api: RestApi;
  readonly stage: string;
  readonly pythonLayer: LayerVersion;
  constructor(scope: Construct, id: string, props: EndpointsProps) {
    super(scope, id);

    this.api = props.api;
    this.stage = props.stage;
    this.pythonLayer = this.createLambdaLayer();

    const hello = this.api.root.addResource("hello");

    const testHandler = this.createLambda({
      id: "TestHandler",
      handler: "handlers.test_lambda_handler",
    });

    this.addIntegration({
      resource: hello,
      method: "GET",
      lambda: testHandler,
    });
  }

  createLambda(options: {
    id: string;
    handler: string;
    envs?: Record<string, string>;
  }) {
    const func = new Function(this, options.id, {
      code: Code.fromAsset(join(dir, "../../api"), {
        exclude: [
          "**/__pycache__/**",
          "**/node_modules/**",
          "**/tests/**",
          "**/.git/**",
          "**/tmp/**",
          "**/venv/**",
          "**/.venv/**",
        ],
        bundling: {
          image: Runtime.PYTHON_3_12.bundlingImage,
          command: ["bash", "-c", ["cp -r . /asset-output/"].join(" && ")],
        },
      }),
      layers: [this.pythonLayer],
      environment: options.envs,
      handler: options.handler,
      runtime: Runtime.PYTHON_3_12,
      memorySize: 512,
      timeout: Duration.seconds(900),
    });

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

  createLambdaLayer() {
    return new LayerVersion(this, "PythonLayer", {
      code: Code.fromAsset(join(dir, "../../api"), {
        exclude: ["**/__pycache__/**", "**/node_modules/**"],
        bundling: {
          image: Runtime.PYTHON_3_12.bundlingImage,
          command: [
            "bash",
            "-c",
            [
              "pip install --platform manylinux2014_x86_64 --only-binary=:all: -r requirements.txt -t /asset-output/python/lib/python3.12/site-packages/",
              "cp -r . /asset-output/python/lib/python3.12/site-packages/",
            ].join(" && "),
          ],
        },
      }),
      compatibleRuntimes: [Runtime.PYTHON_3_12],
      description: "Python dependencies for Reco API Lambda functions",
    });
  }
}
