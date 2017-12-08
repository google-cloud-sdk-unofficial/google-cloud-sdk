
var http = require('http');
var server = http.createServer(function(req, resp) {
    resp.end('Hello Woyld!');
});

server.listen(8080);
