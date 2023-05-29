// const Group = require('../app/group');
// const assert = require('assert');

// const User = require('../app/user');
// const Receipt = require('../app/receipt');
// const Record = require('../app/record');

// const mongoose = require('mongoose');

// beforeEach((done) => {
//     mongoose.connection.collections.groups.drop(() => {
//         done();
//     });
// });

// beforeEach((done) => {
//     mongoose.connection.collections.users.drop(() => {
//         done();
//     });
// });

// beforeEach((done) => {
//     mongoose.connection.collections.receipts.drop(() => {
//         done();
//     });
// });

// beforeEach((done) => {
//     mongoose.connection.collections.records.drop(() => {
//         done();
//     });
// });

// describe('Insert user into group', () => {
//     let user;
//     let group;

//     beforeEach((done) => {
//         mongoose.connection.collections.groups.drop(() => {
//             done();
//         });
//     });

//     beforeEach((done) => {
//         mongoose.connection.collections.users.drop(() => {
//             done();
//         });
//     });


//     beforeEach((done) => {
//         user = new User({ name: 'test', email: 'test@test.com.au', password: 'test', create_date: new Date(), modified_date: new Date() });
//         user.save().then(() => {
//             done();
//         }
//         ).catch((err) => {
//             console.log(err);
//         });
//     });

//     it('should insert a user into group', (done) => {
//         group = new Group({ name: 'test', users: [], records: [] });
//         group.users.push(user._id);
//         group.save().then(() => {
//             assert(!group.isNew);
//             assert(group.users[0].equals(user._id.toString()));
//             done();
//         }).catch((err) => {
//             console.log(err);
//         });
//     });
// });

// describe('Insert record into group', () => {
//     let record;
//     let receipt
//     let group;

//     beforeEach((done) => {
//         mongoose.connection.collections.groups.drop(() => {
//             done();
//         });
//     });

//     beforeEach((done) => {
//         mongoose.connection.collections.users.drop(() => {
//             done();
//         });
//     });

//     beforeEach((done) => {
//         mongoose.connection.collections.receipts.drop(() => {
//             done();
//         });
//     });

//     // create receipt
//     beforeEach((done) => {
//         // create receipt
//         receipt = new Receipt({
//             abn: '123456789',
//             date: new Date(),
//             file_name: 'test',
//             merchant_name: 'test',
//             merchant_phone: '123456789',
//             payer: '123456789',
//             payment_method: 'test',
//             payment_status: 'test',
//             receipt_no: '123456789',
//             share_with: [],
//             time: 'test',
//             total: 123.45,
//         });

//         receipt.save().then(() => {
//             assert(!receipt.isNew);
//             done();
//         }).catch((err) => {
//             console.log(err);
//         });
//     });

//     beforeEach((done) => {
//         // create record
//         record = new Record({
//             hash: 'ffbf1f0e1e3e0704',
//             base64: '//TEST BASE64==',
//             receipt: receipt._id,
//         });
//         record.save().then(() => {
//             assert(!record.isNew);
//             assert(record.receipt.toString() === receipt._id.toString());
//             done();
//         }).catch((err) => {
//             console.log(err);
//         });
//     });

//     it('should insert a record into group', (done) => {
//         group = new Group({ name: 'test', users: [], records: [] });
//         group.records.push(record._id);
//         group.save().then(() => {
//             assert(!group.isNew);
//             assert(group.records[0].equals(record._id.toString()));
//             done();
//         }).catch((err) => {
//             console.log(err);
//         });
//     });
// });