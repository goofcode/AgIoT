const express = require('express');
const cache = require('memory-cache');

const router = express.Router();

const n = 10;

const parseCellNumber = (data) => {
    // TODO: properly parse cell number from packet
    return data[0];
};

const parseImage = (data) => {
    // TODO: properly parse image data
    return data.slice(1);
};

const getImageCell = (data) => {
    return {
        number: parseCellNumber(data),
        image: parseImage(data)
    }
};

const updateCell = (res, changedCell) => {
    let cells = cache.get('cells');
    let updateQueue = cache.get('updateQueue');

    if (!cells) {
        cells = [];
    }

    cells[changedCell.number] = changedCell.image;

    cache.put('cells', cells);

    if (!updateQueue) {
        updateQueue = [];
    }

    updateQueue.push(changedCell);

    cache.put('updateQueue', updateQueue);
};

router.get('/', function (req, res) {
    const cells = cache.get('cells');

    // Draw initial image with whole cells saved in server
    res.render('index', {
        imageCells: cells ? cells : [],
        num_row: n,
        num_col: n
    });
});

router.get('/api/cells', function (req, res) {
    const cells = cache.get('cells');

    if (!cells) {
        res.send([]);
    } else {
        res.send(cells);
    }
});

router.get('/api/updatedCells', function (req, res) {
    const updateQueue = cache.get('updateQueue');

    if (!updateQueue) {
        res.send([]);
    } else {
        res.send(updateQueue);
    }
});

router.post('/api/updatedCells/pop', function (req, res) {
    const updateQueue = cache.get('updateQueue');

    updateQueue.shift();
    cache.put('updateQueue', updateQueue);

    res.send(cache.get('updateQueue'));
});

router.post('/api/image', async function (req, res) {
    let changedCell = await getImageCell(req.body['cell']);

    await updateCell(res, changedCell);

    res.send({
        changedCellNumber: changedCell.number,
        imageData: changedCell.image,
        cells: cache.get('cells'),
        updateQueue: cache.get('updateQueue')
    });
});


module.exports = router;
