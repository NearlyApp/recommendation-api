import { Stack, type StackProps } from "aws-cdk-lib";
import * as route53 from "aws-cdk-lib/aws-route53";
import * as certmgr from "aws-cdk-lib/aws-certificatemanager";
import * as route53Targets from "aws-cdk-lib/aws-route53-targets";
import {
  ApiKey,
  EndpointType,
  RestApi,
  UsagePlan,
} from "aws-cdk-lib/aws-apigateway";
import type { Construct } from "constructs";
import { Endpoints } from "../constructs/Endpoints";
import { DataTable } from "../constructs/DataTable";
import { config } from "../config";
import { ProcessingQueue } from "../constructs/ProcessingQueue";

interface APIProps extends StackProps {
  stage: string;
  recordName: string;
}
export class RecommendationAPI extends Stack {
  constructor(scope: Construct, id: string, props: APIProps) {
    super(scope, id, props);

    const domainName = `${props.recordName}.${config.hostedZone}`;
    const hostedZone = route53.HostedZone.fromLookup(this, "HostedZone", {
      domainName: config.hostedZone,
    });

    const cert = new certmgr.Certificate(this, "ApiCertificate", {
      domainName,
      validation: certmgr.CertificateValidation.fromDns(hostedZone),
    });

    const api = new RestApi(this, `RecommendationAPI-${props.stage}`, {
      defaultCorsPreflightOptions: {
        allowOrigins: ["*"],
        allowMethods: ["*"],
      },
      domainName: {
        domainName,
        certificate: cert,
      },
      endpointConfiguration: {
        types: [EndpointType.REGIONAL],
      },
    });

    new route53.ARecord(this, "AliasRecord", {
      zone: hostedZone,
      recordName: props.recordName,
      target: route53.RecordTarget.fromAlias(
        new route53Targets.ApiGateway(api)
      ),
    });

    const usagePlan = new UsagePlan(this, "UsagePlan");
    const apiKey = new ApiKey(this, "ApiKey");
    usagePlan.addApiKey(apiKey);
    usagePlan.addApiStage({
      stage: api.deploymentStage,
    });

    const { dataTable } = new DataTable(this, "DataTable");
    const { queue } = new ProcessingQueue(this, "ProcessingQueue");

    new Endpoints(this, "Endpoints", {
      api: api,
      stage: props.stage,
      processingQueue: queue,
      dataTable,
    });
  }
}
