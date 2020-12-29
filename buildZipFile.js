const zipFolder = require('zip-folder');
const package_ = require('./package.json');

zipFolder('src', './Blender2Babylon-' + package_.version.replace( /\.[0-9]+$/ , '' ) + 'x.zip', function(err) {
    if(err) {
        console.log('oh no!', err);
    } else {
        console.log('EXCELLENT');
    }
});