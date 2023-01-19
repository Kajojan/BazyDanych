const mongoose = require("mongoose");

const Schema = mongoose.Schema;
const userSchema = new Schema({
  name: {
    type: String,
    uniqe: true
  },
  price: {},
  note: {
    type: String,
  },
  amount: {},
  measure:{
    type: String,
  }
},{timestamps: true});

module.exports = mongoose.model('product', userSchema)

