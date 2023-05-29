const mongoose = require('mongoose');

const Schema = mongoose.Schema;

const RecordSchema = new Schema({
    hash: String,
    base64: String,
    receipt: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'receipts',
    },
});

const Record = mongoose.model('records', RecordSchema);

module.exports = Record;


