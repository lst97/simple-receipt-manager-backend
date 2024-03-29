const mongoose = require('mongoose');

const Schema = mongoose.Schema;

const UserSchema = new Schema({
    name: String,
    email: String,
    password: String,
    create_date: Date,
    modified_date: Date,
    role: String, // admin, user
});

const User = mongoose.model('users', UserSchema);

module.exports = User;
