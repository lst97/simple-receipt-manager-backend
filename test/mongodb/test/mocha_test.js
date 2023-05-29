// Build the database using mock data
const Group = require('../app/groups');

const User = require('../app/user');
const Receipt = require('../app/receipts');
const Record = require('../app/records');

const mongoose = require('mongoose');

const mock_receipts = require('./mock_data/receipts.json');
const mock_users = require('./mock_data/users.json');
const mock_groups = require('./mock_data/groups.json');
const mock_records = require('./mock_data/records.json');


const receipt_models_array = new Array();
const record_models_array = new Array();
const user_models_array = new Array();
const group_models_array = new Array();


// drop all tables
before((done) => {
    mongoose.connection.collections.groups.drop(() => {
        done();
    });
});

before((done) => {
    mongoose.connection.collections.users.drop(() => {
        done();
    });
});

before((done) => {
    mongoose.connection.collections.receipts.drop(() => {
        done();
    });
});

before((done) => {
    mongoose.connection.collections.records.drop(() => {
        done();
    });
});

describe('Create user', () => {
    it('should create users', (done) => {
        const promises = mock_users.map((data) => {
            const user = new User(data);
            user_models_array.push(user);
            return user.save();
        });

        Promise.all(promises)
            .then(() => {
                done();
            }
            ).catch((err) => {
                console.log(err);
            });
    });
});

describe('Create receipts', () => {
    beforeEach((done) => {
        mongoose.connection.collections.receipts.drop(() => {
            done();
        });
    });

    it('should create a receipt', (done) => {
        const promises = mock_receipts.map((data, index) => {
            data.share_with.push(user_models_array[index]._id);
            data.payer = user_models_array[index]._id;
            const receipt = new Receipt(data);
            receipt_models_array.push(receipt);
            return receipt.save();
        });

        Promise.all(promises)
            .then(() => {
                done();
            })
            .catch((err) => {
                console.log(err);
            });
    });
});

describe('Create records', () => {
    it('should create records with receipt reference', (done) => {
        const promises = mock_records.map((data, index) => {
            data.receipt = receipt_models_array[index]._id;
            const record = new Record(data);
            record_models_array.push(record);
            record.save();
        });

        Promise.all(promises)
            .then(() => {
                done();
            })
            .catch((err) => {
                console.log(err);
            });
    });
});

describe('Create group', () => {
    it('should create groups', (done) => {
        const promises = mock_groups.map((data, index) => {
            data.records.push(record_models_array[index]._id);
            data.users.push(user_models_array[index]._id);
            const group = new Group(data);
            group_models_array.push(group);
            return group.save();
        });

        Promise.all(promises)
            .then(() => {
                done();
            }
            ).catch((err) => {
                console.log(err);
            });
    })
})