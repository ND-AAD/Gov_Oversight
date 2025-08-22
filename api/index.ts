import { VercelRequest, VercelResponse } from '@vercel/node';

export default function handler(req: VercelRequest, res: VercelResponse) {
  res.status(200).json({
    message: 'LA 2028 RFP Monitor API is running!',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
    endpoints: [
      '/api/hello',
      '/api/test-connection',
      '/api/rfps',
      '/api/sites',
      '/api/stats'
    ]
  });
}