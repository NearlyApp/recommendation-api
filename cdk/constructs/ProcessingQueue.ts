import { Duration } from "aws-cdk-lib";
import { Queue } from "aws-cdk-lib/aws-sqs";
import { Construct } from "constructs";

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

    this.queue = queue;
  }
}
