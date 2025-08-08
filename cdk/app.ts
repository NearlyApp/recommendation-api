import { App } from "aws-cdk-lib";
import { RecommendationAPI } from "./stacks/RecommendationAPI";
import { environments } from "./config";

const awsEnv = {
  account: process.env.CDK_DEFAULT_ACCOUNT!,
  region: process.env.CDK_DEFAULT_REGION!,
};

const app = new App();

environments.forEach((env) => {
  new RecommendationAPI(app, `RecommendationAPI-${env.stage}`, {
    stage: env.stage,
    env: awsEnv,
    recordName: env.recordName,
  });
});
