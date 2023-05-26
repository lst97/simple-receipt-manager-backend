const mongoose = require('mongoose');

const Schema = mongoose.Schema;

const ReceiptSchema = new Schema({
    abn: String,
    date: Date,
    file_name: String,
    merchant_name: String,
    merchant_phone: String,
    payer: String, // object id
    payment_method: String,
    payment_status: String,
    receipt_no: String,
    share_with: Array, // object id
    time: String,
    total: Number,
});

const Receipt = mongoose.model('receipts', ReceiptSchema);

module.exports = Receipt;
