export default function handler(req, res) {
  res.status(200).json({
    message: 'Hello from Vercel API in pages/api!',
    timestamp: new Date().toISOString(),
    method: req.method,
    url: req.url
  });
}