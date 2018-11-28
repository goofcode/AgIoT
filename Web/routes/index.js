const express = require('express');
const cache = require('memory-cache');

const PNGlib = require('node-pnglib');

const router = express.Router();

const n = 16;

const imageSize = 160;

const cellSize = imageSize / n;

// TODO: get metadata for cells

// TODO: initialize all cells

const parseHexString = (str) => {
    let result = [];

    for (let i = 0; i < 100; i++) {
        result.push(0)
    }

    let i = 0;
    while (str.length >= 2) {
        result[i] = parseInt(str.substring(0, 2), 16);

        str = str.substring(2, str.length);
        i++;
    }

    return result;
};

const parseImage = (data) => {
    const bytes = parseHexString(data);

    let png = new PNGlib(cellSize, cellSize, cellSize * cellSize);
    for (let i = 0; i < cellSize; i++) {
        for (let j = 0; j < cellSize; j++) {
            const g = bytes[i * cellSize + j];

            png.setPixel(j, i, [g, g, g]);
        }
    }

    return "data:image/png;base64," + png.getBase64();
};

const getImageCell = (data) => {
    return {
        number: data['number'],
        image: parseImage(data['image'])
    }
};

const updateCell = async (res, changedCell, sessionStore) => {
    let cells = cache.get('cells');

    if (!cells) {
        cells = [];
    }

    cells[changedCell.number] = changedCell.image;

    cache.put('cells', cells);

    await sessionStore.all(function (err, sessions) {
        for (let key of Object.keys(sessions)) {
            if (!sessions[key].updateQueue) {
                sessions[key].updateQueue = [];

            }
            sessions[key].updateQueue.push(changedCell);

            sessionStore.set(key, sessions[key], function (err) {
                if (err) {
                    throw err;
                }
            });
        }
    });
};


module.exports = (sessionStore) => {
    router.get('/', function (req, res) {
        const cells = cache.get('cells');

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
        res.send(req.session['updateQueue'] ? req.session['updateQueue'] : [])
    });

    router.post('/api/updatedCells/pop', function (req, res) {
        req.session['updateQueue'].shift();

        res.send(req.session['updateQueue']);
    });

    router.post('/api/updateCells/pop/:number', function (req, res) {
        const number = req.params.number;

        const index = req.session['updateQueue'].findIndex(function (item) {
            return item.number === number;
        });

        if (index === -1) {
            res.send(req.session['updateQueue']);
            return;
        }

        req.session['updateQueue'].splice(index, 1);

        res.send(req.session['updateQueue']);
    });

    router.post('/api/image', async function (req, res) {
        let changedCell = await getImageCell({
            number: req.body['number'],
            image: req.body['cell']
        });

        await updateCell(res, changedCell, sessionStore);

        res.send("updated cell " + changedCell.number);
    });

    return router;
};
