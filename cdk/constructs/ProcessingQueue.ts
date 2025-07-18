import { Duration } from "aws-cdk-lib";
import { Code, Function, Runtime } from "aws-cdk-lib/aws-lambda";
import { SqsEventSource } from "aws-cdk-lib/aws-lambda-event-sources";
import { Queue } from "aws-cdk-lib/aws-sqs";
import { Construct } from "constructs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const dir = dirname(fileURLToPath(import.meta.url));

export class ProcessingQueue extends Construct {
  readonly queue: Queue;
  constructor(scope: Construct, id: string) {
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

    const handler = new Function(this, "ProcessingHandler", {
      runtime: Runtime.PYTHON_3_12,
      code: Code.fromAsset(join(dir, "../../worker"), {
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
      handler: "main.handler",
      memorySize: 512,
      timeout: Duration.minutes(5),
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
