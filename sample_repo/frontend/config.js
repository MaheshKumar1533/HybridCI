// Frontend config loader
const fs = require('fs');
const yaml = require('js-yaml');

const config = yaml.load(fs.readFileSync('config.yaml', 'utf8'));

module.exports = {
    apiUrl: process.env.API_URL || `http://${config.api.host}:${config.api.port}`,
    dbHost: process.env.DB_HOST || config.database.host
};
