import type { NextApiRequest, NextApiResponse } from 'next';

type HealthResponse = {
  status: string;
  timestamp: string;
  uptime: number;
  environment: string;
};

export default function handler(
  req: NextApiRequest,
  res: NextApiResponse<HealthResponse>
) {
  const healthData: HealthResponse = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    environment: process.env.NODE_ENV || 'development',
  };

  res.status(200).json(healthData);
}
