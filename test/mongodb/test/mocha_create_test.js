const Group = require('../app/group');
const assert = require('assert');

const User = require('../app/user');
const Receipt = require('../app/receipt');
const Record = require('../app/record');

const mongoose = require('mongoose');

beforeEach((done) => {
    mongoose.connection.collections.groups.drop(() => {
        done();
    });
});

beforeEach((done) => {
    mongoose.connection.collections.users.drop(() => {
        done();
    });
});

beforeEach((done) => {
    mongoose.connection.collections.receipts.drop(() => {
        done();
    });
});

beforeEach((done) => {
    mongoose.connection.collections.records.drop(() => {
        done();
    });
});

describe('Create group', () => {
    it('should create a group', (done) => {
        const group = new Group({ name: 'test', users: [], records: [] });
        group.save().then(() => {
            assert(!group.isNew);
            done();
        }).catch((err) => {
            console.log(err);
        });
    })
})

describe('Read group', () => {
    let reader;

    beforeEach((done) => {
        reader = new Group({ name: 'test', users: [], records: [] });
        reader.save().then(() => {
            done();
        }).catch((err) => {
            console.log(err);
        });
    });

    it('should read a group', (done) => {
        const group = new Group({ name: 'test', users: [], records: [] });
        group.save().then(() => {
            Group.findOne({ name: 'test' }).then((result) => {
                assert(result.name === 'test');
                assert(reader._id.toString() === result._id.toString());
                done();
            });
        }).catch((err) => {
            console.log(err);
        });
    })
});

describe('Create user', () => {
    beforeEach((done) => {
        mongoose.connection.collections.users.drop(() => {
            done();
        });
    });

    it('should create a user', (done) => {
        const user = new User({ name: 'test', email: 'test@test.com.au', password: 'test', create_date: new Date(), modified_date: new Date() });
        user.save().then(() => {
            assert(!user.isNew);
            done();
        }
        ).catch((err) => {
            console.log(err);
        });
    });
});

describe('Read user', () => {
    let reader;

    beforeEach((done) => {
        reader = new User({ name: 'test', email: 'test@test.coma.au', password: 'test', create_date: new Date(), modified_date: new Date() });
        reader.save().then(() => {
            done();
        }).catch((err) => {
            console.log(err);
        });
    });

    it('should read a user', (done) => {
        const user = new User({ name: 'test', email: 'test@test.coma.au', password: 'test', create_date: new Date(), modified_date: new Date() });
        user.save().then(() => {
            User.findOne({ name: 'test' }).then((result) => {
                assert(result.name === 'test');
                assert(reader._id.toString() === result._id.toString());
                done();
            });
        }).catch((err) => {
            console.log(err);
        });
    });
});

describe('Create receipt', () => {
    beforeEach((done) => {
        mongoose.connection.collections.receipts.drop(() => {
            done();
        });
    });

    it('should create a receipt', (done) => {
        const receipt = new Receipt({
            abn: '123456789',
            date: new Date(),
            file_name: 'test',
            merchant_name: 'test',
            merchant_phone: '123456789',
            payer: '123456789',
            payment_method: 'test',
            payment_status: 'test',
            receipt_no: '123456789',
            share_with: [],
            time: 'test',
            total: 123.45,
        });
        receipt.save().then(() => {
            assert(!receipt.isNew);
            done();
        }).catch((err) => {
            console.log(err);
        });
    });
});

describe('Read receipt', () => {
    let reader;

    beforeEach((done) => {
        reader = new Receipt({
            abn: '123456789',
            date: new Date(),
            file_name: 'test',
            merchant_name: 'test',
            merchant_phone: '123456789',
            payer: '123456789',
            payment_method: 'test',
            payment_status: 'test',
            receipt_no: '123456789',
            share_with: [],
            time: 'test',
            total: 123.45,
        });
        reader.save().then(() => {
            done();
        }).catch((err) => {
            console.log(err);
        });
    });

    it('should read a receipt', (done) => {
        const receipt = new Receipt({
            abn: '123456789',
            date: new Date(),
            file_name: 'test',
            merchant_name: 'test',
            merchant_phone: '123456789',
            payer: '123456789',
            payment_method: 'test',
            payment_status: 'test',
            receipt_no: '123456789',
            share_with: [],
            time: 'test',
            total: 123.45,
        });
        receipt.save().then(() => {
            Receipt.findOne({ abn: '123456789' }).then((result) => {
                assert(result.abn === '123456789');
                assert(reader._id.toString() === result._id.toString());
                done();
            });
        }).catch((err) => {
            console.log(err);
        });
    });
});

describe('Create record', () => {
    let receipt;
    beforeEach((done) => {
        mongoose.connection.collections.records.drop(() => {
            done();
        });
    });

    beforeEach((done) => {
        mongoose.connection.collections.receipts.drop(() => {
            done();
        });
    });

    // create receipt
    beforeEach((done) => {
        // create receipt
        receipt = new Receipt({
            abn: '123456789',
            date: new Date(),
            file_name: 'test',
            merchant_name: 'test',
            merchant_phone: '123456789',
            payer: '123456789',
            payment_method: 'test',
            payment_status: 'test',
            receipt_no: '123456789',
            share_with: [],
            time: 'test',
            total: 123.45,
        });

        receipt.save().then(() => {
            assert(!receipt.isNew);
            done();
        }).catch((err) => {
            console.log(err);
        });
    });

    it('should create a record', (done) => {
        const record = new Record({
            hash: 'ffbf1f0e1e3e0704',
            base64: '//TEST BASE64==',
            receipt: receipt._id,
        });
        record.save().then(() => {
            assert(!record.isNew);
            done();
        }).catch((err) => {
            console.log(err);
        });
    });
});