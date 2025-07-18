import { Stack, type StackProps } from "aws-cdk-lib";
import { ApiKey, RestApi, UsagePlan } from "aws-cdk-lib/aws-apigateway";
import type { Construct } from "constructs";
import { Endpoints } from "../constructs/Endpoints";
import { ProcessingQueue } from "../constructs/ProcessingQueue";

interface APIProps extends StackProps {
  stage: string;
}
export class RecommendationAPI extends Stack {
  constructor(scope: Construct, id: string, props: APIProps) {
    super(scope, id, props);

    const api = new RestApi(this, "RestApi", {
      defaultCorsPreflightOptions: {
        allowOrigins: ["*"],
        allowMethods: ["*"],
      },
    });

    const usagePlan = new UsagePlan(this, "UsagePlan");
    const apiKey = new ApiKey(this, "ApiKey");
    usagePlan.addApiKey(apiKey);
    usagePlan.addApiStage({
      stage: api.deploymentStage,
    });

    const { queue } = new ProcessingQueue(this, "ProcessingQueue");

    new Endpoints(this, "Endpoints", {
      api: api,
      stage: props.stage,
      processingQueue: queue,
    });
  }
}
