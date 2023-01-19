require("dotenv").config();
const express = require("express");
const calRoutes = require("./route");
const mongoose = require("mongoose");
const cors = require("cors");
const bp = require('body-parser')

const app = express();


app.use(bp.json())
app.use(bp.urlencoded({ extended: true }))
app.use(cors())
app.use("/products", calRoutes);
app.use(express.json());

mongoose.set("strictQuery", false);

mongoose
  .connect(process.env.MONGO_URI)
  .then(() => {
    app.listen(process.env.PORT, () => {
      console.log("listening on port", process.env.PORT);
    });
  })
  .catch((error) => {
    console.log(error);
  });
