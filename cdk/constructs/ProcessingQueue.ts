import { Duration } from "aws-cdk-lib";
import {
  Code,
  DockerImageCode,
  DockerImageFunction,
  Function,
  Runtime,
} from "aws-cdk-lib/aws-lambda";
import { SqsEventSource } from "aws-cdk-lib/aws-lambda-event-sources";
import { Queue } from "aws-cdk-lib/aws-sqs";
import { Construct } from "constructs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";
import * as ssm from "aws-cdk-lib/aws-ssm";
import * as ddb from "aws-cdk-lib/aws-dynamodb";

const dir = dirname(fileURLToPath(import.meta.url));

interface ProcessingQueueProps {
  stage: string;
  dataTable: ddb.Table;
}

export class ProcessingQueue extends Construct {
  readonly queue: Queue;
  constructor(scope: Construct, id: string, props: ProcessingQueueProps) {
    super(scope, id);

    // dead letter queue for failed processing
    const dlq = new Queue(this, "ProcessingDeadLetterQueue");

    const queue = new Queue(this, "ProcessingQueue", {
      visibilityTimeout: Duration.minutes(5),
      deadLetterQueue: {
        maxReceiveCount: 5,
        queue: dlq,
      },
    });

    const handler = new DockerImageFunction(this, "ProcessingHandler", {
      code: DockerImageCode.fromImageAsset(join(dir, "../../api"), {
        exclude: ["**/__pycache__/**", "**/node_modules/**"],
        file: "Dockerfile.lambda",
      }),
      memorySize: 512,
      timeout: Duration.minutes(5),
      environment: {
        // from SSM parameter store
        OPENAI_API_KEY: ssm.StringParameter.valueFromLookup(
          this,
          `/openai/${props.stage}/API_KEY`
        ),
        OPENSEARCH_ENDPOINT: ssm.StringParameter.valueFromLookup(
          this,
          `/opensearch/ENDPOINT`
        ),
        DATA_TABLE_NAME: props.dataTable.tableName,
        LAMBDA_HANDLER: "handlers.worker_lambda_handler",
      },
    });

    handler.addEventSource(
      new SqsEventSource(queue, {
        batchSize: 10,
        reportBatchItemFailures: true,
        enabled: true,
      })
    );

    this.queue = queue;
  }
}
