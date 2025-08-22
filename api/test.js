export default function handler(req, res) {
  res.status(200).json({
    message: 'JavaScript API test endpoint working!',
    timestamp: new Date().toISOString(),
    method: req.method,
    path: req.url
  });
}