var express = require('express');
var router = express.Router();

var n = 10;

/* GET home page. */
router.get('/', function(req, res, next) {
  res.render('index', {num_row: n, num_col: n});
});

router.post('/api/image', function (req, res, next) {
  res.send(req.body);
});

module.exports = router;
