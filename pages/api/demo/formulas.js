export default function handler(req, res) {
  res.status(200).json({
    formulas: [
      { id: 1, name: 'Gentle Cleanser', notes: 'Sample formula — demo only' },
      { id: 2, name: 'Hydrating Serum', notes: 'Sample formula — demo only' }
    ]
  })
}
