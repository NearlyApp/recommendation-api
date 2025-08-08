export const environments = [
  {
    stage: "dev",
    recordName: "dev.recommendation.api.nearly",
  },
  {
    stage: "prod",
    recordName: "recommendation.api.nearly",
  },
] as const;

export const config = {
  hostedZone: "teamzbl.com",
};
