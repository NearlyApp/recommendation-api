import { Construct } from "constructs";
import * as ddb from "aws-cdk-lib/aws-dynamodb";
import { RemovalPolicy } from "aws-cdk-lib";

export class DataTable extends Construct {
  public readonly dataTable: ddb.Table;
  constructor(scope: Construct, id: string) {
    super(scope, id);
    this.dataTable = new ddb.Table(this, "DataTable", {
      partitionKey: { name: "post_id", type: ddb.AttributeType.STRING },
      sortKey: { name: "timestamp", type: ddb.AttributeType.STRING },
      billingMode: ddb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: RemovalPolicy.DESTROY,
    });
  }
}
