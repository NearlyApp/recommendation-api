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
  DockerImageCode,
  DockerImageFunction,
  Function,
} from "aws-cdk-lib/aws-lambda";
import * as ddb from "aws-cdk-lib/aws-dynamodb";
import * as ssm from "aws-cdk-lib/aws-ssm";
import * as sqs from "aws-cdk-lib/aws-sqs";
import * as opensearch from "aws-cdk-lib/aws-opensearchservice";
import { fileURLToPath } from "node:url";
import { Construct } from "constructs";
import { dirname, join } from "path";
import { PolicyStatement } from "aws-cdk-lib/aws-iam";
import { Platform } from "aws-cdk-lib/aws-ecr-assets";
import { ProcessingQueue } from "./ProcessingQueue";
import { SqsEventSource } from "aws-cdk-lib/aws-lambda-event-sources";

const dir = dirname(fileURLToPath(import.meta.url));

interface EndpointsProps {
  api: RestApi;
  stage: string;
  dataTable: ddb.Table;
  processingQueue: sqs.Queue;
}

export class Endpoints extends Construct {
  readonly api: RestApi;
  readonly stage: string;
  readonly processingQueue: sqs.Queue;
  private props: EndpointsProps;
  constructor(scope: Construct, id: string, props: EndpointsProps) {
    super(scope, id);

    this.api = props.api;
    this.stage = props.stage;
    this.props = props;

    this.processingQueue = props.processingQueue;

    const processingLambda = this.createLambda({
      id: "ProcessingHandler",
      handler: "handlers.worker_lambda_handler",
      timeout: 300,
    });

    // add permissions to opensearch for this lambda
    const opensearchArn = ssm.StringParameter.valueFromLookup(
      this,
      `/opensearch/DOMAIN_ARN`
    );
    const opensearchEndpoint = ssm.StringParameter.valueFromLookup(
      this,
      `/opensearch/ENDPOINT`
    );
    const opensearchDomain = opensearch.Domain.fromDomainEndpoint(
      this,
      "OpenSearchDomain",
      opensearchEndpoint
    );
    opensearchDomain.grantReadWrite(processingLambda);

    processingLambda.addToRolePolicy(
      new PolicyStatement({
        actions: ["es:ESHttp*"],
        resources: [`${opensearchArn}/*`],
      })
    );

    processingLambda.addEventSource(
      new SqsEventSource(this.processingQueue, {
        batchSize: 10,
        reportBatchItemFailures: true,
        enabled: true,
      })
    );

    props.dataTable.grantReadWriteData(processingLambda);

    const ingest = this.api.root.addResource("ingest");

    const ingestHandler = this.createLambda({
      id: "IngestHandler",
      handler: "handlers.ingest_lambda_handler",
    });

    ingestHandler.addToRolePolicy(
      new PolicyStatement({
        actions: ["sqs:SendMessage"],
        resources: [this.processingQueue.queueArn],
      })
    );
    ingestHandler.addToRolePolicy(
      new PolicyStatement({
        actions: ["dynamodb:PutItem"],
        resources: [this.props.dataTable.tableArn],
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
    timeout?: number;
  }) {
    const func = new DockerImageFunction(this, options.id, {
      code: DockerImageCode.fromImageAsset(join(dir, "../../api"), {
        exclude: ["**/__pycache__/**", "**/node_modules/**"],
        file: "Dockerfile.lambda",
        platform: Platform.LINUX_AMD64,
      }),
      environment: {
        DATA_TABLE_NAME: this.props.dataTable.tableName,
        OPENAI_API_KEY: ssm.StringParameter.valueForStringParameter(
          this,
          `/openai/${this.props.stage}/API_KEY`
        ),
        OPENSEARCH_ENDPOINT: ssm.StringParameter.valueFromLookup(
          this,
          `/opensearch/ENDPOINT`
        ),
        QUEUE_URL: this.processingQueue.queueUrl,
        STAGE: this.stage,
        ...options.envs,
      },
      memorySize: 512,
      timeout: Duration.seconds(options.timeout ?? 900),
    });

    func.addEnvironment("LAMBDA_HANDLER", options.handler);

    return func;
  }

  addIntegration({
    resource,
    method,
    lambda,
  }: {
    resource: IResource;
    method: string;
    lambda: Function;
  }) {
    const methodOptions: MethodOptions = {
      apiKeyRequired: true,
  };


      resource.addMethod(method, new LambdaIntegration(lambda), methodOptions);
  }
}
