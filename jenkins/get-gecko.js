#!/usr/bin/env node

'use strict';

let service = require('@mozilla/raptor/node_modules/raptor-test/dist/es5/lib/service');

let GetGecko = function(options) {
  this.options = options;
  
  this
    .getRevision()
    .then((geckoRevision) => {
      console.log(geckoRevision);
      process.emit('complete');
    });
};

GetGecko.prototype.getRevision = function() {
  return new Promise((resolve, reject) => {
      service(this.options)
        .then(device => this.device = device)
        .then(() => {
          this.device.getGeckoRevision()
            .then((geckoRevision) => {
              resolve(geckoRevision);
            });
        })
        .catch((err) => {
          resolve(err);
        });
    });
};

let opts = {
  serial: process.argv[2]
}

return new GetGecko(opts);
