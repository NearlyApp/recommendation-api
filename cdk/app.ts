import { App } from "aws-cdk-lib";
import { RecommendationAPI } from "./stacks/RecommendationAPI";
import { environments } from "./config";

const app = new App();

environments.forEach((env) => {
  new RecommendationAPI(app, `RecommendationAPI-${env.stage}`, {
    stage: env.stage,
  });
});
