// User model schema for frontend
const mongoose = require('mongoose');

const UserSchema = new mongoose.Schema({
    username: String,
    email: String,
    createdAt: Date
});

module.exports = mongoose.model('User', UserSchema);
