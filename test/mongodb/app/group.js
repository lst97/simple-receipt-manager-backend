const mongoose = require('mongoose');

const Schema = mongoose.Schema;

const GroupSchema = new Schema({
    name: String,
    users: Array,
    records: Array,
});

const Group = mongoose.model('groups', GroupSchema);

module.exports = Group;